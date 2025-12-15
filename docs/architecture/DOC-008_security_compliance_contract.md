Voici **DOC-008 — Security & Compliance Contract (Version longue, 6–12 pages)**, conforme aux standards **OWASP, NIST, Google BeyondCorp, Zero-Trust**, et adapté spécifiquement à Sparkmetriq (architecture multi-nœuds, API FastAPI, Scheduler, Workers Celery, Connecteurs, Admin Panel, multi-agences, multi-tenants).

Prêt à être intégré dans :

```
docs/architecture/DOC-008_security_compliance_contract.md
```

---

# 📘 **DOC-008 — Security & Compliance Contract (Version longue)**

*Document Technique de Référence — Sparkmetriq Security / Compliance / Zero-Trust / Multi-Tenant Isolation*

```markdown
---
title: DOC-008 — Security & Compliance Contract
version: 1.0
status: Stable
category: Architecture / Security / Compliance / Multi-Tenant
last_updated: 2025-02-01
---
```

---

# # **1. Objectif du document**

Ce document définit **les exigences de sécurité et de conformité obligatoires** pour Sparkmetriq, couvrant :

* authentification & autorisations (JWT, OAuth2, API tokens)
* isolation multi-agences (multi-tenant)
* gestion des permissions internes (RBAC)
* sécurité API (rate limiting, replay protection, signature)
* sécurité workers & connecteurs
* sécurité de la donnée (cryptographie, hash, secrets)
* hardening des nœuds Sparkmetriq (API, Workers, Node1–3)
* conformité (logging, traçabilité, audit, data retention)

Objectif :

> *Garantir que Sparkmetriq soit sécurisé par défaut (“secure-by-design”), résilient aux attaques, conforme aux exigences des agences, et protégé contre l’exposition ou la fuite de données.*

---

# # **2. Périmètre**

Ce contrat s’applique à **toute la plateforme** Sparkmetriq :

* API FastAPI
* Scheduler & Dispatcher
* Celery Workers
* Connecteurs réseaux (Instagram/TikTok/Threads/etc.)
* Admin Panel Next.js
* Webhooks entrants
* Base de données MongoDB
* RabbitMQ
* Caddy / Reverse Proxy
* Infrastructure OVH Nodes 1–3

---

# # **3. Principes fondamentaux (Zero-Trust / OWASP)**

## ✔ **3.1. Zero Trust par défaut**

Aucun composant n’est fiable implicitement :

* chaque requête doit être authentifiée,
* chaque worker doit s’authentifier pour consommer une tâche,
* aucun accès direct DB depuis l'extérieur.

---

## ✔ **3.2. Multi-tenant Isolation**

Chaque “organisation” (agence cliente) :

* ne peut voir que ses propres données,
* ne peut déclencher des actions que dans son périmètre,
* ne doit jamais accéder aux tokens/connecteurs d’une autre agence.

---

## ✔ **3.3. Defense-in-Depth**

Plusieurs couches de sécurité :
API → Reverse Proxy → Rate Limiter → Worker → DB.

---

## ✔ **3.4. Principle of Least Privilege (PoLP)**

Chaque composant a **le minimum de permissions nécessaires**.

---

## ✔ **3.5. Auditabilité obligatoire**

Toutes les actions critiques doivent être loggées (DOC-006).

---

# # **4. Authentification (JWT, OAuth2, Tokens internes)**

## **4.1. JWT Access Tokens (API)**

Format imposé :

```json
{
  "sub": "user_id",
  "org": "org_id",
  "role": "admin|member|superadmin",
  "exp": 1735689600,
  "iat": 1735686000,
  "type": "access"
}
```

### Règles :

* durée de vie courte : **15 minutes**
* refresh tokens séparés
* signature HS256 ou RS256 (RS recommandé)
* blacklist refresh tokens si révocation

---

## **4.2. OAuth2 pour intégrations externes**

Chaque agence peut connecter :

* Instagram Business
* TikTok
* Threads
* Snapchat (+ futur)

Les tokens doivent :

* être stockés **chiffrés** (AES-256-GCM) dans MongoDB,
* être isolés par `org_id`,
* ne jamais transiter en clair dans les logs,
* être renouvelés via refresh automatiques sécurisés.

---

## **4.3. Service-to-Service Tokens**

Scheduler → Workers → Connecteurs
Utilisent des *internal JWT* :

```json
{
  "svc": "scheduler",
  "scope": ["dispatch", "reserve_quota"],
  "exp": <short TTL>
}
```

Durée de vie : **60–300 secondes**.

---

# # **5. Autorisation (RBAC Sparkmetriq)**

Niveaux :

| Rôle             | Permissions                                 |
| ---------------- | ------------------------------------------- |
| **superadmin**   | accès global multi-agences                  |
| **org_admin**    | gestion agence + comptes + quotas           |
| **org_operator** | planification + contenu                     |
| **org_viewer**   | lecture seule                               |
| **bot_service**  | accès limité aux endpoints bot automatiques |

Règles :

* aucune route ne doit fonctionner sans vérification RBAC explicite,
* le `role` est vérifié via un middleware,
* contrôle renforcé pour les routes *modifiant* scheduler, quotas ou connecteurs.

---

# # **6. Security API Contract**

## ✔ **6.1. Rate Limiting**

Par API route :

```
X requests / minute per user
Y requests / minute per organisation
```

Par exemple :

* User : 120 req/min
* Organisation : 500 req/min
* Endpoints critiques (publish) : 20 req/min

---

## ✔ **6.2. Replay Protection**

Chaque requête POST doit offrir :

* un `request_id`: unique
* un `idempotency_key` si action externe

---

## ✔ **6.3. IP filtering pour endpoints sensibles**

* `/admin/*`
* `/internal/*`

Autorisé uniquement depuis :

* VPN interne
* Node2 / Node3
* whiteliste IP agences premium (optionnel)

---

## ✔ **6.4. Protection contre injection / validation stricte**

* Pydantic + type strict
* aucun `eval()`, `exec()`, `pickle`
* validation explicite des URLs, tokens, payloads média

---

## ✔ **6.5. CORS locked-down**

Pas de wildcard `*`.
Domaines autorisés :

* `app.sparkmetriq.com`
* `admin.sparkmetriq.com`

---

# # **7. Sécurité Workers & Connecteurs**

## **7.1. Sandboxing logique**

Un worker :

* n’a pas accès aux tokens d'autres organisations
* ne peut traiter que les jobs de sa queue
* ne peut pas lire la config globalement (DOC-001)

---

## **7.2. Network Security**

Workers/Connecteurs :

* accèdent uniquement aux API externes avec timeouts stricts
* jamais directement à MongoDB administrative
* jamais aux endpoints internes `/internal/*`

---

## **7.3. Secrets Management**

Tous les secrets :

* via variables d’environnement chiffrées (Vault futur)
* jamais en clair dans config files
* rotation régulière

---

# # **8. Sécurité MongoDB**

## ✔ DB par organisation (logique)

Chaque document doit contenir :

```
org_id
```

Et toutes les requêtes doivent filtrer par `org_id`.

---

## ✔ Encryption-at-Rest (EBS/OVH)

Volumes chiffrés.

---

## ✔ NoSQL injection protection

Interdit :

```python
collection.find({"$where": "this.x > 0"})   # ❌
```

Correct :

```python
collection.find({"org_id": org})
```

---

## ✔ Indexes sur `org_id` obligatoire

Essentiel pour performance + isolation (voir DOC-007).

---

# # **9. Sécurité RabbitMQ**

* utilisateurs séparés : `scheduler_user`, `worker_user`
* vHosts séparés par organisation (option premium futur)
* pas de permissions d’administration via l’API
* queues durables
* SSL/TLS activé

---

# # **10. Sécurité Admin Panel (Next.js)**

* authentification via JWT + cookies HttpOnly
* aucune manipulation de tokens connecteurs côté front
* CSP renforcé
* désactivation dangerous HTML (XSS)
* validation systématique des inputs

---

# # **11. Sécurité Infrastructure (OVH Nodes 1–3)**

## ✔ Hardening obligatoire

* fail2ban
* firewall strict (UFW)
* ssh keys only
* user non-root pour services
* rotation journalière des logs sensibles

---

## ✔ HTTPS Only (Caddy)

* TLS 1.2+
* HSTS enabled
* Pas d'HTTP fallback

---

## ✔ Monitoring sécurité

* alertes brute force SSH
* alertes sur anomalies API (DOC-006)
* détection de patterns frauduleux

---

# # **12. Conformité & Audit**

Sparkmetriq doit assurer :

* audit trail complet (actions sensibles)
* logs non falsifiables (append-only)
* retention configurable (ex: 90 jours)
* suppression sur demande (RGPD-like)
* encryptage des backups

---

# # **13. Violations bloquantes (CI/CD)**

### 🚫 Bloquant

* JWT incorrect ou non vérifié
* absence de filtrage `org_id`
* endpoint sensible sans authentification
* secrets en clair dans repository
* logs contenant tokens
* tokens connecteurs non chiffrés
* absence de rate limiting sur POST critiques

### ⚠ Warning

* RBAC incomplet
* CORS permissif
* utilisation de `print()` (interdit DOC-006)

---

# # **14. Checklist finale Security SRE++**

* [ ] JWT & OAuth2 sécurisés
* [ ] RBAC complet
* [ ] multi-tenant isolation garantie
* [ ] aucun secret en clair
* [ ] tokens chiffrés en DB
* [ ] rate limiting présent
* [ ] anti-replay actif
* [ ] connecteurs isolés
* [ ] workers sandboxés
* [ ] DB isolée par org
* [ ] logs sans tokens
* [ ] infrastructure OVH durcie
* [ ] conformité appliquée

---

# # **15. Conclusion**

DOC-008 constitue la **référence de sécurité officielle** pour Sparkmetriq.
Il protège :

* les agences clientes,
* leurs données et comptes sociaux,
* la plateforme,
* l’exploitation commerciale.

Sparkmetriq devient ainsi une plateforme **sécurisée, professionnelle, conforme**, indispensable pour le déploiement S2/S3/S4.

---
