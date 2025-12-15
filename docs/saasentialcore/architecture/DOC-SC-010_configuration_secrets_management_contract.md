Voici **DOC-SC-010 — Configuration & Secrets Management Contract**, version longue, exhaustive, alignée avec les exigences SRE++, zero-trust, multi-startup, multi-produit, multi-tenant, et cohérente avec les documents précédents (SC-001 → SC-009).

Ce document est **critique** car il définit la manière dont SaasentialCore — et toutes les startups/produits — manipulent, stockent, chargent, isolent et sécurisent les secrets, configurations d’exécution, clés, tokens API (ex : Instagram, TikTok, Threads), JWT keys, credentials Mongo/RabbitMQ, etc.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-010_configuration_secrets_management_contract.md
```

---

# 📘 `DOC-SC-010_configuration_secrets_management_contract.md`

```markdown
---
title: DOC-SC-010 — Configuration & Secrets Management Contract
version: 1.0
status: Stable
category: SaasentialCore / Configuration / Secrets / Security / Zero-Trust
last_updated: 2025-02-15
---

# 1. Objectif du document

DOC-SC-010 définit le **cadre contractuel officiel** de gestion :

- des configurations runtime,
- des secrets tenants,
- des environnements multi-startup,
- du chargement DI (DOC-SC-003),
- de la sécurité (aligné DOC-SC-005),
- des connecteurs externes (ex: Instagram/TikTok),
- des clés JWT,
- des tokens OAuth externes,
- et de l’architecture globale zero-trust.

Il garantit que chaque produit (Sparkmetriq, Sparkpusher, futurs produits) consomme config & secrets de manière **sécurisée, isolée, traçable et prévisible**.

---

# 2. Principes fondamentaux

## ✔ 2.1. Aucun secret dans le code  
Interdiction absolue :

- pas de clé API hardcodée  
- pas de token dans un fichier Python  
- pas de config sensible dans `product_manifest.json`

## ✔ 2.2. Tout secret doit être chargé via provider DI  
Aligné avec DOC-SC-003.

## ✔ 2.3. Stockage centralisé et isolé par tenant  
Aligné DOC-SC-004.

## ✔ 2.4. Séparation *config publique* vs *config sensible*

- settings publics → `Settings()` Pydantic  
- secrets → Vault / Secret Store  
- override dans env variables autorisé uniquement pour développement

## ✔ 2.5. Auditabilité  
Chaque accès secret doit être journalisé.

---

# 3. Typologie des configurations

| Type | Exemple | Source |
|------|---------|--------|
| Static config | DEBUG, product feature flags | settings (env) |
| Sensitive config | API keys, DB passwords | Vault / KMS |
| Tenant secrets | Instagram token d’une agence | Tenant Secret Store |
| Operational config | worker pool size, backoff | settings (env) |
| Cryptographic keys | JWT private keys | Vault / HSM |

---

# 4. Structure officielle des Settings

Les settings Core doivent être dans :

```

saasentialcore/config/settings.py

````

Exemple :

```python
class Settings(BaseSettings):
    environment: str = "development"  # dev/staging/prod
    mongo_url: SecretStr
    rabbitmq_url: SecretStr
    vault_url: str
    jwt_public_key: str
    jwt_private_key: SecretStr
    telemetry_enabled: bool = True
````

### Obligations :

* chaque champ sensible doit être un `SecretStr`
* settings ne doivent jamais contenir de defaults sensibles

---

# 5. Secret Storage Architecture

```
Vault /
    startups/
        <startup_id>/
            orgs/
                <org_id>/
                    products/
                        <product_id>/
                            secrets/
                                instagram_access_token
                                tiktok_refresh_token
                                twitter_bearer_token
                                openai_api_key
                                ...
```

### Règles :

* un produit ne peut lire que ses secrets
* un tenant ne peut lire que son espace
* interdire cross-startup

---

# 6. Providers secrets (DI)

SaasentialCore doit fournir :

```python
container.register("vault", lambda: VaultClient(settings.vault_url))
container.register("secret_provider", lambda: TenantSecretProvider(vault))
```

Un produit doit **toujours** utiliser :

```python
secret = secret_provider.get(context, "instagram_access_token")
```

Jamais :

```python
secret = os.getenv("INSTAGRAM_TOKEN")   # interdit
```

---

# 7. Rotation des clés et tokens

## 7.1. JWT keys

* rotation tous les 90 jours
* support des clés multiples via `kid` header
* versionnée dans Vault

## 7.2. API tokens externes (Instagram, TikTok)

* rotation automatique via refresh
* stockage unique dans tenant secret store
* jamais loggés en clair
* jamais envoyés vers workers sans cryptage

---

# 8. Secrets dans le runtime

## Interdit :

* stocker un secret dans un événement (DOC-SC-006)
* stocker un secret dans une métrique (DOC-SC-009)
* stocker un secret dans un log (DOC-SC-009)
* envoyer secret dans un worker job payload

## Obligatoire :

* secrets transitent uniquement dans les services concernés
* jamais sérialisés dans les API réponses
* jamais retournés dans Pydantic models

---

# 9. Configuration multi-environnements

Arborescence :

```
env/
    dev.env
    staging.env
    prod.env
```

### Règles :

* **prod** doit ignorer tous les defaults dev
* staging & prod doivent obligatoirement charger leurs secrets depuis Vault
* dev peut utiliser `.env.local` mais pas les produits

---

# 10. Configuration des produits

Les produits doivent déclarer **seulement** les settings non sensibles dans :

```
products/<id>/config/settings.py
```

Et déclarer les secrets souhaités dans leur manifest :

```json
{
  "required_secrets": [
    "instagram_access_token",
    "tiktok_refresh_token",
    "twitter_bearer_token"
  ]
}
```

SaasentialCore valide à l’exécution que :

* tous les secrets nécessaires sont présents
* tenant isolé
* clé valide

---

# 11. Secrets côté Workers & Scheduler

Le Scheduler et les Workers ne lisent **jamais** directement des env vars.
Ils utilisent :

```python
secret = secret_provider.get(context, "instagram_access_token")
```

---

# 12. Audit & Logging (aligné DOC-SC-009)

Chaque accès secret génère un log structuré :

```json
{
  "event": "secret.access",
  "startup_id": "...",
  "org_id": "...",
  "product_id": "...",
  "secret_name": "instagram_access_token",
  "accessor": "scheduler",
  "timestamp": "..."
}
```

### Interdit :

* logging du secret lui-même

---

# 13. CI/CD Compliance Rules

### 🚫 Bloquant

* fichier contenant un secret hardcodé
* secret dans un manifest produit
* secret dans un test
* secret dans un log
* secret dans un événement
* product override direct sans passer par DI
* accès Vault sans tenant context
* produit utilisant un secret d’un autre produit

### ⚠ Warning

* absence de tests secrets
* absence de rotation pour env prod
* absence de namespacing produit

---

# 14. Tests obligatoires

### Unitaires

* secret provider fonctionne
* tenant isolation

### Intégration

* Vault ↔ Providers
* produit ↔ tenant isolation

### E2E

* scheduling S2 utilisant des tokens externes
* refresh token flux (TikTok/Instagram)

---

# 15. Invariants non négociables

1. Aucun secret ne doit jamais apparaître en clair dans code, logs, events, metrics.
2. Toute lecture de secret doit être contextualisée (tenant + produit).
3. Toute configuration sensible doit être chargée via DI.
4. Les produits ne peuvent accéder qu’aux secrets déclarés.
5. Toute PR violant DOC-SC-010 est bloquée.

---

# 16. Conclusion

DOC-SC-010 fixe le **contrat de sécurité et configuration** essentiel du socle SaasentialCore :

* Zero trust architecture
* Isolation tenant stricte
* Gestion des secrets multi-produit
* Sécurité cryptographique durable
* Gouvernance CI/CD
* Conformité avec DOC-SC-001 à DOC-SC-009

Ce document est obligatoire pour toutes les contributions présentes et futures.

```

### 👉 **DOC-SC-011 — Admin Panel Contract (permissions UI, boundaries API, roles)**
