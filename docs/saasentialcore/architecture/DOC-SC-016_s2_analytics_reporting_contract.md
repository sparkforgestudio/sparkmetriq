Voici **DOC-SC-016 — S2 Analytics & Reporting Contract (Event Sourcing, Metrics, BI Feed)**,
version **longue**, structurée, normative, et strictement cohérente avec toute la série SC-001 → SC-015.

Ce document définit **le système d’analytics officiel de Sparkmetriq S2**, depuis la source événementielle jusqu’aux dashboards BI, en respectant :

* l’event sourcing (DOC-SC-006),
* l’observabilité SRE++ (DOC-SC-009),
* l’isolation multi-tenant (DOC-SC-004),
* la compatibilité Scheduler / Worker (DOC-SC-013 / 015),
* la gouvernance data multi-startup.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-016_s2_analytics_reporting_contract.md
```

---

# 📘 `DOC-SC-016_s2_analytics_reporting_contract.md`

````markdown
---
title: DOC-SC-016 — S2 Analytics & Reporting Contract
version: 1.0
status: Stable
category: SaasentialCore / Sparkmetriq S2 / Analytics / BI / Event Sourcing
last_updated: 2025-02-18
---

# 1. Objectif du document

DOC-SC-016 définit le **contrat analytique officiel de Sparkmetriq S2**.  
Il décrit :

- les sources de vérité analytiques,
- les événements analysables,
- les métriques business et techniques,
- la structure du data pipeline analytique,
- les règles de stockage et d’agrégation,
- l’exposition BI / reporting,
- la conformité multi-tenant / multi-produit,
- l’intégration avec SRE et observabilité.

Ce document garantit que **toute action S2 est mesurable, auditée et exploitable**.

---

# 2. Principes fondamentaux

## ✔ 2.1. Event-sourced by design  
Aucune métrique business ne doit être calculée à partir d’états mutables.  
**Les événements sont la source de vérité.**

## ✔ 2.2. Séparation Analytics vs Runtime  
Le pipeline analytics ne doit **jamais** impacter le chemin critique S2.

## ✔ 2.3. Multi-tenant strict  
Aucune donnée analytique ne traverse les frontières tenant (DOC-SC-004).

## ✔ 2.4. Analytics ≠ Observability  
- Observability = santé système (DOC-SC-009)  
- Analytics = performance produit / business

---

# 3. Sources de données analytiques

## 3.1. Event Bus (source primaire)

Événements produits par S2 (DOC-SC-006) :

- `s2.post.scheduled`
- `s2.post.queued`
- `s2.post.dispatched`
- `s2.post.executed`
- `s2.post.published`
- `s2.post.failed`
- `s2.post.dead`
- `s2.quota.reserved`
- `s2.quota.released`

Chaque événement contient :

- tenant metadata,
- product_id,
- platform,
- timestamps,
- job_id / post_id.

---

## 3.2. Metrics techniques (source secondaire)

Issues de Prometheus (DOC-SC-009) :

- latence scheduler
- latence worker
- retry count
- error rate

Utilisées uniquement pour **corrélation**, jamais comme source business.

---

# 4. Modèle Event Sourcing Analytics

## 4.1. Event Record canonical

Chaque événement est persisté sous forme canonique :

```json
{
  "event_id": "uuid",
  "event_type": "s2.post.published",
  "timestamp": "2025-02-18T10:12:44Z",
  "startup_id": "stp_1",
  "org_id": "org_22",
  "product_id": "sparkmetriq",
  "platform": "instagram",
  "job_id": "job_abc",
  "post_id": "post_xyz",
  "payload": { ... }
}
````

---

## 4.2. Immutabilité

* aucun événement n’est modifié,
* corrections = nouveaux événements compensatoires,
* suppression interdite (sauf RGPD, voir section 12).

---

# 5. Data Pipeline Analytics

```mermaid
flowchart LR
    EventBus --> Collector
    Collector --> RawEventStore
    RawEventStore --> Aggregator
    Aggregator --> AnalyticsDB
    AnalyticsDB --> BI
```

### Composants :

| Composant     | Rôle                        |
| ------------- | --------------------------- |
| Collector     | Consomme événements S2      |
| RawEventStore | Stockage brut (append-only) |
| Aggregator    | Calcul agrégats             |
| AnalyticsDB   | Tables optimisées BI        |
| BI            | Dashboards / exports        |

---

# 6. Raw Event Store

### Caractéristiques :

* append-only,
* partitionné par :

  * startup_id
  * org_id
  * product_id
  * date (YYYY-MM-DD)
* retention longue (≥ 12 mois),
* compressé.

Exemple :

```
analytics_raw/
  sparkmetriq/
    stp_1/
      org_22/
        2025-02-18.jsonl
```

---

# 7. Agrégations analytiques S2

## 7.1. Agrégats standards

| Agrégat               | Description               |
| --------------------- | ------------------------- |
| posts_scheduled       | nombre de posts planifiés |
| posts_published       | nombre de posts publiés   |
| posts_failed          | échecs définitifs         |
| retry_rate            | ratio retries             |
| publish_latency       | scheduled → published     |
| platform_success_rate | par plateforme            |
| quota_usage           | consommation quotas       |

---

## 7.2. Fenêtres temporelles

* temps réel (rolling 5 min),
* journalier,
* hebdomadaire,
* mensuel.

---

# 8. Modèle de données AnalyticsDB

Exemple table agrégée :

```json
{
  "date": "2025-02-18",
  "startup_id": "stp_1",
  "org_id": "org_22",
  "product_id": "sparkmetriq",
  "platform": "instagram",
  "posts_published": 143,
  "posts_failed": 3,
  "avg_publish_latency_sec": 18.2,
  "retry_rate": 0.04
}
```

Index obligatoires :

* (startup_id, org_id, product_id, date)
* (platform, date)

---

# 9. Reporting & BI Exposure

## 9.1. Dashboards standards

Chaque organisation doit disposer de :

* Overview S2
* Performance par plateforme
* Heatmap horaires de publication
* Erreurs & retries
* Consommation quotas
* SLA / SLO tenant

---

## 9.2. Exports

Formats autorisés :

* CSV
* Parquet
* JSON

Expositions possibles :

* API `/analytics/export`
* S3 / Object Storage
* Connecteur BI (Metabase, Superset, PowerBI)

---

# 10. Multi-Tenant & Sécurité Analytics

### Règles strictes :

* filtrage obligatoire par tenant,
* aucun accès cross-org,
* aucun accès cross-startup,
* agrégats globaux uniquement pour `core.admin`.

Aligné DOC-SC-004 / DOC-SC-005.

---

# 11. Observabilité du pipeline analytics

Le pipeline analytics doit produire :

* logs ingestion events,
* métriques :

  * events_consumed_total
  * events_dropped_total
  * aggregation_latency_seconds
* alertes :

  * lag ingestion > seuil
  * drop rate > seuil

---

# 12. RGPD & Data Retention

## 12.1. Données personnelles

* user_id pseudonymisé,
* aucun contenu sensible dans analytics,
* purge sur demande RGPD.

## 12.2. Rétention

| Type           | Durée      |
| -------------- | ---------- |
| Raw events     | 12–24 mois |
| Agrégats       | 36 mois    |
| Logs analytics | 90 jours   |

---

# 13. Tests & Validation

Tests obligatoires :

* replay event log,
* cohérence agrégats,
* isolation tenant,
* volumétrie (load tests),
* idempotence collector.

---

# 14. CI/CD Compliance Rules

### 🚫 Bloquant

* analytics sans event source,
* agrégats calculés depuis runtime state,
* absence tenant_id dans analytics,
* pipeline bloquant S2 runtime,
* suppression événement non compensée,
* fuite cross-tenant.

### ⚠ Warning

* absence de dashboards standards,
* absence tests replay,
* absence alerting pipeline.

---

# 15. Invariants non négociables

1. Les événements sont la source unique de vérité analytics.
2. Aucun calcul business dans le runtime S2.
3. Isolation tenant stricte.
4. Pipeline analytics asynchrone.
5. Données analytiques auditables et rejouables.
6. Toute PR violant DOC-SC-016 est bloquée.

---

# 16. Conclusion

DOC-SC-016 établit une **architecture analytics industrielle** pour Sparkmetriq S2 :

* event-sourcing natif,
* analytics fiables et auditables,
* reporting BI prêt entreprise,
* conformité SRE++ / sécurité / RGPD,
* support multi-startup et hyperscale.

C’est le socle décisionnel de la plateforme.

```
