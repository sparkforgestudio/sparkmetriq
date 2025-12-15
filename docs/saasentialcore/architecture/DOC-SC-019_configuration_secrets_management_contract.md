Voici **DOC-SC-019 — Configuration & Secrets Management Contract (env, vault, multi-tenant keys)**,
version **longue**, normative, exhaustive, et **structurante pour tout le socle SaasentialCore**, parfaitement alignée avec **SC-001 → SC-018**, SRE++, Zero-Trust et multi-startup hyperscale.

> ⚠️ Ce document est **l’un des plus sensibles de toute la série** : il conditionne la sécurité, la fiabilité, l’isolation inter-agences et la capacité de Sparkmetriq / Sparkpusher à scaler sans dette critique.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-019_configuration_secrets_management_contract.md
```

---

# 📘 `DOC-SC-019_configuration_secrets_management_contract.md`

```markdown
---
title: DOC-SC-019 — Configuration & Secrets Management Contract
version: 1.0
status: Stable
category: SaasentialCore / Security / Configuration / Secrets / Zero-Trust
last_updated: 2025-02-18
---

# 1. Objectif du document

DOC-SC-019 définit le **contrat officiel et non négociable** de gestion :

- des configurations runtime,
- des variables d’environnement,
- des secrets applicatifs,
- des clés cryptographiques,
- des tokens API externes (Instagram, TikTok, Threads, etc.),
- des secrets multi-tenant,
- des secrets multi-startup,
- des secrets multi-produits.

Il garantit :
- **aucun secret dans le code**,
- **aucun secret dans Git**,
- **aucun secret dans les logs**,
- **aucun secret hors DI**,
- **isolation stricte par startup / org / produit**,
- **rotation, audit et traçabilité**.

---

# 2. Principes fondamentaux (Non négociables)

## ✔ 2.1. Zero-Trust Configuration
Aucune donnée de configuration n’est considérée fiable par défaut.

## ✔ 2.2. Séparation stricte Config vs Secrets

| Type | Définition |
|-----|------------|
| Configuration | Paramètres non sensibles |
| Secrets | Toute donnée compromettante |

Un secret **n’est jamais** une config.

---

## ✔ 2.3. Single Source of Truth

- Config → Settings Pydantic
- Secrets → Vault / Secret Store
- Overrides locaux → DEV uniquement

Aucune duplication.

---

## ✔ 2.4. Injection obligatoire (DI)

Tout accès à la configuration ou aux secrets passe par :
- le **container DI** (DOC-SC-003),
- le **Bridge Core**.

Accès direct = **violation critique**.

---

# 3. Typologie officielle des données

## 3.1. Configuration (non sensible)

Exemples :
- ENV (`dev`, `staging`, `prod`)
- ports
- feature flags
- timeouts
- worker pool size
- backoff defaults

Stockage :
- `.env`
- variables système
- fichiers settings versionnés

---

## 3.2. Secrets (sensibles)

Exemples :
- MongoDB credentials
- RabbitMQ credentials
- JWT private keys
- OAuth client secrets
- Tokens Instagram / TikTok / Threads
- API keys LLM
- Webhook secrets

Stockage :
- **Vault obligatoire**
- jamais dans `.env` en prod

---

# 4. Architecture cible de gestion des secrets

```

Vault
└── startups/
└── <startup_id>/
└── orgs/
└── <org_id>/
└── products/
└── <product_id>/
├── db/
│   └── credentials
├── connectors/
│   ├── instagram
│   ├── tiktok
│   └── threads
├── jwt/
│   ├── private_key
│   └── public_key
└── webhooks/

```

### Invariants :
- un produit ne lit **que** son namespace,
- une org ne lit **que** ses secrets,
- aucune lecture cross-startup.

---

# 5. Settings applicatifs (Pydantic)

Tous les settings Core doivent être définis dans :

```

saasentialcore/config/settings.py

````

Exemple :

```python
class CoreSettings(BaseSettings):
    environment: Literal["dev", "staging", "prod"]
    api_host: str
    api_port: int

    mongo_uri: SecretStr
    rabbitmq_uri: SecretStr

    vault_url: str
    vault_token: SecretStr

    telemetry_enabled: bool = True
````

### Règles :

* `SecretStr` obligatoire pour tout sensible
* aucun default pour secret
* validation au démarrage

---

# 6. Provider Secrets (DI obligatoire)

Accès autorisé uniquement via :

```python
secret_provider = container.get(SecretProvider)

token = secret_provider.get(
    startup_id,
    org_id,
    product_id,
    "connectors.instagram.access_token"
)
```

### Interdictions absolues :

```python
os.getenv("INSTAGRAM_TOKEN")   # ❌
settings.INSTAGRAM_TOKEN      # ❌
```

---

# 7. Gestion des secrets multi-tenant

## 7.1. Secrets par organisation

Chaque organisation possède :

* ses propres tokens sociaux,
* ses propres clés API,
* ses propres quotas indirects.

Aucun partage par défaut.

---

## 7.2. Secrets par produit

Sparkmetriq et Sparkpusher **ne partagent jamais** leurs secrets, même pour une même org.

---

# 8. Secrets & Scheduler / Workers

## Règles strictes

* le Scheduler **ne stocke jamais** de secrets
* les Workers :

  * chargent les secrets **juste avant exécution**
  * les détruisent en `CLEANUP` (DOC-SC-015)

Jamais :

* secret dans payload
* secret dans job metadata
* secret sérialisé

---

# 9. Rotation des secrets

## 9.1. Rotation obligatoire

| Type            | Fréquence        |
| --------------- | ---------------- |
| JWT keys        | 90 jours         |
| OAuth tokens    | selon plateforme |
| DB credentials  | 180 jours        |
| Webhook secrets | 90 jours         |

---

## 9.2. Rotation sans downtime

* support multi-key active
* `kid` header JWT
* grace period contrôlée

---

# 10. Secrets & Observabilité

## Interdictions absolues

* secret dans logs
* secret dans metrics
* secret dans traces
* secret dans events

Violation = **incident sécurité critique**.

---

## Logging autorisé

```json
{
  "event": "secret.access",
  "startup_id": "...",
  "org_id": "...",
  "product_id": "...",
  "secret_path": "connectors.instagram",
  "trace_id": "..."
}
```

Jamais la valeur.

---

# 11. Environnements

## DEV

* `.env.local` autorisé
* secrets mockés
* jamais commités

## STAGING

* Vault obligatoire
* secrets proches prod

## PROD

* Vault obligatoire
* aucun fallback
* démarrage échoue si secret manquant

---

# 12. CI/CD Compliance Rules

### 🚫 Bloquant

* secret dans Git
* secret hardcodé
* accès secret hors DI
* secret dans logs
* secret dans payload
* absence de rotation
* absence audit secret access
* fallback prod

### ⚠ Warning

* absence de tests rotation
* absence namespace produit
* absence documentation secrets requis

---

# 13. Tests obligatoires

* test démarrage sans secret → FAIL
* test isolation tenant
* test rotation JWT
* test accès secret invalide
* test suppression secrets en cleanup worker

---

# 14. Invariants non négociables

1. Aucun secret n’est versionné.
2. Aucun secret n’est partagé cross-tenant.
3. Aucun secret n’est accessible hors DI.
4. Aucun secret n’est loggué.
5. Tout secret est rotatable.
6. Toute PR violant DOC-SC-019 est refusée.

---

# 15. Conclusion

DOC-SC-019 est **le contrat de sécurité configurationnelle** du socle SaasentialCore.

Il permet :

* multi-startup sécurisé,
* multi-produit isolé,
* exploitation industrielle,
* conformité SRE++,
* évolutivité sans dette.

Sans ce contrat, Sparkmetriq ne peut pas passer à l’échelle production sérieuse.
