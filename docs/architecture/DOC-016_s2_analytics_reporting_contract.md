Voici **DOC-016 — S2 Analytics & Reporting Contract (Event Sourcing, Metrics, BI Feed)**
Version longue (12–18 pages), format Markdown, conçue pour structurer **toute la couche analytique et reporting de Sparkmetriq S2**, incluant :

* métriques SRE++
* logs structurés
* events normalisés
* pipeline analytique
* BI feed (Mongo secondary / warehouse)
* dashboards Admin Panel
* futur moteur S4 Analytics

À intégrer dans :

```
docs/architecture/DOC-016_s2_analytics_reporting_contract.md
```

---

# 📘 **DOC-016 — S2 Analytics & Reporting Contract**

*Document Technique — Sparkmetriq S2 / Event Sourcing / Observability / Analytics Pipeline / BI*

```markdown
---
title: DOC-016 — S2 Analytics & Reporting Contract
version: 1.0
status: Stable
category: Architecture / Analytics / Observability / Reporting
last_updated: 2025-02-09
---
```

---

# # **1. Objectif du document**

Sparkmetriq S2 manipule des données stratégiques :

* publications planifiées
* publications exécutées
* retries
* erreurs connecteurs
* débits exécutés
* quotas
* utilisation par agence
* performance workers
* activité API
* activité du scheduler
* succès / échec par plateforme

Le système doit garantir :

* **visibilité totale**
* **mesures fiables et exploitables**
* **un canal BI cohérent**
* **des métriques SRE++** pour piloter qualité et performance
* **des dashboards Admin Panel** précis et robustes
* **un système d’événements unifié** pour S3/S4

DOC-016 définit le **contrat officiel** des analytics Sparkmetriq S2.

---

# # **2. Périmètre**

S’applique à :

* Scheduler (DOC-013)
* Dispatcher
* Workers (DOC-015)
* Connecteurs (DOC-012)
* Quotas (DOC-004)
* Storage & Media (DOC-010)
* UnifiedPostPayload (DOC-014)
* Admin Panel (DOC-011)
* MongoDB Primary & Secondary
* Pipeline BI
* Observability (DOC-006)

---

# # **3. Architecture générale du pipeline analytics**

```mermaid
flowchart TD
A[Scheduler] --> E[Event Bus]
B[Dispatcher] --> E
C[Workers] --> E
D[Connectors] --> E

E --> F[Event Normalizer]
F --> G[Analytics Store (Mongo secondary)]
G --> H[BI Feed → Warehouse (future)]
G --> I[Admin Panel Metrics & Dashboards]

E --> J[Prometheus Exporter]
```

---

# # **4. Event Sourcing Contract (obligatoire)**

Chaque module de Sparkmetriq doit produire un **événement structuré immuable** pour :

* les transitions d’état
* les actions externes
* les erreurs
* les succès
* les retries
* les décisions du scheduler
* les limites de quotas

### Format unique (JSON) :

```json
{
  "timestamp": "2025-02-09T12:05:22Z",
  "event_type": "s2.job.dispatched",
  "job_id": "job_883",
  "org_id": "org_99",
  "platform": "instagram",
  "actor": "dispatcher",
  "payload": {
    "state_from": "READY",
    "state_to": "ENQUEUED",
    "priority": 2
  },
  "meta": {
    "request_id": "req_702",
    "span_id": "sp_11"
  }
}
```

Règles :

* immuable
* event_type en snake.case
* timestamp UTC ISO
* org_id obligatoire
* aucun token/secret
* payload doit être minimal

---

# # **5. Typologie des événements (catalogue complet)**

### 5.1. Scheduler Events

* `s2.scheduler.job.validated`
* `s2.scheduler.job.scheduled`
* `s2.scheduler.job.ready`
* `s2.scheduler.decision.batch`

### 5.2. Dispatcher Events

* `s2.dispatcher.job.enqueued`
* `s2.dispatcher.rabbitmq.ack`
* `s2.dispatcher.error`

### 5.3. Worker Events

* `s2.worker.job.processing`
* `s2.worker.job.success`
* `s2.worker.job.failure`
* `s2.worker.retry`
* `s2.worker.timeout`

### 5.4. Connector Events

* `s2.connector.call.start`
* `s2.connector.call.success`
* `s2.connector.call.retryable_error`
* `s2.connector.call.error`

### 5.5. Quotas Events

* `s2.quotas.reserved`
* `s2.quotas.released`
* `s2.quotas.consumed`
* `s2.quotas.exceeded`

---

# # **6. Analytics Store (MongoDB secondary)**

## 6.1. Pourquoi une Secondary Analytics DB ?

* BI doit éviter toute charge sur la DB primaire
* events volumineux
* writes massives acceptables
* lecture fréquente (dashboards)
* altération facile du schéma (audit logs)

## 6.2. Collections principales

### `analytics_events`

Tous les events normalisés.

Index :

```
{ org_id: 1, event_type: 1, timestamp: -1 }
{ job_id: 1 }
{ platform: 1, timestamp: -1 }
{ actor: 1 }
```

### `analytics_daily`

Agrégats journaliers.

### `analytics_reliability`

Données SRE++ :

* SLIs (latence, erreur, débit)
* SLOs
* disponibilité interne

---

# # **7. BI Feed (warehouse)**

Le système BI (futur BigQuery / Snowflake / etc.) reçoit :

* events normalisés
* snapshots journaliers
* agrégats agences
* scoring qualité connecteurs
* métriques workers

Règle :

> Aucun raw event interne ne doit être envoyé au warehouse
> → seulement des structures normalisées.

---

# # **8. Métriques (Prometheus / SRE++)**

DOC-006 définit l’observabilité, DOC-016 définit **les métriques officielles S2**.

## 8.1. Métriques Scheduler

```
scheduler_queue_length
scheduler_batch_size
scheduler_decision_latency_seconds
scheduler_ready_jobs
scheduler_priority_distribution
```

## 8.2. Métriques Dispatcher

```
dispatcher_enqueued_total
dispatcher_ack_latency_seconds
dispatcher_rabbitmq_errors_total
```

## 8.3. Métriques Workers

```
worker_active_jobs
worker_execution_latency_seconds
worker_timeout_total
worker_retry_total
worker_success_total
worker_failure_total
```

## 8.4. Métriques Connecteurs

```
connector_api_latency_seconds{platform="instagram"}
connector_api_errors_total{platform="tiktok"}
connector_rate_limit_hits_total
connector_publish_success_total
connector_publish_failure_total
```

## 8.5. Métriques Quotas

```
quotas_reserved_total
quotas_consumed_total
quotas_released_total
quotas_exceeded_total
```

---

# # **9. Dashboards Admin Panel (DOC-011 alignment)**

Les dashboards doivent être alimentés EXCLUSIVEMENT par :

* MongoDB analytics secondary
* Prometheus metrics
* Aggregation API

### 9.1. Dashboard Calendrier

* volume posts
* statut posts (success/failure)
* temps d’exécution

### 9.2. Dashboard Quotas

* évolution consommation
* alertes dépassement

### 9.3. Dashboard Fiabilité

* SLO 99% sur "job completed successfully"
* retries par plateforme
* erreurs par worker

### 9.4. Dashboard Usage Agence

* nombre de publications
* plateformes les plus utilisées
* évolution hebdomadaire
* performance des carrousels / reels

---

# # **10. SLOs (Service Level Objectives)**

Sparkmetriq S2 définit les SLOs officiels :

| SLO                      | Objectif              |
| ------------------------ | --------------------- |
| Publication Success Rate | ≥ 98%                 |
| Scheduler Latency        | < 3 s                 |
| Worker Execution Time    | < 8 s 90th percentile |
| Retry Failure            | < 3%                  |
| BI Feed Lag              | < 5 min               |

---

# # **11. Failure Reporting Contract**

Chaque échec doit produire :

```json
{
  "event_type": "s2.worker.job.failure",
  "job_id": "...",
  "reason": "connector_invalid_token",
  "platform": "...",
  "org_id": "...",
  "severity": "error"
}
```

Catégories :

* **internal_error**
* **connector_error**
* **quota_error**
* **validation_error**
* **timeout**
* **network_error**
* **tenant_violation**

---

# # **12. Quotas Reporting (DOC-004 alignment)**

Pour chaque transition quota :

```
s2.quotas.reserved
s2.quotas.consumed
s2.quotas.released
s2.quotas.exceeded
```

Metrics par tenant :

```
quotas_used_percentage{org_id="x"}
```

---

# # **13. Tests obligatoires**

## Unit tests

* event formatting
* metric counters
* timestamp generation

## Integration tests

* BI feed simulation
* large volume events
* dashboard queries

## E2E tests

* 1000 jobs → aggregator accuracy
* faults → correct reporting
* scheduler failover → reporting complet

---

# # **14. CI/CD Compliance**

### 🚫 Bloquant

* event sans org_id
* event avec token/secret
* event non normalisé
* métriques manquantes
* dashboards non alimentés
* absence d’indexes analytics
* accusations non structurées

### ⚠ Warning

* schéma metadata non documenté
* event payload excessif
* agrégats trop lourds

---

# # **15. Checklist finale SRE++ Analytics**

* [ ] event sourcing en place
* [ ] normalisation réussie
* [ ] logs structurés
* [ ] métriques complètes
* [ ] BI feed opérationnel
* [ ] dashboards UI cohérents
* [ ] aucun token dans logs
* [ ] cross-tenant supprimé
* [ ] SLO respectés
* [ ] CI/CD compliance OK

---

# # **16. Conclusion**

DOC-016 formalise **la colonne vertébrale analytique** de Sparkmetriq S2.
Il garantit :

* transparence totale,
* qualité des données,
* fiabilité opérationnelle,
* capacité BI,
* scalabilité technique,
* UX améliorée dans admin panel,
* préparation aux modules S3 & S4.

> **Toute violation de DOC-016 doit bloquer la PR.**

---
