Voici **DOC-SC-015 — Worker Lifecycle & Execution Model (RTOS-Inspired Contract)**,
version **longue**, formelle et normative, alignée avec Sparkmetriq S2, SaasentialCore, et l’ensemble des contrats SC-001 → SC-014.

Ce document définit **le modèle d’exécution des workers** comme un **micro-RTOS applicatif distribué**, garantissant :

* déterminisme,
* isolation,
* robustesse face aux pannes,
* contrôle strict des ressources,
* observabilité complète,
* compatibilité retry / idempotence / scheduler.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-015_worker_lifecycle_execution_model.md
```

---

# 📘 `DOC-SC-015_worker_lifecycle_execution_model.md`

````markdown
---
title: DOC-SC-015 — Worker Lifecycle & Execution Model (RTOS-Inspired)
version: 1.0
status: Stable
category: SaasentialCore / Sparkmetriq S2 / Workers / Execution Model
last_updated: 2025-02-18
---

# 1. Objectif du document

DOC-SC-015 définit le **contrat d’exécution des Workers** dans SaasentialCore et Sparkmetriq S2.

Il formalise :

- le cycle de vie complet d’un worker,
- son modèle d’exécution inspiré des systèmes temps réel (RTOS),
- la gestion des ressources (CPU, mémoire, I/O),
- la relation avec Scheduler & Dispatcher (DOC-SC-013),
- les règles d’isolation multi-tenant (DOC-SC-004),
- l’intégration retry & idempotence (DOC-005),
- l’observabilité (DOC-SC-009),
- la résilience et la reprise après panne.

Le worker n’est **pas un simple consumer Celery** :  
il est un **agent d’exécution contrôlé**, déterministe et auditable.

---

# 2. Philosophie RTOS appliquée aux Workers

Les workers S2 suivent les principes fondamentaux d’un RTOS :

| Principe RTOS | Application S2 |
|---------------|----------------|
| Task isolation | 1 job = 1 contexte isolé |
| Determinism | transitions d’état strictes |
| Preemption control | pas d’exécution incontrôlée |
| Resource bounding | limites CPU/mémoire |
| Fault containment | une tâche ne casse pas le worker |
| Predictable recovery | reprise explicite |

---

# 3. Rôle du Worker dans l’architecture S2

Le worker est responsable de :

- exécuter **un job plateforme** à la fois,
- appliquer les règles du connecteur,
- interagir avec des APIs externes,
- respecter quotas, rate limits, retries,
- produire événements, logs, métriques,
- ne jamais prendre de décision métier globale.

Le worker **n’est pas** responsable de :
- l’ordonnancement,
- la gestion des quotas,
- la planification temporelle,
- la logique multi-plateformes globale.

---

# 4. Cycle de vie global d’un Worker

```mermaid
stateDiagram-v2
    [*] --> INIT
    INIT --> BOOTSTRAP
    BOOTSTRAP --> IDLE
    IDLE --> CLAIM_JOB
    CLAIM_JOB --> EXECUTING
    EXECUTING --> SUCCESS
    EXECUTING --> FAILURE
    FAILURE --> CLEANUP
    SUCCESS --> CLEANUP
    CLEANUP --> IDLE
    IDLE --> SHUTDOWN
    SHUTDOWN --> [*]
````

---

# 5. États détaillés du Worker

## 5.1. INIT

* Process démarre
* Aucun accès réseau
* Aucune dépendance chargée

## 5.2. BOOTSTRAP

* Chargement Settings (DOC-SC-010)
* Initialisation DI Container (DOC-SC-003)
* Enregistrement des produits (DOC-SC-002)
* Connexion Broker (RabbitMQ)
* Enregistrement heartbeat

**Interdiction** : traiter un job à ce stade.

---

## 5.3. IDLE

* Worker disponible
* Attente passive d’un job
* Heartbeat actif
* Monitoring actif

---

## 5.4. CLAIM_JOB

* Réception d’un job du Dispatcher
* Validation :

  * job_id
  * tenant context
  * product_id
  * payload_version
* Vérification idempotence

Échec → job rejeté + event `job.claim.rejected`

---

## 5.5. EXECUTING

Phase critique, subdivisée :

### a) PRE_EXEC

* chargement secrets tenant (DOC-SC-010)
* validation connecteur
* allocation ressources

### b) EXEC

* appel API plateforme
* gestion timeouts
* gestion rate limit
* retry local si autorisé

### c) POST_EXEC

* parsing réponse
* validation succès/échec
* enrichissement metadata

---

## 5.6. SUCCESS

* job marqué SUCCESS
* événement `s2.post.published`
* métriques succès
* libération ressources

---

## 5.7. FAILURE

* classification erreur :

  * transitoire
  * permanente
* décision retry vs dead (DOC-005)
* événement `s2.post.failed`

---

## 5.8. CLEANUP

* suppression données temporaires
* purge mémoire
* reset contexte
* reset secrets
* confirmation heartbeat sain

**Obligatoire avant retour IDLE**

---

## 5.9. SHUTDOWN

* drain des jobs
* arrêt heartbeat
* fermeture connexions
* flush logs/metrics

---

# 6. Modèle d’exécution interne

## 6.1. Un job = un contexte isolé

Chaque job s’exécute dans un **Execution Context** :

```python
class WorkerExecutionContext:
    job_id
    tenant_context
    trace_id
    start_time
    timeout
    resources_limits
```

Interdiction absolue de partager ce contexte entre jobs.

---

## 6.2. Resource Bounding (obligatoire)

Chaque worker doit appliquer :

* limite mémoire par job
* limite CPU par job
* timeout hard (ex: 120s)

Si dépassement → abort + FAILURE.

---

# 7. Concurrency Model

## 7.1. Single-Job per Worker (par défaut)

Un worker ne traite **qu’un seul job à la fois**.

Avantages :

* isolation maximale
* déboggage simple
* prédictibilité

## 7.2. Multi-slot Worker (option avancée)

Autorisé uniquement si :

* slots strictement isolés
* monitoring par slot
* limites CPU/mémoire par slot

---

# 8. Interaction avec Retry & Idempotence (DOC-005)

* Worker **ne décide jamais seul** du retry global
* Il remonte :

  * code erreur
  * type erreur
  * retryable = true/false
* Scheduler/Dispatcher décide du retry

Idempotency key obligatoire :

```
hash(job_id + attempt)
```

---

# 9. Isolation Multi-Tenant (DOC-SC-004)

Le worker doit garantir :

* un job = un tenant unique
* aucun secret cross-tenant
* aucun cache partagé cross-tenant
* aucun état persistant local

Violation = CRITICAL ERROR.

---

# 10. Event & Messaging Integration (DOC-SC-006)

Événements produits par le worker :

* `worker.job.claimed`
* `worker.job.started`
* `worker.job.succeeded`
* `worker.job.failed`
* `worker.job.dead`
* `worker.job.timeout`

Tous doivent inclure :

* job_id
* tenant metadata
* trace_id
* product_id

---

# 11. Observabilité (DOC-SC-009)

## Logs obligatoires

```json
{
  "event": "worker.execute",
  "job_id": "...",
  "state": "EXECUTING",
  "product_id": "sparkmetriq",
  "startup_id": "...",
  "org_id": "...",
  "trace_id": "..."
}
```

## Metrics obligatoires

* `worker_jobs_started_total`
* `worker_jobs_success_total`
* `worker_jobs_failed_total`
* `worker_execution_seconds`
* `worker_timeouts_total`
* `worker_memory_peak_mb`

---

# 12. Failure Modes & Recovery

| Failure         | Comportement        |
| --------------- | ------------------- |
| API timeout     | FAILURE → retry     |
| Worker crash    | job requeued        |
| OOM             | job DEAD + alert    |
| Invalid payload | job DEAD            |
| Secret missing  | FAILURE             |
| Rate limit      | FAILURE (retryable) |

Worker doit **toujours fail fast**, jamais rester bloqué.

---

# 13. Tests obligatoires (DOC-SC-008)

Chaque worker doit être couvert par :

* tests unitaires d’exécution
* tests timeout
* tests retry
* tests isolation tenant
* tests crash recovery
* tests idempotence

---

# 14. CI/CD Compliance Rules

### 🚫 Bloquant

* worker traitant plusieurs tenants simultanément
* absence de cleanup
* job exécuté sans tenant context
* secret loggué
* absence de timeout hard
* absence d’événements obligatoires
* partage mémoire cross-job

### ⚠ Warning

* absence de resource metrics
* absence de stress tests
* absence de dashboards worker

---

# 15. Invariants non négociables

1. Un worker ne traite qu’un job par contexte.
2. Aucun job sans tenant context.
3. Toute exécution est bornée (temps, mémoire).
4. Le worker ne décide jamais seul du retry global.
5. Chaque transition est observable.
6. Toute PR violant DOC-SC-015 est bloquée.

---

# 16. Conclusion

DOC-SC-015 transforme les workers Sparkmetriq S2 en **agents d’exécution industriels** :

* déterministes,
* isolés,
* résilients,
* observables,
* sécurisés,
* compatibles hyperscale.

C’est le fondement de la fiabilité du pipeline S2 en production.

```
👉 **DOC-SC-017 — S2 Failure Modes & Reliability Playbook**
