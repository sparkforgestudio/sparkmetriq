Voici **DOC-SC-018 — S2 API Gateway & Rate Limiting Contract**,
version **longue**, normative, orientée **production hyperscale**, alignée SRE++, sécurité, multi-tenant strict, et cohérente avec **SC-001 → SC-017**.

Ce document fixe **le contrat frontal de Sparkmetriq S2** :
comment les requêtes entrent, sont filtrées, limitées, tracées, sécurisées et protégées avant d’atteindre l’API cœur.

À placer dans :

```
docs/saasentialcore/architecture/DOC-SC-018_s2_api_gateway_rate_limiting_contract.md
```

---

# 📘 `DOC-SC-018_s2_api_gateway_rate_limiting_contract.md`

```markdown
---
title: DOC-SC-018 — S2 API Gateway & Rate Limiting Contract
version: 1.0
status: Stable
category: SaasentialCore / Sparkmetriq S2 / API Gateway / Security / SRE
last_updated: 2025-02-18
---

# 1. Objectif du document

DOC-SC-018 définit le **contrat officiel de l’API Gateway S2**, incluant :

- la frontière d’entrée unique vers l’API,
- l’authentification et l’autorisation initiales,
- le rate limiting multi-niveaux,
- la protection contre abus et attaques,
- la propagation du contexte (tenant, trace),
- l’intégration observabilité et sécurité,
- la compatibilité multi-startup et multi-produit.

L’API Gateway est une **barrière non négociable** :  
aucun trafic S2 ne peut contourner ce contrat.

---

# 2. Principes fondamentaux

## ✔ 2.1. Single Entry Point  
Toute requête S2 passe par l’API Gateway.

## ✔ 2.2. Zero Trust Front Door  
Aucune requête n’est considérée fiable avant validation complète.

## ✔ 2.3. Multi-Tenant First-Class  
Le rate limiting, la sécurité et la visibilité sont **tenant-aware**.

## ✔ 2.4. Fail Fast, Fail Safe  
Une requête invalide est rejetée **le plus tôt possible**.

---

# 3. Positionnement architectural

```

Client
↓
API Gateway
↓
Auth / Rate Limit / Validation
↓
FastAPI Core (Routes)
↓
Bridge / Services

````

L’API Gateway peut être implémentée via :
- Caddy / Nginx / Envoy (L7),
- ou un composant FastAPI dédié en frontal.

---

# 4. Responsabilités de l’API Gateway

L’API Gateway est responsable de :

- TLS termination
- JWT validation (DOC-SC-005)
- extraction du TenantContext
- rate limiting
- request size limiting
- schema pre-validation
- propagation trace_id
- rejection des patterns malveillants
- logging d’accès structuré

Elle **n’est pas responsable** :
- de logique métier,
- de gestion des quotas,
- de retries applicatifs,
- de scheduling.

---

# 5. Authentification & Contexte

## 5.1. JWT obligatoire

Chaque requête doit contenir un JWT valide :

- signé
- non expiré
- avec claims :
  - startup_id
  - org_id
  - product_id
  - roles
  - scopes

Requête sans JWT → **401 immédiat**.

---

## 5.2. Construction du TenantContext

L’API Gateway construit :

```json
{
  "startup_id": "...",
  "org_id": "...",
  "product_id": "...",
  "user_id": "...",
  "roles": [...],
  "trace_id": "..."
}
````

Ce contexte est injecté downstream (DOC-SC-003).

---

# 6. Rate Limiting — Vue globale

Le rate limiting est **hiérarchique** et cumulatif.

Niveaux :

1. IP / Client
2. User
3. Organisation
4. Produit
5. Route / Action

Chaque niveau peut bloquer indépendamment.

---

# 7. Rate Limiting par niveau

## 7.1. IP / Client

Protection anti-abus basique :

* ex: 100 req/min/IP
* burst limité
* protection bots

Dépassement → **429**.

---

## 7.2. User-level

Limitation par utilisateur authentifié :

* ex: 60 req/min/user
* sliding window

Utilisé pour :

* UI abusive
* scripts non maîtrisés

---

## 7.3. Organisation-level (critique)

Limite globale par organisation :

* ex: 600 req/min/org
* configurable selon plan

Empêche :

* saturation S2
* déni de service interne

---

## 7.4. Product-level

Chaque produit peut définir :

* ses propres seuils
* ses propres priorités

Ex :

* Sparkmetriq S2 scheduling ≠ Sparkpusher inbox

---

## 7.5. Route / Action-level

Certaines routes sont **sensibles** :

* `/schedule`
* `/publish_now`
* `/bulk_schedule`

Exemple :

```
POST /s2/schedule → 10/min/org
```

---

# 8. Quotas vs Rate Limiting (clarification)

| Concept          | Rôle                   |
| ---------------- | ---------------------- |
| Rate limiting    | protection infra & API |
| Quotas (DOC-004) | règle business         |

Une requête peut :

* passer le rate limit
* mais être rejetée par quota (402/409)

---

# 9. Request Size & Payload Protection

Limites obligatoires :

* taille JSON max (ex: 1MB)
* nombre de médias max
* profondeur JSON max

Payload trop gros → **413 Payload Too Large**.

---

# 10. Schema Pre-Validation

L’API Gateway peut effectuer une **pré-validation légère** :

* JSON valide
* champs obligatoires présents
* payload_version présent

La validation complète reste côté API (DOC-SC-014).

---

# 11. Abuse & Attack Protection

### Protections obligatoires :

* rate limit agressif sur 401/403
* blacklist IP temporaires
* détection burst anormaux
* interdiction path traversal
* interdiction user-agent suspects

---

# 12. Error Handling Standard

Réponses standardisées :

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "retry_after": 30,
    "trace_id": "..."
  }
}
```

Jamais :

* stack trace
* détails internes
* info tenant sensible

---

# 13. Observabilité Gateway (DOC-SC-009)

## Logs obligatoires

```json
{
  "event": "api.request",
  "method": "POST",
  "path": "/s2/schedule",
  "status": 429,
  "startup_id": "...",
  "org_id": "...",
  "product_id": "...",
  "trace_id": "...",
  "latency_ms": 12
}
```

## Metrics obligatoires

* `api_requests_total`
* `api_requests_blocked_total`
* `api_rate_limit_exceeded_total`
* `api_latency_seconds`
* `api_payload_too_large_total`

---

# 14. Failover & Degraded Modes

En cas de surcharge :

* rejet précoce (fail fast)
* priorité routes critiques
* dégradation UI analytics
* maintien scheduling critique

---

# 15. CI/CD Compliance Rules

### 🚫 Bloquant

* route exposée hors Gateway
* absence rate limit
* absence JWT validation
* absence tenant extraction
* absence trace propagation
* réponse non standardisée

### ⚠ Warning

* seuils non documentés
* absence tests rate limit
* absence dashboards gateway

---

# 16. Invariants non négociables

1. Aucune requête S2 ne contourne l’API Gateway.
2. Toute requête est authentifiée.
3. Toute requête est limitée.
4. Toute requête est tracée.
5. Toute violation est bloquée.
6. Toute PR violant DOC-SC-018 est refusée.

---

# 17. Conclusion

DOC-SC-018 érige l’API Gateway en **mur de protection intelligent** de Sparkmetriq S2 :

* sécurité renforcée,
* stabilité sous charge,
* isolation multi-tenant,
* prévention des abus,
* observabilité complète,
* compatibilité hyperscale.

C’est la première ligne de défense du système

