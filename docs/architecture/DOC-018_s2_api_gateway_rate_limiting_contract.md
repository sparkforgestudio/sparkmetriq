Voici **DOC-018 — S2 API Gateway & Rate Limiting Contract**, version longue (12–18 pages), conçu pour définir **l’architecture de l’API Gateway Sparkmetriq**, les règles de rate limiting, les protections anti-abus, la gestion du trafic multi-tenant, les contraintes SRE++, les garde-fous de sécurité (DOC-008) et les limites pratiques pour garantir la fiabilité et la scalabilité de S2.

Ce document complète :

* DOC-003 (API Contract),
* DOC-009 (Multi-Tenant),
* DOC-012 (Connectors),
* DOC-013 (Scheduler),
* DOC-017 (Failure Modes).

À intégrer dans :

```
docs/architecture/DOC-018_s2_api_gateway_rate_limiting_contract.md
```

---

# 📘 **DOC-018 — S2 API Gateway & Rate Limiting Contract**

*Sparkmetriq S2 — API Boundary / Security / Throttling / Traffic Shaping / Multi-Tenant Controls*

```markdown
---
title: DOC-018 — S2 API Gateway & Rate Limiting Contract
version: 1.0
status: Stable
category: Architecture / API / Security / Rate Limits / Gateway
last_updated: 2025-02-10
---
```

---

# # **1. Objectif du document**

Sparkmetriq S2 traite des flux API critiques :

* scheduling de masse,
* uploads média,
* configuration de comptes sociaux,
* monitoring & logs,
* interactions Admin Panel,
* flux connecteurs indirects.

Il est vital de garantir :

* stabilité face à la charge,
* protection DoS / misuse,
* rate limiting multi-tenant équitable,
* isolation stricte entre organisations (DOC-009),
* sécurité renforcée (DOC-008),
* disponibilité continue (DOC-017),
* intégration propre avec le scheduler/dispatcher.

Ce document spécifie les **règles officielles** de l'API Gateway S2 et des limites.

---

# # **2. Périmètre**

Ce document couvre :

* l’API Gateway (Caddy ou API internal Gateway)
* rate limiting global & par tenant
* throttling par endpoint
* anti-abuse & anti-spam
* circuit breaker
* burst management
* limites liées à S2 Scheduler
* quotas API internes
* backpressure API

Hors périmètre :

* connecteurs externes (DOC-012),
* Worker execution (DOC-015).

---

# # **3. Architecture API Gateway**

### Composants

```mermaid
flowchart LR
Client --> G[API Gateway]
G --> A[Auth Service]
G --> RL[Rate Limiter (per-tenant)]
G --> API[FastAPI Core]
API --> S2[Scheduler/Dispatcher]
```

### Rôles du Gateway :

* authentification précoce
* extraction org_id
* rate limiting intelligent
* quota API
* normalisation des logs
* rejet anticipé des requêtes invalides
* protection anti-DoS
* circuit breaker

---

# # **4. Obligations fondamentales**

## ✔ 4.1. Rate limiting **par organisation**, jamais par IP

L’usage multi-agents nécessite une gestion correcte des API depuis :

* Admin Panel
* bots internes
* comptes opérateurs

Limiter par IP est non fonctionnel → on limite **par org_id**.

---

## ✔ 4.2. Rate limiting différent selon la criticité du point d’accès

| Endpoint             | Protection                 |
| -------------------- | -------------------------- |
| `/s2/posts/schedule` | strict (par tenant)        |
| `/api/media/upload`  | strict (poids)             |
| `/auth/login`        | anti-bruteforce            |
| `/s2/analytics/*`    | dédié (lecture intensive)  |
| `/connectors/*`      | verrouillages multi-tenant |

---

## ✔ 4.3. Gateway doit rejeter toute requête non authentifiée

Avant même d’appeler FastAPI :

* token invalide → 401
* token expiré → 401
* org_id absent ou incohérent → 403

---

## ✔ 4.4. Aucun rate limit n’est défini côté FastAPI

Toute la logique rate-limit est **hors** API app.

---

## ✔ 4.5. Rate limiting doit être **élastique**

Tenir compte :

* de la taille de l’agence
* du plan tarifaire
* du volume historique
* de l’urgence (immediate publish)

---

# # **5. Modèle de Rate Limiting (Hybrid Token Bucket)**

L’API Gateway doit implémenter un **hybrid token bucket** avec :

* window glissante (rolling window)
* burst capacity
* refill adaptatif

### Formule :

```
tokens = min(max_tokens, tokens + refill_rate_per_second)
```

### Paramètres recommandés :

| Niveau     | max_tokens | refill_rate |
| ---------- | ---------- | ----------- |
| Free plan  | 20/s       | 5/s         |
| Basic      | 40/s       | 10/s        |
| Pro        | 100/s      | 25/s        |
| Enterprise | 500/s      | 100/s       |

**Tous ces chiffres sont ajustables via settings.**

---

# # **6. Limites par endpoint (exigences officielles)**

| Endpoint             | Limite par Tenant | Notes                 |
| -------------------- | ----------------- | --------------------- |
| `/s2/posts/schedule` | 10 req/s          | anti-burst, anti-spam |
| `/api/media/upload`  | 3 req/s           | poids élevé           |
| `/s2/posts/status`   | 20 req/s          | lecture fréquente     |
| `/s2/analytics/...`  | 50 req/s          | lecture intensive     |
| `/auth/*`            | 5 req/min per IP  | anti-bruteforce       |
| `/connectors/*`      | 10 req/s          | gestion tokens        |

---

# # **7. Anti-Abuse & Anti-Flood Rules**

Le système doit bloquer automatiquement :

### 7.1. Dépôt massif de scheduled_at identiques

→ risque d’inondation du scheduler.

### 7.2. Upload média > 100 Mo

→ refus + log + throttle.

### 7.3. Spam captation (boucle front bug)

→ circuit breaker automatique.

### 7.4. Session flood depuis un client mal configuré

→ throttle + email admin + log SRE.

---

# # **8. Circuit Breaker**

Le circuit breaker s’active si :

* worker latency > threshold
* scheduler backlog > 1000 jobs
* rate limiter dépasse 80% burst pendant >10 secondes
* erreur 500 > 5% en 30 secondes

### Comportement :

* APIs sensibles passent en **MODE DEGRADED**
* réponses : 503 avec retry-after
* allègement du scheduler window

---

# # **9. Backpressure API → Scheduler**

Pour éviter une surcharge du scheduler (DOC-013):

### Si :

`ready_queue_length > READY_THRESHOLD`
→ l’API Gateway ralentit la route `/schedule`.

### Politique :

* ralentissement progressif
* 429 avec message explicite
* journaux analytics dédiés

---

# # **10. Multi-Tenant Isolation (DOC-009)**

Le Gateway :

* extrait systématiquement `org_id` depuis JWT
* interdit toute surcharge par paramètre
* applique les limites par org_id
* empêche tout dépassement inter-tenant
* fournit un audit log complet par tenant

### Critique :

> Si un tenant dépasse ses limites, cela ne doit jamais affecter les autres.

---

# # **11. Logs & Observability (DOC-006)**

Chaque requête API doit logguer :

```json
{
  "event": "gateway_request",
  "org_id": "org_77",
  "user_id": "u_41",
  "ip": "...",
  "endpoint": "/s2/posts/schedule",
  "http_status": 200,
  "rate_limited": false,
  "duration_ms": 12
}
```

Métriques Prometheus officielles :

```
gateway_request_total
gateway_rate_limit_hits_total
gateway_latency_seconds
gateway_circuit_breaker_active
gateway_tenant_rl_exceeded_total
```

---

# # **12. SRE Reliability Objectives**

| SLO                         | Valeur      |
| --------------------------- | ----------- |
| Gateway Availability        | ≥ 99,95%    |
| Rate Limit Fairness         | 100% strict |
| P95 Latency                 | < 50ms      |
| Rate Limit Errors           | < 1%        |
| Circuit Breaker Activations | < 0.05%     |

---

# # **13. Policy de sécurité (DOC-008 alignment)**

Le Gateway doit :

* refuser tout payload > 5 MB
* refuser tout champ JSON non documenté (strict schema)
* refuser les requêtes avec body tropp profond
* vérifier signature JWT (HS256 ou RS256)
* empêcher bypass de `org_id`
* protéger `/auth` par bruteforce shield

---

# # **14. Tests obligatoires**

## Unitaires

* token bucket
* window glissante
* anti-burst
* circuit breaker
* detection org_id

## Intégration

* surcharge scheduler
* flood test
* test cross-tenant
* test tokens invalides

## E2E

* charges burst → comportement stable
* enchaînement 500 → circuit breaker s’active
* reconfiguration dynamique sans downtime

---

# # **15. CI/CD Compliance Rules**

### 🚫 Bloquant :

* route sans rate-limit
* absence extraction org_id
* absence logs gateway
* circuit breaker non implémenté
* absence tests anti-abuse
* tests flood non passés
* org_id fourni par client → violation

### ⚠ Warning :

* metrics manquantes
* thresholds non configurés
* absence dashboard gateway

---

# # **16. Checklist finale SRE++**

* [ ] Gateway stateless
* [ ] Rate limiting par tenant
* [ ] burst management opérationnel
* [ ] circuit breaker actif
* [ ] isolation tenant stricte
* [ ] backpressure vers scheduler
* [ ] anti-abuse & anti-flood en place
* [ ] logs structurés DOC-006
* [ ] métriques Prometheus
* [ ] CI/CD compliance validée

---

# # **17. Conclusion**

DOC-018 définit **le cadre officiel de l’API Gateway de Sparkmetriq S2**, garantissant :

* stabilité,
* sécurité,
* équité multi-tenant,
* résilience,
* scalabilité,
* conformité aux modules DOC-003 → DOC-017.

> **Toute PR violant DOC-018 est bloquée automatiquement.**

---
