Voici **DOC-SC-021 — S2 Monitoring Dashboards Contract (Grafana Templates & SRE Maps)**,
version **longue**, normative, orientée **exploitation réelle**, et **transverse à toutes les startups / produits** opérant sur SaasentialCore.

Ce document formalise **ce qui doit être visible, comment, par qui, et avec quels invariants**, afin que **rien d’important ne puisse casser sans être vu**.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-021_monitoring_dashboards_contract.md
```

---

# 📘 `DOC-SC-021_monitoring_dashboards_contract.md`

```markdown
---
title: DOC-SC-021 — Monitoring Dashboards Contract (Grafana & SRE Maps)
version: 1.0
status: Stable
category: SaasentialCore / Observability / Monitoring / SRE
last_updated: 2025-02-18
---

# 1. Objectif du document

DOC-SC-021 définit le **contrat officiel de monitoring et de visualisation** pour SaasentialCore et les produits qui l’utilisent.

Il formalise :
- les **dashboards obligatoires**,
- les **métriques minimales requises**,
- les **niveaux de lecture (RBAC)**,
- les **cartographies SRE (Service Maps)**,
- les **règles de nommage et structuration Grafana**,
- les **invariants d’observabilité non négociables**.

Ce document garantit que :
> *si le système fonctionne, on le voit ;  
> s’il dégrade, on le voit ;  
> s’il casse, on sait où et pourquoi.*

---

# 2. Principes fondamentaux

## ✔ 2.1. Monitoring ≠ Logging ≠ Analytics  
- Monitoring : **état du système en temps réel**
- Logging : **événements détaillés**
- Analytics : **performance produit / business**

DOC-SC-021 concerne **uniquement le monitoring**.

---

## ✔ 2.2. Tout ce qui est critique doit être visible  
Si un composant peut provoquer :
- une perte de données,
- une indisponibilité,
- un incident tenant,

alors il **doit avoir un dashboard dédié**.

---

## ✔ 2.3. Multi-tenant first-class  
Le monitoring doit permettre :
- une vue globale (plateforme),
- une vue par startup,
- une vue par organisation,
- une vue par produit.

Sans fuite cross-tenant.

---

# 3. Stack de monitoring de référence

## 3.1. Outils standards

| Fonction | Outil |
|-------|------|
| Metrics | Prometheus |
| Dashboards | Grafana |
| Logs | Loki |
| Traces | OpenTelemetry |
| Alerting | Alertmanager |

Toute alternative doit respecter **les mêmes contrats**.

---

# 4. Hiérarchie des dashboards (obligatoire)

```

📊 Platform Overview
├── Core Infrastructure
├── API Gateway
├── Scheduler
├── Dispatcher
├── Workers
├── Connectors
├── AI / Inference
├── Analytics Pipeline
├── Databases
└── Message Broker

```

---

# 5. Dashboard 1 — Platform Overview (global)

## Objectif
Vue synthétique **temps réel** de la santé de la plateforme.

### KPIs obligatoires
- availability %
- error rate global
- request rate
- latency P95 / P99
- active tenants
- active jobs
- failed jobs

### Invariants
- visible en < 5 secondes
- aucune dépendance à une vue détaillée

---

# 6. Dashboard 2 — API Gateway

### Métriques obligatoires
- `api_requests_total`
- `api_requests_4xx_total`
- `api_requests_5xx_total`
- `api_rate_limit_exceeded_total`
- `api_latency_seconds{quantile}`

### Dimensions
- route
- product_id
- org_id (agrégé)
- status_code

---

# 7. Dashboard 3 — Scheduler

### Métriques
- `scheduler_queue_depth`
- `scheduler_delay_seconds`
- `scheduler_jobs_scheduled_total`
- `scheduler_jobs_late_total`

### Visualisations
- backlog dans le temps
- heatmap horaire
- drift planning vs exécution

---

# 8. Dashboard 4 — Dispatcher

### Métriques
- `dispatcher_jobs_dispatched_total`
- `dispatcher_dispatch_latency_seconds`
- `dispatcher_starvation_events`
- `dispatcher_retry_enqueued_total`

### Objectif
Détecter :
- starvation tenant
- déséquilibre plateforme
- saturation workers

---

# 9. Dashboard 5 — Workers

### Métriques
- `worker_jobs_running`
- `worker_jobs_success_total`
- `worker_jobs_failed_total`
- `worker_execution_seconds`
- `worker_oom_total`
- `worker_timeouts_total`

### Vues
- par worker
- par plateforme
- par tenant (agrégé)

---

# 10. Dashboard 6 — Connectors

### Métriques
- `connector_requests_total`
- `connector_errors_total`
- `connector_429_total`
- `connector_latency_seconds`

### Par plateforme
- Instagram
- TikTok
- Threads
- X
- Reddit
- OnlyFans
- autres

---

# 11. Dashboard 7 — AI / Inference

### Métriques
- `ai_inference_total`
- `ai_inference_latency_seconds`
- `ai_inference_timeout_total`
- `ai_tokens_in_total`
- `ai_tokens_out_total`
- `ai_cost_estimated`

### Objectif
- contrôler coûts
- détecter dérives
- anticiper saturation

---

# 12. Dashboard 8 — Analytics Pipeline

### Métriques
- `analytics_events_ingested_total`
- `analytics_ingestion_lag_seconds`
- `analytics_events_dropped_total`
- `analytics_aggregation_latency_seconds`

---

# 13. Dashboard 9 — Databases

### MongoDB
- connections
- replication lag
- slow queries
- disk usage

### Objectif
- prévenir corruption
- prévenir saturation
- anticiper scale

---

# 14. Dashboard 10 — Message Broker

### RabbitMQ
- queue depth
- unacked messages
- publish rate
- consumer lag

---

# 15. SRE Service Maps (obligatoires)

Chaque service critique doit apparaître dans une **Service Map** :

```

API → Scheduler → Dispatcher → Worker → Connector → External API

```

### Objectif
- visualiser dépendances
- détecter point de rupture
- comprendre blast radius

---

# 16. RBAC & Accès aux dashboards

| Rôle | Accès |
|----|------|
| core.admin | tous dashboards |
| startup.owner | startup only |
| org.admin | org only |
| product.admin | produit only |
| support | lecture limitée |

Aucune vue cross-tenant non autorisée.

---

# 17. Nommage & Standards Grafana

### Dossiers
```

Grafana/
├── Platform/
├── Core/
├── Products/
│    ├── sparkmetriq/
│    ├── sparkpusher/
└── AI/

```

### Nommage métriques
- snake_case
- suffixes standards (`_total`, `_seconds`, `_bytes`)
- labels limités et contrôlés

---

# 18. Alerting (liaison DOC-SC-017)

Chaque dashboard doit être associé à :
- alertes critiques
- alertes majeures
- alertes mineures

Aucune métrique critique sans alerte.

---

# 19. CI/CD Compliance Rules

### 🚫 Bloquant
- service sans dashboard
- métrique critique sans visualisation
- métrique critique sans alerte
- fuite tenant dans labels
- dashboard non documenté

### ⚠ Warning
- absence SRE map
- absence P95/P99
- absence drill-down

---

# 20. Invariants non négociables

1. Aucun service critique sans dashboard.
2. Aucune métrique critique sans alerte.
3. Aucun dashboard sans RBAC.
4. Aucune fuite cross-tenant.
5. Toute panne doit être visible.
6. Toute PR violant DOC-SC-021 est bloquée.

---

# 21. Conclusion

DOC-SC-021 transforme le monitoring en **système nerveux central** de SaasentialCore :

- visibilité temps réel,
- compréhension systémique,
- anticipation des incidents,
- pilotage SRE++,
- exploitation multi-startup fiable.

Sans ce contrat, aucune plateforme ne peut prétendre à une exploitation sérieuse.
```
