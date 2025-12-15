Parfait.
Je génère maintenant **DOC-SC-004 — Core Multi-Tenant & Data Isolation Contract**, version longue, propre, cohérente avec les contrats précédents, et compatible avec Sparkmetriq S2, Sparkpusher, ainsi que les futurs produits multi-startup.

Ce document est **fondamental** : c’est lui qui garantit que chaque agence, chaque startup, chaque produit et même chaque worker reste strictement isolé.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-004_core_multi_tenant_data_isolation_contract.md
```

---

# 📘 `DOC-SC-004_core_multi_tenant_data_isolation_contract.md`

```markdown
---
title: DOC-SC-004 — Core Multi-Tenant & Data Isolation Contract
version: 1.0
status: Stable
category: SaasentialCore / Multi-Tenant / Security / Data Isolation
last_updated: 2025-02-14
---

# 1. Objectif du document

DOC-SC-004 définit le **contrat multi-tenant central de SaasentialCore**, garantissant :

- séparation stricte des organisations (agences),
- isolation entre startups,
- isolation entre produits au runtime,
- règles de stockage des données,
- politique d’accès pour API, workers, scheduler et services,
- intégrité des journaux,
- sécurité des secrets (aligné sur DOC-019),
- cohérence pour les produits Sparkmetriq, Sparkpusher, et futurs.

Ce document accompagne :

- DOC-SC-001 (architecture workspace),
- DOC-SC-002 (enregistrement produits),
- DOC-SC-003 (DI Container),
- DOC-019 (secrets & configuration).

---

# 2. Le modèle multi-tenant dans SaasentialCore

SaasentialCore doit gérer **trois niveaux d’isolation** :

```

Startup      = une marque / entreprise indépendante dans le SaaS global
Organisation = un client interne de cette startup (ex : une agence)
Product      = une application métier utilisée par une organisation

````

Visuellement :

```mermaid
flowchart TD
    Startup --> Org1
    Startup --> Org2
    Org1 --> Products
    Org2 --> Products
````

### Exemple réel :

* Startup = *Musai Agency Platform*
* Organisations = agences clientes
* Produits = Sparkmetriq, Sparkpusher, etc.

---

# 3. Identifiants obligatoires (tenant identifiers)

Chaque entité doit obligatoirement posséder ces identifiants :

| Niveau       | Identifiant  | Format     | Rôle             |
| ------------ | ------------ | ---------- | ---------------- |
| Startup      | `startup_id` | `str` UUID | isolement global |
| Organisation | `org_id`     | `str` UUID | isolement client |
| Produit      | `product_id` | `str` slug | isolement métier |
| Utilisateur  | `user_id`    | `str` UUID | identité locale  |

Des identifiants dérivés peuvent exister :

* `tenant_key_id` (clé de chiffrement)
* `tenant_bucket_prefix`
* `tenant_database_prefix`

---

# 4. Modèle de données multi-tenant

Les données doivent être **partitionnées logiquement** selon ce modèle :

```python
Document {
    startup_id: str
    org_id: str
    product_id: str
    ...
}
```

Ce triplé est **obligatoire pour toute donnée persistée**.

### Interdictions absolues :

* ❌ stocker un document produit sans `product_id`
* ❌ mélanger des orgas de startups différentes dans une même collection
* ❌ requêtes globales sans filtre tenant dans les produits
* ❌ storing tenants in separate databases *seulement si non justifié*

---

# 5. Règles de partitionnement des données (MongoDB)

## 5.1. Partitionnement logique (obligatoire)

Les collections doivent inclure les trois identifiants :

```
startup_id + org_id + product_id
```

Index recommandé :

```python
db.collection.create_index([
    ("startup_id", 1),
    ("org_id", 1),
    ("product_id", 1)
])
```

## 5.2. Partitionnement physique (optionnel selon scale)

Pour scale extrême :

* base par startup (`db_startup_xxx`)
* ou buckets S3 par startup

**Mais pas avant d’en avoir besoin.**

---

# 6. Isolation dans les services (Core vs Produits)

### 6.1. SaasentialCore

Les services Core doivent :

* être agnostiques produit,
* refuser toute action sans `context` tenant valide.

### 6.2. Produits

Un service produit doit **toujours** exiger un contexte tenant :

```python
class SchedulerService:
    def run(self, context: TenantContext, payload):
        ...
```

Il est interdit d’utiliser un service produit comme :

```python
SchedulerService().run(payload)  # interdit
```

---

# 7. TenantContext (contrat d’exécution)

Toutes les opérations runtime doivent être contextualisées via :

```python
class TenantContext(BaseModel):
    startup_id: str
    org_id: str
    product_id: str
    user_id: Optional[str]
```

### 7.1. Acquisition du contexte

Le contexte doit être obtenu :

* via JWT,
* via FastAPI Depends(),
* ou via DI pour Workers/Scheduler.

### 7.2. Utilisation obligatoire

Tout service doit avoir une signature de ce type :

```python
def execute(self, context: TenantContext, input):
```

---

# 8. Isolation dans API (FastAPI)

L’API doit :

1. extraire `startup_id`, `org_id`, `user_id`, `product_id` depuis le JWT
2. interdire toute requête sans contexte tenant valide
3. injecter ce contexte via DI dans toutes les routes

Exemple :

```python
def get_tenant_context(token=Depends(authenticate)):
    return TenantContext(
        startup_id=token.startup_id,
        org_id=token.org_id,
        product_id=token.product_id,
        user_id=token.user_id
    )
```

---

# 9. Isolation dans Workers

Les workers doivent recevoir le tenant context dans chaque job :

```python
{
  "job_id": "...",
  "context": {
      "startup_id": "stp_001",
      "org_id": "org_517",
      "product_id": "sparkmetriq",
      "user_id": null
  }
}
```

### Interdit :

```python
worker.execute(job_id)  # sans contexte → interdit
```

---

# 10. Isolation des secrets (aligné DOC-019)

Les secrets sont stockés par niveau tenant :

```
/tenants/{startup_id}/{org_id}/{product_id}/secrets/*
```

Workers, API et Scheduler ne peuvent récupérer que :

* les secrets correspondant au tenant du contexte,
* jamais les secrets d’une autre organisation/startup,
* jamais les secrets d’un autre produit.

---

# 11. Isolation des logs

Chaque log doit inclure automatiquement :

* `startup_id`
* `org_id`
* `product_id`
* `user_id` (si applicable)

Exemple :

```json
{
  "event": "post.scheduled",
  "startup_id": "stp_2",
  "org_id": "org_77",
  "product_id": "sparkmetriq",
  "user_id": "usr_221",
  "payload": {...}
}
```

Interdictions :

* ❌ logs sans metadata tenant
* ❌ logs transversaux produits

---

# 12. Isolation des métriques (SRE)

Prometheus doit toujours inclure un label tenant :

```
scheduler_latency_seconds_total{org_id="xxx", product_id="sparkmetriq"}
```

Mêmes règles pour :

* worker_latency
* error_rate
* retry_rate
* quota_usage

---

# 13. Isolation des erreurs & exceptions

Toute exception doit inclure le contexte tenant pour audit et debug :

```
raise TenantBoundError("Quota exceeded", context=context)
```

---

# 14. Multi-Produit : usage concurrent

Un utilisateur peut appartenir à plusieurs produits.
Les permissions sont isolées par produit (DOC-SC-005).

---

# 15. Isolation réseau / API Gateway

Le Gateway doit :

* limiter les requêtes par org,
* interdire le changement de tenant dans le payload,
* refuser toute incohérence entre JWT et paramètres.

Aligné sur DOC-018.

---

# 16. CI/CD Compliance Rules

### 🚫 Bloquant :

* modèle sans `org_id/startup_id/product_id`
* route FastAPI sans extraction tenant
* secret cross-tenant
* worker sans contexte tenant
* absence de logs tenant metadata
* DB query non filtrée par tenant

### ⚠ Warning :

* metrics sans labels tenant
* tests tenant incomplets

---

# 17. Invariants non négociables

1. Aucun document n’est stocké sans triple identifiant.
2. Aucun service ne s’exécute sans TenantContext.
3. Aucun produit ne peut accéder aux données d’un autre.
4. Les secrets sont toujours par tenant et jamais globaux.
5. Les logs, métriques et erreurs doivent inclure tenant metadata.
6. Le Gateway valide le tenant avant toute action API.
7. Toute PR violant DOC-SC-004 est bloquée.

---

# 18. Conclusion

DOC-SC-004 établit la **fondation multi-tenant et multi-startup** incontournable pour l’écosystème SaasentialCore.
Il garantit :

* sécurité,
* isolation stricte,
* scalabilité,
* compatibilité multi-produits,
* alignement parfait avec Sparkmetriq & Sparkpusher,
* conformité SRE++.

Aucun service ne peut fonctionner correctement sans respecter ce contrat.

```
# DOC-SC-004_core_multi_tenant_data_isolation_contract.md
