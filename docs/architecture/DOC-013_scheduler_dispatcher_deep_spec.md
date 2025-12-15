Voici **DOC-013 — Scheduler & Dispatcher Deep Spec (Version longue, 12–20 pages)**, le document de référence le plus critique du module Sparkmetriq S2.
Il définit la **state machine interne**, la **gestion de la concurrence**, l’**ordonnancement**, la **récupération après panne**, la **garantie de livraison**, la **cohérence avec DOC-004 / DOC-005**, la **séparation scheduler/dispatcher**, les **invariants**, et les **exigences SRE++**.

Prêt à être intégré dans :

```
docs/architecture/DOC-013_scheduler_dispatcher_deep_spec.md
```

---

# 📘 **DOC-013 — Scheduler & Dispatcher Deep Spec (Version longue)**

*Document Technique Final — Sparkmetriq S2 / Scheduling Engine / Distributed Coordination / SRE++*

```markdown
---
title: DOC-013 — Scheduler & Dispatcher Deep Spec
version: 1.0
status: Stable
category: Architecture / Distributed Systems / Scheduler / Messaging
last_updated: 2025-02-06
---
```

---

# # **1. Objectif du document**

Sparkmetriq S2 repose sur un moteur complexe composé de :

* **Scheduler** : planification
* **Dispatcher** : envoi des tâches dans RabbitMQ
* **Workers S2** : exécution des jobs (connecteurs)

Ce document définit la **spécification profonde et normative** du système :

* state machine interne du scheduler
* ordering & priorité
* gestion de la concurrence
* backpressure & rate limiting interne
* tolérance aux pannes (fault recovery)
* garanties de livraison ("exactly-once effect")
* invariants structurels
* intégration idempotence & quotas
* synchronisation API ↔ Scheduler ↔ Workers

**Ceci est la pierre angulaire du fonctionnement Sparkmetriq.**

Toute violation → **PR bloquée**.

---

# # **2. Périmètre**

S’applique à :

* SchedulerService
* DispatcherService
* Queue Manager RabbitMQ
* Celery S2 Workers
* State transitions (internal)
* Quotas (DOC-004)
* Idempotence (DOC-005)
* Retry (DOC-005)
* Observability (DOC-006)

---

# # **3. Architecture générale**

```mermaid
flowchart TD
A[API → schedule()] --> B[Scheduler]
B --> C[Scheduler State Machine]
C --> D[Dispatcher]
D --> E[RabbitMQ Queue]
E --> F[Celery Worker]
F --> G[Connector]
G -->|success/failure| H[Idempotence Registry]
```

---

# # **4. State Machine interne (Scheduler + Dispatcher)**

La state machine interne (à ne pas confondre avec la **quota state machine DOC-004**) décrit les transitions du job à travers Sparkmetriq.

### États internes :

| État           | Description                              |
| -------------- | ---------------------------------------- |
| **NEW**        | Job créé, pas encore validé              |
| **VALIDATED**  | Payload validé, tenant vérifié           |
| **SCHEDULED**  | Réservé dans les quotas, inscrit dans DB |
| **READY**      | Prêt à être dispatché                    |
| **ENQUEUED**   | Envoyé à RabbitMQ                        |
| **DISPATCHED** | Acquitté par RabbitMQ                    |
| **PROCESSING** | Worker en cours d'exécution              |
| **EXECUTED**   | Connecteur exécuté, résultat reçu        |
| **COMPLETED**  | État final (SUCCESS / FAILURE)           |

---

# # **5. Transitions internes**

## ✔ 5.1. NEW → VALIDATED

Validation complète :

* schéma (DOC-003)
* org_id enforced (DOC-009)
* connector tokens disponibles
* media disponibles

## ✔ 5.2. VALIDATED → SCHEDULED

Transition critique :

* réservation quota (DOC-004)
* écriture DB document job
* génération idempotency_key

## ✔ 5.3. SCHEDULED → READY

Condition :

* scheduled_at ≤ now + schedule_window
* retry possible

## ✔ 5.4. READY → ENQUEUED

Le Dispatcher pousse le job dans RabbitMQ.

Invariant :

```
Chaque job ne peut être ENQUEUED qu’une seule fois.
```

## ✔ 5.5. ENQUEUED → DISPATCHED

RabbitMQ confirme l’ack.
Un job non acké → réessayé (mais jamais dupliqué).

## ✔ 5.6. DISPATCHED → PROCESSING

Worker Celery prend en charge la tâche.

## ✔ 5.7. PROCESSING → EXECUTED

Worker reçoit un résultat du connecteur :

* SUCCESS
* FAILURE
* RETRYABLE_ERROR

## ✔ 5.8. EXECUTED → COMPLETED

Finalisation :

* idempotence registry → `SUCCESS` or `FAILED`
* quotas → `CONSUMED` or `RELEASED`
* logs structurés (DOC-006)

---

# # **6. Ordering Guarantees (Ordonnancement)**

Sparkmetriq garantit **FIFO par compte social**, mais pas globalement.

### 6.1. Par plateforme + compte :

```
(Instagram, account_11)
job1 → job2 → job3
```

### 6.2. Jamais de FIFO global cross-tenants

Isolation tenant (DOC-009).

### 6.3. Priorités

| Niveau | Raison                          |
| ------ | ------------------------------- |
| HIGH   | publication immédiate           |
| MEDIUM | publication programmée proche   |
| LOW    | publication programmée > 30 min |

Le scheduler doit recalculer dynamiquement les priorités.

---

# # **7. Gestion de la concurrence (Concurrency Model)**

Sparkmetriq doit supporter :

* plusieurs workers
* plusieurs dispatcher threads
* plusieurs tenants simultanés
* plusieurs connecteurs

### 7.1. Un job ne peut être traité par plusieurs workers

→ Protégé par RabbitMQ + idempotence.

### 7.2. Aucun traitement parallèle sur même média

→ ACL Media (DOC-010) interdit modification concurrente.

### 7.3. Mutex logique par "account_id"

```text
Only 1 running job per social-account per tenant
```

---

# # **8. Backpressure & queue management**

Le scheduler doit surveiller :

* backlog RabbitMQ
* saturation workers
* quota consommé
* erreurs connecteurs

Si backlog > threshold :

* réduction taux d’envoi
* extension des créneaux
* backoff progressif du dispatcher

---

# # **9. Fault Recovery (Tolérance aux pannes)**

### Cas A — Crash Scheduler

Au redémarrage :

* re-validation des jobs `READY`
* reprise du plan

Aucun job ne doit être perdu.

---

### Cas B — Crash Dispatcher

Au redémarrage :

* RabbitMQ renvoie les messages non ackés
* dispatcher re-pousse (idempotent)

---

### Cas C — Crash Worker

Worker crash → message remis dans la queue.

**Grâce à DOC-005 Idempotence → aucun double effet.**

---

### Cas D — Crash Connecteur

Selon error :

* retry policy (DOC-005)
* si 4xx → failure immédiate
* si 5xx → backoff + retry

---

### Cas E — MongoDB indisponible

Scheduler :

* retry + backoff
  Worker :

* ne modifie pas quotas

* ne finalise pas job → requeue

---

# # **10. Hard Invariants (non négociables)**

Ces invariants garantissent la sécurité du système.

### ⭐ Invariant 1 — Aucun job ne peut être exécuté sans être SCHEDULED

Respect strict DOC-004.

### ⭐ Invariant 2 — Aucun job ne peut être exécuté deux fois

Grâce à :

* RabbitMQ ack model
* idempotence registry
* state machine interne

### ⭐ Invariant 3 — Aucun job ne peut revenir en arrière

Pas de transitions :

```
EXECUTED → PROCESSING
ENQUEUED → READY
DISPATCHED → READY
```

### ⭐ Invariant 4 — Les quotas ne mentent jamais

No double consumption.

### ⭐ Invariant 5 — org_id est strict (DOC-009)

Pas de cross-tenant.

---

# # **11. Scheduling Algorithms (Détails)**

Sparkmetriq utilise un **hybrid bucket scheduler** :

## 11.1. Buckets

Groupés par :

* org_id
* platform
* account
* scheduled_at window

## 11.2. Heap de priorité

Critères :

1. scheduled_at
2. priority_level
3. retry_count
4. tenant fairness (équité cross-tenants)

## 11.3. Sliding window

Fenêtre d’envoi dynamique :

```
T = now
jobs with scheduled_at in [T, T+5min]
```

---

# # **12. Retry integration**

Le scheduler **ne retry jamais** un job exécuté.
Le worker retry selon DOC-005.

---

# # **13. API Contract (DOC-003 alignment)**

Endpoints critiques :

* `/s2/jobs/schedule`
* `/s2/jobs/calendar`
* `/s2/jobs/{id}/status`
* `/s2/jobs/retry_failed`
* `/s2/jobs/next_batch` (internal)

Réponses doivent :

* être typées
* ne jamais exposer état interne non documenté
* jamais exposer idempotency_key

---

# # **14. Observability Contract (DOC-006)**

Chaque transition doit émettre un log structuré :

```
event: "scheduler_transition"
old_state: "READY"
new_state: "ENQUEUED"
org_id: ...
job_id: ...
priority: ...
```

Métriques Prometheus obligatoires :

* scheduler_queue_length
* scheduler_latency_seconds
* dispatcher_throughput
* worker_retry_count
* connector_failure_rate

---

# # **15. Tests obligatoires**

## 15.1. Unit tests

* state machine transitions
* concurrency model
* retry logic
* ordering

## 15.2. Integration tests

* simulated crash scenarios
* Mongo down
* RabbitMQ down
* worker crash

## 15.3. E2E tests

* 500 jobs scheduled → 500 executed
* aucun double publish
* aucun cross-tenant leak
* quotas toujours corrects
* idempotence correcte

---

# # **16. CI/CD — Compliance Rules**

### 🚫 Bloquant :

* violation invariants
* double ENQUEUED
* job exécuté sans être READY
* absence de state machine transitions
* pas de logs structurés
* pas de retry control
* absence de idempotency_key
* cross-tenant execution

### ⚠ Warning :

* absence de tests crash recovery
* absence de tests concurrency

---

# # **17. Checklist finale SRE++ Scheduler/Dispatcher**

* [ ] state machine entièrement respectée
* [ ] idempotence garantie
* [ ] quota state machine respectée
* [ ] scheduling window stable
* [ ] ordering par compte correct
* [ ] aucun double dispatch
* [ ] aucun job bloqué
* [ ] crash recovery fonctionnel
* [ ] logs complets
* [ ] métriques complètes
* [ ] test suite conforme
* [ ] CI compliance activée

---

# # **18. Conclusion**

DOC-013 est l’un des documents les plus critiques de Sparkmetriq S2.
Il définit la **précision mécanique** du moteur d’automatisation.

Il garantit :

* fiabilité,
* sécurité,
* scalabilité,
* cohérence,
* absence de doublons,
* maîtrise des pannes,
* cohérence cross-tenants.

> **Toute violation de DOC-013 bloque la PR et empêche le déploiement en production.**

---
