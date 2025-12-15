Voici **DOC-SC-009 — Observability & SRE Contract (Core)**, version longue, ultra complète, alignée avec les pratiques SRE++ modernes (Google SRE, Observability Engineering, High Performance Python), et cohérente avec SaasentialCore + Produits (Sparkmetriq, Sparkpusher, futurs modules).

Ce document définit **tout le système d’observabilité du monorepo** : logs, métriques, traces, dashboards, alertes, budgets d’erreur, SLIs, SLOs, SLA, etc.
Il fixe les règles obligatoires que chaque module doit respecter.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-009_observability_sre_contract.md
```

---

# 📘 `DOC-SC-009_observability_sre_contract.md`

````markdown
---
title: DOC-SC-009 — Observability & SRE Contract (Core)
version: 1.0
status: Stable
category: SaasentialCore / Observability / SRE / Monitoring / Reliability
last_updated: 2025-02-15
---

# 1. Objectif du document

DOC-SC-009 définit la **charte d’observabilité et de fiabilité SRE** de l’écosystème SaasentialCore :

- collection de logs structurés,
- métriques systèmes et business,
- traces distribuées,
- dashboards Grafana standardisés,
- alerting fiable et hiérarchisé,
- budgets d’erreur,
- SLIs, SLOs, SLA,
- politique de retours automatiques (self-healing),
- intégration multi-tenant / multi-produit.

Ce contrat garantit que **Sparkmetriq, Sparkpusher et tout futur produit** restent observables, audités, et exploitables en production.

---

# 2. Principes fondamentaux de l’Observability SRE++

## ✔ 2.1. "You cannot fix what you cannot see"  
Chaque composant doit être observable par défaut.

## ✔ 2.2. Pas de logs non structurés  
Tous les logs doivent être en **JSON structuré**, jamais en texte brut.

## ✔ 2.3. Séparation **Logs → Metrics → Traces**  
Chacun a un rôle :

- Logs : granularité événementielle
- Metrics : monitoring temps réel, alerting
- Traces : déboggage cross-services

## ✔ 2.4. Observabilité multi-tenant & multi-produit  
Aligné DOC-SC-004 : chaque donnée d’observabilité doit être associée à un tenant et un produit.

## ✔ 2.5. SRE = responsabilité partagée  
Tous les produits doivent implémenter les standards.

---

# 3. Architecture d'observabilité

```mermaid
flowchart TD

    API --> Logs
    API --> Metrics
    API --> Traces

    Workers --> Logs
    Workers --> Metrics
    Workers --> Traces

    Scheduler --> Logs
    Scheduler --> Metrics
    Scheduler --> Traces

    Dispatcher --> Logs
    Dispatcher --> Metrics
    Dispatcher --> Traces

    Logs --> Loki/Elastic
    Metrics --> Prometheus
    Traces --> OpenTelemetry --> Jaeger

    Prometheus --> Grafana
    Loki --> Grafana
    Jaeger --> Grafana
````

---

# 4. Logs structurés (obligatoire)

## 4.1. Format standard JSON

```json
{
  "timestamp": "2025-02-15T10:21:34.111Z",
  "level": "INFO",
  "event": "post.scheduled",
  "product_id": "sparkmetriq",
  "startup_id": "stp_1",
  "org_id": "org_22",
  "service": "scheduler",
  "trace_id": "abc-123",
  "payload": { ... }
}
```

### Champs obligatoires

| Champ               | Signification                         |
| ------------------- | ------------------------------------- |
| timestamp           | ISO 8601 UTC                          |
| level               | INFO/WARN/ERROR/CRITICAL              |
| event               | nom structuré                         |
| product_id          | aligné DOC-SC-002                     |
| startup_id / org_id | aligné DOC-SC-004                     |
| service             | API / worker / scheduler / dispatcher |
| trace_id            | aligné DOC-SC-006                     |
| payload             | données supplémentaires               |

## 4.2. Interdictions

* ❌ logs multi-lignes,
* ❌ logs sans tenant context,
* ❌ logs contenant secrets (aligné DOC-019),
* ❌ logs de debug non filtrés.

---

# 5. Metrics (Prometheus)

## 5.1. Règle d’or : **Toutes les métriques doivent être labelisées tenant + produit**

Ex :

```
s2_scheduled_jobs_total{product_id="sparkmetriq", org_id="org_22"}
```

## 5.2. Types de métriques obligatoires

### A. Compteurs (counters)

* `api_requests_total`
* `worker_jobs_total`
* `events_produced_total`
* `events_consumed_total`
* `retry_total`

### B. Latences (histograms)

* `api_latency_seconds`
* `scheduler_latency_seconds`
* `worker_execution_seconds`

### C. États (gauges)

* `queue_depth`
* `active_workers`
* `db_connections`

### D. Business Metrics

Sparkmetriq S2 :

* `posts_scheduled_total`
* `posts_published_total`
* `connectors_failures_total`
* `quota_consumption_total`

---

# 6. Traces distribuées (OpenTelemetry)

Chaque requête doit générer un trace_id unique propagé via :

* API → Scheduler → Dispatcher → Worker → Connecteur.

### Exemple de propagation :

```
X-Trace-Id: abc-1223-fg44
```

## 6.1. Span obligatoires

* `api.request`
* `scheduler.schedule`
* `dispatcher.dispatch`
* `worker.execute`
* `connector.call`
* `db.query`

## 6.2. Interdictions

* ❌ ne pas propager trace_id
* ❌ spans sans metadata tenant

---

# 7. SLO / SLI / SLA

## 7.1. SLIs (indicateurs de qualité)

| SLI                    | Description |
| ---------------------- | ----------- |
| Latence API P95        | < 250ms     |
| Job Success Rate       | > 99%       |
| Scheduler Delay        | < 5 sec     |
| Event Delivery Success | > 99.9%     |
| Worker Error Rate      | < 0.5%      |

## 7.2. SLOs (objectifs)

* Uptime API : **99.5%**
* Uptime Scheduler : **99%**
* Path S2 Planification → Publication : **99% succès**

## 7.3. SLA (engagement externe)

Défini au niveau startup → clients.

---

# 8. Alerting Rules

### 8.1. Alertes critiques (pager)

* API error rate > 5%
* Worker failure > 10%
* Dead letter queue > 100 messages
* Scheduler non actif > 60s

### 8.2. Alertes warnings (email/slack)

* Latence API P95 > 300ms
* Retry inhabituel
* Spike usage tenant

---

# 9. Dashboards Grafana (obligatoires)

Chaque produit doit avoir un dashboard :

```
grafana/
    sparkmetriq/
        overview.json
        scheduler.json
        workers.json
        connectors.json
```

Chaque dashboard doit inclure :

* tenants filtrables,
* produit filtrable,
* heatmap délais scheduler,
* répartition erreurs par connecteur,
* latence par étape S2,
* retries total.

---

# 10. Observabilité Multi-Startup et Multi-Produit

À chaque log / metric / trace, les labels suivants sont **obligatoires** :

* `startup_id`
* `org_id`
* `product_id`
* `service`
* `trace_id`

Interdit :

* ❌ cross-tenant logs merges
* ❌ metrics globales non filtrables par tenant

---

# 11. Tests d’observabilité

Tests unitaires, intégration & E2E doivent valider :

* logs conformes
* metrics exposées
* traces générées
* labels tenant présents
* absence de secrets dans logs

---

# 12. CI/CD Compliance

### 🚫 Bloquant :

* logs non structurés
* absence de tenant metadata
* pas de métriques business obligatoires
* pas de trace_id propagé
* violation d’un SLO > 3 jours
* connecteur sans metrics
* workers silencieux (pas de logs/metrics)

### ⚠ Warning :

* absence de dashboards produit
* absence d’alertes pour un composant clé
* absence de tests observabilité

---

# 13. Invariants non négociables

1. Aucune fonctionnalité n’est considérée “terminée” sans observabilité.
2. Aucun composant n’existe sans logs, metrics & traces.
3. Les logs ne doivent jamais contenir de secrets.
4. Les métriques doivent toujours être labelisées tenant + produit.
5. Toute PR violant DOC-SC-009 est bloquée.
6. SRE n’est pas optional — c’est une exigence de production.

---

# 14. Conclusion

DOC-SC-009 définit le **piliers SRE++** du projet SaasentialCore :

* Observabilité totale, structurée, multi-tenant, multi-produit.
* Résilience, sécurité, visibilité complète sur runtime.
* Standards professionnels compatibles hyperscale.

C’est un document de référence obligatoire pour tous les produits présents et futurs.

```
### 👉 **DOC-SC-010 — Configuration & Secrets Management Contract (Vault / env / keys)**
