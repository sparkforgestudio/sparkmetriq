Parfait. Voici **DOC-SC-013 — Scheduler & Dispatcher Deep Spec (State Machine, Ordering, Concurrency, Fault Recovery)**, version longue, complète, ultra-formelle, alignée avec S2, SaasentialCore et tous les précédents SC (001–012).

Ce document décrit **la mécanique interne exacte** du Scheduler et du Dispatcher, cœur de Sparkmetriq S2, incluant :

* state machine complète
* ordering des tâches
* règles de k-séquençage
* gestion des échecs
* retries
* isolation multi-tenant
* interaction avec l’Event Bus
* invariants SRE++

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-013_scheduler_dispatcher_deep_spec.md
```

---

# 📘 `DOC-SC-013_scheduler_dispatcher_deep_spec.md`

````markdown
---
title: DOC-SC-013 — Scheduler & Dispatcher Deep Spec
version: 1.0
status: Stable
category: SaasentialCore / Sparkmetriq S2 / Scheduling / Dispatching
last_updated: 2025-02-17
---

# 1. Objectif du document

DOC-SC-013 formalise le fonctionnement interne du **Scheduler** et du **Dispatcher** dans SaasentialCore / Sparkmetriq S2 :

- state machine complète des jobs,
- règles d’ordonnancement (ordering),
- gestion de la concurrence,
- résilience en cas de pannes,
- relation avec quotas (DOC-004),
- interaction avec retry/idempotence (DOC-005),
- émission et consommation d’événements (DOC-SC-006),
- conformité DI (DOC-SC-003),
- isolation multi-tenant (DOC-SC-004),
- contraintes SRE++ (DOC-SC-009).

Le but : une exécution **prédictible, stable, scalable et observable** le long de la chaîne S2.

---

# 2. Vue d’ensemble du pipeline S2

```mermaid
flowchart LR
    A[API - schedule request] --> B[Scheduler]
    B --> C[Dispatcher]
    C --> D[Worker Pool]
    D --> E[Connector Layer]
    E --> F[Platform Publish]
    F --> G[Events + Analytics]
````

---

# 3. Modèle des Jobs

Un **Job** S2 représente une exécution unitaire d’un contenu vers une plateforme.

## 3.1. Identifiants

* `job_id` : ULID / UUID
* `tenant` : startup_id, org_id, product_id
* `post_id` : ID du contenu
* `target_platform` : ex. "instagram", "tiktok", "threads"
* `scheduled_at`
* `created_at`
* `updated_at`

## 3.2. Métadonnées runtime

* `retry_count`
* `max_retries`
* `last_error`
* `connector_response`
* `trace_id`

---

# 4. State Machine officielle des Jobs

```mermaid
stateDiagram-v2
    [*] --> SCHEDULED
    SCHEDULED --> RESERVED : quota.reserve()
    RESERVED --> QUEUED : scheduler.enqueue()
    QUEUED --> DISPATCHED : dispatcher.push_to_worker()
    DISPATCHED --> EXECUTING : worker.start()
    EXECUTING --> SUCCESS : connector.publish OK
    EXECUTING --> FAILED : connector.publish ERROR
    FAILED --> RETRYING : retry_policy()
    RETRYING --> QUEUED : enqueue again
    FAILED --> DEAD : exceeding retries
    SUCCESS --> [*]
```

### États

| État       | Description                      |
| ---------- | -------------------------------- |
| SCHEDULED  | Job créé mais quota non réservé  |
| RESERVED   | Quota consommé (DOC-004)         |
| QUEUED     | Job en attente de dispatch       |
| DISPATCHED | Assigné à un worker              |
| EXECUTING  | Worker en train d’exécuter       |
| SUCCESS    | Publication validée              |
| FAILED     | Erreur transitoire ou permanente |
| RETRYING   | Application du retry policy      |
| DEAD       | Erreur irréparable après retries |

---

# 5. Règles d’ordonnancement (Ordering)

## 5.1. Ordering par tenant (STRICT)

Un tenant doit voir ses jobs exécutés dans l’ordre prévu (FIFO tenant-level).

Pourquoi ?

* éviter les collisions de scheduling multi-plateformes,
* cohérence fonctionnelle,
* respect des SLO tenant.

## 5.2. Ordering global (LOOSE)

Globalement, les jobs sont distribués dans le worker pool selon :

* priorité tenant,
* délai restant avant exécution,
* round-robin multi-produit.

## 5.3. Priorités internes

| Priorité | Type                                    |
| -------- | --------------------------------------- |
| 0        | Jobs immédiats (publish_now)            |
| 1        | Jobs retardés par retry                 |
| 2        | Jobs planifiés à l’heure exacte         |
| 3        | Jobs low-priority à exécution lointaine |

---

# 6. Concurrency Model

## 6.1. Par tenant

Chaque tenant possède une limite configurable :

```
tenant.concurrent_jobs_max = N  (ex: 5)
```

Cela évite :

* surcharge plateforme,
* ban API,
* explosion de latence.

## 6.2. Par worker pool

Le pool exécute en parallèle :

```
workers = W (configurable)
```

Exemple :

* worker-A: Instagram
* worker-B: TikTok
* worker-C: Threads

## 6.3. Par plateforme

Certaines plateformes imposent leur propre rate limit → intégrée dans connectors (DOC-SC-012).

---

# 7. Scheduler Deep Behavior

## 7.1. Fonction principale

Le scheduler :

* lit les jobs en `SCHEDULED`,
* réserve les quotas,
* passe l’état → `RESERVED`,
* programme dans une priority queue,
* envoie `QUEUED` lorsque le timestamp est atteint.

## 7.2. Time-wheel algorithm (optionnel)

Pour performance extrême, utilisation d’un time-wheel :

```
slot[t] → jobs planifiés
```

## 7.3. Gestion des retards

Si le scheduler détecte :

* worker en panne,
* backlog élevé,
* retries massifs,

il ajuste:

* backpressure,
* fréquence d’enqueue,
* dispatch spacing.

---

# 8. Dispatcher Deep Behavior

## 8.1. Rôle

Le dispatcher est responsable de :

* prendre les jobs `QUEUED`,
* route vers un worker disponible,
* gérer le backoff cluster-wide,
* émettre `DISPATCHED`.

## 8.2. Worker Selection Algorithm

### Entry points :

```
Round-robin
Load-aware selection
Platform affinity
Tenant fairness
```

### Fairness garantie :

```
no-tenant-starvation
no-product-starvation
no-platform-starvation
```

## 8.3. Dead-worker detection

Worker considéré mort si :

```
last_heartbeat > X seconds
```

Les jobs en cours → renvoyés en retry.

---

# 9. Fault Recovery

## 9.1. Failures connector

Échec lors de l’appel API plateforme.

→ état `FAILED`
→ retry policy (DOC-005)

## 9.2. Worker crash

Worker meurt pendant exécution

→ dispatcher marque job = FAILED
→ retry

## 9.3. Scheduler crash

Scheduler redémarre → reconstruit sa priority queue depuis DB.

## 9.4. Dispatcher crash

Dispatcher redémarre → détecte jobs "in-flight" → requeue.

---

# 10. Retry Model (DOC-005)

## 10.1. Backoff + Jitter

répartition :

```
retry_delay = base * (2 ** retry_count) + random(0, jitter)
```

## 10.2. Retry boundaries

* erreur transitoire (HTTP 429, 503, timeout) → retry
* erreur permanente (auth invalid, rate limit définitif, bad media) → DEAD

## 10.3. Max retries

Typiquement :

```
max_retries = 4
```

---

# 11. Idempotence (DOC-005)

### Actions idempotentes :

* dispatcher.push(job)
* worker.execute(job)
* connector.call(job)

Chaque action possède une `idempotency_key` :

```
idempotency_key = hash(job_id + attempt)
```

---

# 12. Event Bus integration (DOC-SC-006)

Chaque étape produit un événement :

| Événement            | Condition              |
| -------------------- | ---------------------- |
| `s2.post.scheduled`  | API → Scheduler        |
| `s2.post.queued`     | Scheduler → Dispatcher |
| `s2.post.dispatched` | Dispatcher → Worker    |
| `s2.post.executed`   | Worker → Connector     |
| `s2.post.published`  | Connector success      |
| `s2.post.failed`     | Connector error        |
| `s2.post.dead`       | Max retries exceeded   |

Ces événements sont :

* immuables,
* multi-tenant tagged,
* préviennent l’Analytics S2 (DOC-016).

---

# 13. Observabilité (SRE++)

### Logs obligatoires

Chaque transition d’état doit logguer :

```json
{
  "event": "job.transition",
  "job_id": "123",
  "from": "QUEUED",
  "to": "DISPATCHED",
  "product_id": "sparkmetriq",
  "startup_id": "...",
  "org_id": "...",
  "trace_id": "abc"
}
```

### Metrics obligatoires

* `s2_jobs_total`
* `s2_jobs_failed_total`
* `s2_jobs_success_total`
* `s2_dispatch_latency_seconds`
* `s2_scheduler_delay_seconds`
* `s2_worker_execution_seconds`
* `s2_retry_total`

### Traces

Propagation du trace_id → obligatoire.

---

# 14. Multi-tenant isolation

Scheduler & Dispatcher doivent :

* isoler les files d’attente par tenant,
* isoler la priorité par tenant,
* éviter qu’un tenant monopolise le worker pool,
* interdire publication d’un secret/emplacement d’un autre tenant,
* tagguer logs & metrics & events.

Aligné DOC-SC-004.

---

# 15. CI/CD Compliance Rules

### 🚫 Bloquant :

* transition non validée par state machine,
* job sans tenant context,
* absence d’idempotency key,
* absence d’événements obligatoires,
* modification state machine sans version bump,
* accès direct aux secrets hors DI,
* code non résilient à crash scheduler/worker.

### ⚠ Warning :

* absence de fairness testing,
* absence de tests d’ordre tenant,
* absence d’observabilité complète,
* absence de tests retry.

---

# 16. Invariants non négociables

1. La state machine ne peut être cassée ou modifiée sans MAJOR change (DOC-SC-007).
2. Le scheduler doit toujours être idempotent.
3. Le dispatcher doit toujours garantir fairness inter-tenant.
4. Aucun job ne peut être exécuté sans quota (DOC-004).
5. Tous les événements doivent être produits.
6. Toute PR violant DOC-SC-013 est bloquée.

---

# 17. Conclusion

DOC-SC-013 constitue la **spécification interne complète** du Scheduler & Dispatcher S2 :

* state machine précise et immuable,
* ordonnancement fiable,
* concurrence maîtrisée,
* reprise après échec,
* isolation tenant stricte,
* intégration totale DI/Events/Observability.

C’est un pilier central du fonctionnement de Sparkmetriq S2.

```
### 👉 **DOC-SC-014 — UnifiedPostPayload & Cross-Platform Schema Contract**,
