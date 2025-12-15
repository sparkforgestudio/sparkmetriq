Voici **DOC-006 — Observability Contract (Version longue 6–12 pages)**, conçu selon les standards **SRE++ / Google SRE / Observability Engineering / DDIA**, entièrement adapté à Sparkmetriq S2/S3/S4 (multi-nœuds, multi-services, scheduler, dispatcher, connecteurs, workers, API).

Prêt à être placé dans :

```
docs/architecture/DOC-006_observability_contract.md
```

Ce document établit **le contrat d’observabilité obligatoire** :
logs structurés → métriques → traces → corrélation → alerting → dashboards Grafana → normes de qualité → exigences CI/CD.

---

# 📘 **DOC-006 — Observability Contract (Version longue)**

*Document Technique de Référence — Sparkmetriq SRE++ / Reliability / Monitoring Architecture*

```markdown
---
title: DOC-006 — Observability Contract
version: 1.0
status: Stable
category: Architecture / SRE / Observability / Monitoring
last_updated: 2025-01-30
---
```

---

# # **1. Objectif du document**

Ce document définit le **contrat d’observabilité** obligatoire dans tout Sparkmetriq, couvrant :

* logs structurés uniformisés,
* métriques applicatives et système,
* traces distribuées,
* corrélation end-to-end (API → Scheduler → Celery → Connecteurs),
* dashboards Grafana,
* alerting (SLO violation, erreurs critiques, quotas, retries).

Objectif :

> *donner aux équipes la capacité de comprendre, diagnostiquer et corriger un problème en moins de 5 minutes, même dans un système distribué complexe.*

Ce contrat suit les principes des ouvrages :
**Google SRE**, **Observability Engineering**, **DDIA**, et les meilleures pratiques modernes.

---

# # **2. Périmètre**

S’applique à **tous les services** Sparkmetriq :

* **API FastAPI**
* **Scheduler**
* **Dispatcher**
* **Workers Celery**
* **Connecteurs** (Instagram, TikTok, etc.)
* **Tasks planifiées**
* **DB Layer (MongoDB)**
* **Broker Layer (RabbitMQ)**
* **Admin Panel (via API logs)**

---

# # **3. Les 4 Piliers de l’Observabilité Sparkmetriq**

## ✔ **3.1. Logs structurés (obligatoires)**

Format unique JSON → lisible par machines et humains.

## ✔ **3.2. Métriques (Prometheus format)**

Métriques techniques + métier.

## ✔ **3.3. Traces distribuées (OpenTelemetry)**

Corrélation inter-service : request_id → task_id → external_call_id.

## ✔ **3.4. Événements métier (Business Events)**

Exemples :
`quota_reserved`, `quota_consumed`, `post_scheduled`, `retry_started`, `connector_call_failed`.

---

# # **4. Logs structurés — Standard unique Sparkmetriq**

## **4.1. Format JSON obligatoire**

Chaque log doit suivre la structure :

```json
{
  "timestamp": "2025-01-30T12:45:03.123Z",
  "level": "INFO",
  "service": "scheduler",
  "event": "post_scheduled",
  "request_id": "req_abc123",
  "job_id": "job_456",
  "org_id": "org_789",
  "idempotency_key": "...",
  "details": {
      "platform": "instagram",
      "scheduled_at": "2025-02-01T08:00:00Z"
  }
}
```

### Champs obligatoires :

| Champ             | Description                                   |
| ----------------- | --------------------------------------------- |
| `timestamp`       | ISO 8601 UTC                                  |
| `level`           | INFO / WARNING / ERROR / CRITICAL             |
| `service`         | api / scheduler / celery_worker / connector_X |
| `event`           | nom d’événement normalisé                     |
| `request_id`      | généré par middleware API                     |
| `task_id`         | id Celery si applicable                       |
| `idempotency_key` | obligatoire si effet externe                  |
| `org_id`          | toujours requis                               |

---

# # **5. Nommage des événements (Business Events)**

### Obligatoires :

| Service     | Événements                                                                |
| ----------- | ------------------------------------------------------------------------- |
| Scheduler   | `post_scheduled`, `quota_reserved`, `schedule_retry`                      |
| Dispatcher  | `job_dispatched`, `queue_error`                                           |
| Worker      | `execute_started`, `execute_success`, `execute_failed`, `retry_started`   |
| Quotas      | `quota_consumed`, `quota_released`                                        |
| Connecteurs | `external_call_started`, `external_call_success`, `external_call_failure` |
| API         | `api_request_received`, `api_request_completed`                           |

Les noms d'événements doivent être **constants**, **stables**, **documentés**.

---

# # **6. Tracing Distribué — OpenTelemetry obligatoire**

Chaque requête API initialise :

```
request_id
trace_id
span_id
```

Ces IDs doivent suivre :

| Composant      | Doit transmettre `trace_id` ? |
| -------------- | ----------------------------- |
| API            | ✔                             |
| Scheduler      | ✔                             |
| Celery Worker  | ✔                             |
| Connecteurs    | ✔                             |
| Mongo / Rabbit | partiel (metadata logs)       |

### Exemple de propagation :

```
API → Scheduler → Celery Worker → Connector → External platform
```

---

# # **7. Métriques Prometheus — Standard Sparkmetriq**

## **7.1. Métriques obligatoires**

### **API**

* `http_requests_total{route,method,status}`
* `http_request_duration_seconds_bucket{route}`
* `api_errors_total{type}`

---

### **Scheduler**

* `scheduled_jobs_total{org_id,platform}`
* `scheduler_retries_total{reason}`
* `scheduler_latency_seconds`

---

### **Workers**

* `worker_jobs_total{status}`
* `worker_retry_total{reason}`
* `idempotent_hit_total`

---

### **Connecteurs**

* `connector_calls_total{platform,status}`
* `connector_latency_seconds_bucket{platform}`
* `connector_failures_total{type}`

---

### **Quotas**

* `quota_reserved_total{org_id}`
* `quota_consumed_total{org_id}`
* `quota_released_total{org_id}`

---

# # **8. Dashboards Grafana — Obligatoires**

## **8.1. Dashboard S2 — Scheduler/Dispatcher**

Widgets :

* jobs scheduled (par org, plateforme)
* retry rate
* latency pipeline
* error types
* top idempotency hits

---

## **8.2. Dashboard Worker**

* task throughput
* retry rate
* error types
* queue latency
* idempotency audit

---

## **8.3. Dashboard Connecteurs**

Par plateforme :

* taux de succès
* temps de réponse
* erreurs 429 / 5xx
* retry rate

---

## **8.4. Dashboard Quotas**

* consommation journalière
* orgs proches de la limite
* transitions invalides
* anomalies (ex. double consommation)

---

# # **9. Alerting (SLO-driven)**

### **Critiques (pager)**

* double publication détectée
* quota consommé deux fois
* connecteur external 500 rate > X%
* scheduler stuck (> 30 sec sans progression)
* worker crash loop
* RabbitMQ down
* MongoDB unreachable

---

### **Alerte Warning**

* retry rate > seuil
* 429 rate élevé
* API latency > seuil
* absence de logs structurés

---

# # **10. Intégration avec la CI/CD**

La CI doit vérifier :

## 🚫 **Bloquant**

* absence de logs structurés dans nouveaux modules
* absence de `request_id` dans réponses API
* absence de `trace_id` dans scheduler / worker
* aucun événement métier dans actions critiques
* utilisation de `print()` (interdit)
* logs non JSON
* absence de métriques pour un nouveau service

## ⚠ Warning

* absence de tests d'observabilité
* métriques exposées mais non documentées
* événements nommés différemment du standard

---

# # **11. Requirements pour les développeurs**

Tout développeur doit respecter :

* **log obligatoire** pour tout effet externe
* **trace_id obligatoire** dans tout service distribué
* **métriques obligatoires** dans toute création de service
* **ban complet de `print()` et logs non structurés**
* **événements métier normalisés**

---

# # **12. Checklist finale Observability (SRE++)**

* [ ] logs JSON structurés
* [ ] request_id + trace_id propagés
* [ ] événements métier émis pour chaque transition importante
* [ ] métriques Prometheus exposées par chaque service
* [ ] dashboards Grafana complets
* [ ] alerting configuré (SLO-based)
* [ ] CI vérifie l'observabilité
* [ ] aucun print()
* [ ] retry/quotas/idempotence corrélés via trace_id
* [ ] conformité DOC-001 → DOC-005

---

# # **13. Conclusion**

DOC-006 définit la **colonne vertébrale** du monitoring Sparkmetriq.
Sans observabilité :

* impossible de diagnostiquer un bug rapidement,
* impossible de détecter une double publication,
* impossible de suivre les quotas correctement,
* impossible de maintenir la fiabilité globale.

Ce document est **obligatoire** et fait partie intégrante du standard SRE++ Sparkmetriq.

> **Toute nouvelle fonctionnalité doit être conforme à DOC-006 pour être mergée.**

---
