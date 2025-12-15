Voici **DOC-SC-005 — Identity & AuthN/AuthZ Core Contract**, version longue, sans fautes, parfaitement alignée avec SaasentialCore, Sparkmetriq, Sparkpusher, le multi-startup (DOC-SC-001), le multi-produit (DOC-SC-002), la DI (DOC-SC-003), et l’isolation tenant (DOC-SC-004).

C’est l’un des documents **les plus critiques** du socle, car l’identité & l’autorisation gouvernent *tous* les accès API, worker, scheduler, dispatcher, admin panel, logs, secrets, etc.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-005_identity_authn_authz_core_contract.md
```

---

# 📘 `DOC-SC-005_identity_authn_authz_core_contract.md`

```markdown
---
title: DOC-SC-005 — Identity & AuthN/AuthZ Core Contract
version: 1.0
status: Stable
category: SaasentialCore / Identity / AuthN/AuthZ / Multi-Startup
last_updated: 2025-02-14
---

# 1. Objectif du document

DOC-SC-005 définit le **contrat central d’identité, d’authentification et d’autorisation** dans SaasentialCore, garantissant :

- un modèle global d’identités,
- la gestion multi-startup / multi-organisation,
- le contrôle d’accès strict aux produits,
- l’intégration propre dans l’API Gateway (DOC-018),
- le passage du TenantContext dans tous les services (DOC-SC-004),
- la compatibilité avec workers, scheduler, dispatcher,
- les règles JWT globales,
- la sécurité des tokens & sessions.

Ce document est obligatoire pour tout produit enregistré (DOC-SC-002).

---

# 2. Modèle d’identité global (Identity Model)

SaasentialCore doit gérer un modèle d'identité en **quatre niveaux** :

```

Startup  → Organisation  → Utilisateur  → Rôles & Permissions

````

## 2.1. Entités obligatoires

### Startup
Représente une entité indépendante dans la plateforme SaaS (ex : Musai, SparkForge).

### Organisation
Représente un client ou une agence d’une startup.

### User
Compte individuel, pouvant appartenir :

- à une ou plusieurs organisations,
- à une ou plusieurs startups,
- à un ou plusieurs produits.

### Roles & Permissions
Déterminent les droits au niveau :

- Core global,
- Startup,
- Organisation,
- Produit.

---

# 3. Identifiants obligatoires

Chaque identité doit posséder :

| Niveau        | ID            | Format |
|---------------|---------------|--------|
| Startup       | `startup_id`  | UUID   |
| Organisation  | `org_id`      | UUID   |
| User          | `user_id`     | UUID   |
| Product       | `product_id`  | slug   |

Ces identifiants sont inclus dans :

- JWT,  
- TenantContext,  
- logs,  
- métriques,  
- messages workers.

---

# 4. Authentification (AuthN)

L’authentification repose sur des **JWT signés par SaasentialCore**, jamais par un produit.

## 4.1. Types de tokens

### A. Access Token (JWT)
- durée courte (15–30 min)
- utilisé pour la majorité des requêtes API

### B. Refresh Token
- durée longue (7–30 jours)
- stocké côté frontend uniquement en HTTP-only cookie

### C. Service Token (Worker/Scheduler)
- non utilisable côté frontend
- scellé avec claims restrictifs

---

# 5. Structure officielle du JWT (Core)

Exemple de payload :

```json
{
  "sub": "user_123",
  "startup_id": "stp_001",
  "org_id": "org_517",
  "permissions": ["sparkmetriq.s2.schedule", "sparkmetriq.s2.analytics.read"],
  "products": ["sparkmetriq"],
  "iat": 1718241200,
  "exp": 1718243000
}
````

Claims obligatoires :

* `sub` (identité)
* `startup_id`
* `org_id`
* `permissions`
* `products`
* `iat`, `exp`

Claims interdits :

* secrets,
* tokens platformes sociales (aligné DOC-019),
* informations sensibles non nécessaires.

---

# 6. Extraction & vérification des JWT (API Layer)

L’API doit :

1. vérifier la signature JWT via SaasentialCore,
2. vérifier expiration,
3. vérifier que le produit ciblé correspond à `product_id` dans le token,
4. vérifier que `startup_id` & `org_id` sont cohérents,
5. construire le TenantContext (DOC-SC-004),
6. attacher les rôles & permissions.

Exemple :

```python
def authenticate(token: str) -> TenantContext:
    payload = verify_jwt(token)
    return TenantContext(
        startup_id=payload["startup_id"],
        org_id=payload["org_id"],
        user_id=payload["sub"],
        product_id=extract_product_from_route(),
        permissions=payload["permissions"],
    )
```

---

# 7. Autorisation (AuthZ)

## 7.1. Modèle RBAC étagé (4 niveaux)

| Niveau       | Exemple                   | Description                           |
| ------------ | ------------------------- | ------------------------------------- |
| Core         | `core.admin`              | droits globaux, gestion startups      |
| Startup      | `startup.owner`           | gestion des organisations             |
| Organisation | `org.manager`             | gestion des utilisateurs org          |
| Produit      | `sparkmetriq.s2.schedule` | droits sur une fonctionnalité produit |

## 7.2. Une permission doit être **explicite** et **scopée**

Exemples :

```
sparkmetriq.s2.schedule
sparkmetriq.s2.analytics.read
sparkpusher.inbox.read
sparkpusher.dm.send
```

## 7.3. Aucun accès n’est autorisé par défaut

La philosophie est : **Zero Trust by Construction**.

---

# 8. AuthZ dans les routes FastAPI

Chaque route doit déclarer explicitement la permission :

```python
@router.post("/schedule")
def schedule(
    payload: UnifiedPostPayload,
    context: TenantContext = Depends(authenticate),
):
    require_permission(context, "sparkmetriq.s2.schedule")
    ...
```

Interdit :

```python
# ❌ Pas de logique métier sans check de permission
```

---

# 9. AuthZ dans les Workers & Scheduler

Les workers reçoivent un TenantContext partiel :

```json
{
  "startup_id": "stp_1",
  "org_id": "org_77",
  "product_id": "sparkmetriq",
  "user_id": null
}
```

Règles :

* les workers n’ont pas besoin de permissions utilisateur,
* mais ils doivent respecter l’isolation tenant,
* un worker ne doit jamais accéder à un autre tenant.

---

# 10. Rôles globaux

SaasentialCore doit définir un set minimal de rôles globaux :

| Rôle            | Description                                |
| --------------- | ------------------------------------------ |
| `core.admin`    | contrôle total systeme                     |
| `startup.owner` | contrôle d’une startup                     |
| `org.admin`     | gestion des utilisateurs de l’organisation |
| `product.admin` | gestion spécifique au produit              |

Les produits peuvent ajouter leurs propres rôles, sous leur namespace, ex :

```
sparkmetriq.admin
sparkmetriq.editor
sparkmetriq.viewer
```

---

# 11. Multi-Produit : compatibilité

Un utilisateur peut avoir :

* accès à plusieurs produits,
* mais accès **distinct** dans chaque produit.

Aucun produit ne peut :

* lire les permissions d’un autre produit,
* modifier les permissions d’un autre produit.

---

# 12. Sessions & sécurité

### 12.1. Refresh Token

* stocké uniquement en HTTP-only cookie
* jamais dans localStorage

### 12.2. Rotation des clés JWT

Aligné DOC-019 :

* rotation tous les 90 jours,
* support des clés multiples (`kid` header).

### 12.3. Secret Exposure Protection

Interdictions :

* logs contenant un JWT complet,
* passer un token en paramètre URL,
* exposer un secret produit dans un JWT.

---

# 13. Intégration avec API Gateway (DOC-018)

Le Gateway doit :

* extraire token,
* vérifier JWT,
* rejeter requête si :

  * permission manquante,
  * produit non inclus dans token,
  * tenant mismatch,
* nettoyer headers,
* transmettre un `X-Tenant-ID` interne sécurisé.

---

# 14. Intégration avec Observability (DOC-SC-009)

Chaque requête doit logger :

```json
{
  "event": "auth.success",
  "startup_id": "stp_1",
  "org_id": "org_77",
  "user_id": "usr_12",
  "product_id": "sparkmetriq",
  "permissions": ["sparkmetriq.s2.schedule"]
}
```

Les métriques Prometheus doivent inclure :

```
auth_success_total
auth_failure_total
auth_permission_denied_total
```

---

# 15. CI/CD Compliance Rules

### 🚫 Bloquant :

* route sans permission explicite,
* bypass du Gateway pour AuthN/AuthZ,
* absence de `startup_id/org_id/product_id` dans JWT,
* worker exécutant une action sans TenantContext,
* permission cross-produits non autorisée,
* storage ou logs contenant un JWT,
* token signé par un produit au lieu du Core.

### ⚠ Warning :

* rôle produit non documenté,
* absence de tests permission denied,
* manque de labels tenant dans metrics auth.

---

# 16. Invariants non négociables

1. Un utilisateur = identité globale, rôles par startup, permissions par produit.
2. JWT = signé uniquement par SaasentialCore.
3. Aucun accès n’est accordé sans permission explicite.
4. TenantContext est obligatoire dans chaque service.
5. Logs & métriques incluent toujours les identifiants tenant.
6. Workers respectent les mêmes règles d’isolement que l’API.
7. Toute PR violant DOC-SC-005 est bloquée.

---

# 17. Conclusion

DOC-SC-005 définit l’ossature identitaire du monorepo.
Il garantit :

* hydratation cohérente du TenantContext,
* isolation stricte multi-startup / multi-produit,
* sécurité de niveau industriel,
* compatibilité avec tous les modules,
* conformité avec SRE++, DI, Observability et CI/CD.

Aucun produit ne peut fonctionner correctement sans respecter ce contrat.

```
# DOC-SC-005_identity_authn_authz_core_contract.md
