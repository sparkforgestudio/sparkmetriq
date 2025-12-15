Voici **DOC-009 — Multi-Tenant Architecture Contract (Version longue, 8–14 pages)**, format Markdown complet, prêt à être placé dans :

```
docs/architecture/DOC-009_multi_tenant_architecture_contract.md
```

⚠️ **J’ai bien mémorisé ta directive :**

> *Après les DOC-XX (architecture Sparkmetriq), il faudra produire des **DOC-YY** dédiés à **SaasentialCore** pour la stack multi-startup.*
> Cela sera intégré comme dépendance de fin de document et dans la roadmap.

---

# 📘 **DOC-009 — Multi-Tenant Architecture Contract (Version longue)**

*Document Technique de Référence — Sparkmetriq Multi-Tenant / Multi-Agences Isolation / SRE++*

```markdown
---
title: DOC-009 — Multi-Tenant Architecture Contract
version: 1.0
status: Stable
category: Architecture / Multi-Tenant / Security / Data Isolation
last_updated: 2025-02-02
---
```

---

# # **1. Objectif du document**

Sparkmetriq est une plateforme destinée à **des centaines d’agences** utilisant simultanément :

* Scheduler multi-plateformes
* Dispatcher
* Connecteurs sociaux
* Génération de contenu S3/S4
* Automations et bots
* Paiements, quotas, et workflows

Ce document formalise les **obligations techniques d’isolation multi-tenant (multi-agences)**.

Objectifs :

* **séparer strictement les données** entre agences,
* **empêcher les accès croisés** (horizontal privilege escalation),
* **isoler les pipelines de publication**,
* **isoler les ressources compute**,
* garantir que S2/S3/S4 fonctionnent en **multi-tenant sécurisé et scalable**,
* fournir la base future pour **SaasentialCore Multi-Startup Stack (DOC-YY)**.

Ce document est **normatif et bloquant** pour toute PR.

---

# # **2. Modèle Multi-Tenant de Sparkmetriq**

Sparkmetriq adopte un modèle hybride :

## ✔ **2.1. Multi-Tenant Logique (par défaut)**

Toutes les agences cohabitent dans les mêmes services :

* une seule API FastAPI
* un scheduler
* un cluster de workers
* une seule DB Mongo
* un broker RabbitMQ

Mais toutes les données sont **strictement partitionnées** par `org_id`.

---

## ✔ **2.2. Multi-Tenant Physique (option Enterprise)**

Certaines agences premium peuvent être isolées :

* nœud worker dédié
* queue dédiée
* connecteurs isolés
* storage séparé
* clé d’encryption propre

Ce document couvre les **2 modèles**, le logique étant obligatoire.

---

# # **3. Principe fondamental : org_id as Boundary**

### 3.1. org_id est la frontière d’isolation

Chaque ressource, document, job ou token DOIT contenir :

```
org_id
```

Et chaque requête doit être filtrée :

```
query = {"org_id": current_user.org_id}
```

Aucun endpoint ne doit retourner **quoi que ce soit** qui ne comporte pas l’`org_id` du tenant.

---

### 3.2. Org-Bound Enforcement (OBE)

Une violation OBE est **critique** :

* afficher les comptes sociaux d’une autre agence
* consommer les quotas d’une autre agence
* publier sur un compte externe d’une autre agence
* voir l’historique S2 d’une autre agence

**CI doit refuser toute PR non conforme.**

---

# # **4. Architecture d’Isolation**

## **4.1. API Layer**

Le middleware ajoute :

* `current_org_id`
* `current_user_id`
* `role` (RBAC)

Toutes les routes doivent :

* vérifier `role`,
* restreindre toute requête par `org_id`,
* interdire tout paramètre `org_id` fourni par l’utilisateur.

**org_id ne doit jamais venir du payload du client.**

---

## **4.2. Scheduler Layer**

Les jobs appartiennent à une agence :

```json
{
  "job_id": "...",
  "org_id": "org_541",
  "platform": "instagram",
  "account_id": "acc_33",
  "state": "RESERVED",
  ...
}
```

Interdictions :

* ❌ fusion inter-tenant dans les queues
* ❌ voir les jobs d'une autre agence

---

## **4.3. Workers & Queues RabbitMQ**

Le mapping recommandé :

| Agence        | Queue                | Worker             |
| ------------- | -------------------- | ------------------ |
| org_1         | `s2.org_1.jobs`      | worker pool limité |
| org_2         | `s2.org_2.jobs`      | worker pool limité |
| small clients | `s2.shared.low`      | shared workers     |
| enterprise    | `s2.enterprise.orgX` | exclusive workers  |

Les workers **ne doivent jamais** consommer hors de leur partition.

---

## **4.4. Connecteurs**

Chaque connecteur :

* ne possède que les tokens de son `org_id`
* ne doit jamais accéder à un token d’une autre agence
* doit logguer `org_id` obligatoirement (DOC-006)

---

# # **5. Isolation des données MongoDB**

## **5.1. org_id obligatoire dans toutes les collections**

| Collection  | org_id obligatoire ? |
| ----------- | -------------------- |
| jobs        | ✔                    |
| quotas      | ✔                    |
| idempotence | ✔                    |
| accounts    | ✔                    |
| connectors  | ✔                    |
| media       | ✔                    |
| logs métier | ✔                    |

---

## **5.2. Requêtes toujours filtrées**

Interdit :

```python
jobs.find({})
```

Correct :

```python
jobs.find({"org_id": org_id})
```

---

## **5.3. Index composés**

Performance + sécurité :

```
{ org_id: 1, scheduled_at: 1 }
{ org_id: 1, status: 1 }
```

---

## **5.4. Encryption Per Tenant**

Par défaut :
Encryption-at-rest OVH + volumes chiffrés.

Niveau enterprise :
Encryption secrets **per org**.

---

# # **6. Isolation Connecteurs / Tokens OAuth**

### 6.1. Structure standard

```json
{
  "_id": "...",
  "org_id": "org_541",
  "platform": "instagram",
  "access_token": "<encrypted>",
  "refresh_token": "<encrypted>",
  "expires_at": "..."
}
```

### 6.2. Règles :

* un token appartient **à une seule agence**,
* jamais stocké en clair,
* jamais exposé dans les logs,
* jamais envoyé au frontend,
* jamais accessible à un worker d'une autre agence.

---

# # **7. Tenant-Level Resource Limiting (quotas & perf)**

Chaque agence doit posséder :

* quotas journaliers
* quotas mensuels
* limites de scheduling
* limites de triggers
* limites de stockage
* limites de throughput

Basé sur DOC-004 (State Machine Quotas).

---

# # **8. Sécurité Multi-Tenant**

### 8.1. Anti-tenant horizontal escalations

Interdits :

* passer un `org_id` d’une autre agence dans un payload
* filtrage non basé sur l’utilisateur authentifié
* exposer des tokens externes
* utiliser un connecteur global partagé

---

### 8.2. Validation stricte des identifiants

Chaque :

* job_id
* account_id
* token_id
* media_id

DOIT être vérifié par `org_id`.

---

# # **9. Observabilité Tenant-Scopée (DOC-006)**

Tous les logs événementiels doivent inclure :

```
org_id
tenant_span_id
tenant_request_id
role
```

Les dashboards Grafana doivent être filtrables par agence.

---

# # **10. Tests Multi-Tenant (unitaires & E2E)**

Cas obligatoires :

### ✔ Tenant A schedule un post

→ Tenant B ne peut ni le lire ni l’exécuter.

### ✔ Tenant A possède un token Instagram

→ Tenant B ne le voit jamais.

### ✔ Deux tenants partagent le scheduler

→ aucune collision de données.

### ✔ Workers reçoivent des jobs uniquement de leur tenant.

### ✔ MongoDB queries sans org_id

→ test doit échouer.

---

# # **11. CI/CD — Multi-Tenant Compliance**

### 🚫 Bloquant

* route non filtrée par org_id
* payload contenant un org_id client
* connecteur recevant un token hors tenant
* worker consommant une mauvaise queue
* requête MongoDB non filtrée
* job sans `org_id`
* token stocké en clair

### ⚠ Warning

* logs sans org_id
* dashboards non filtrés
* absence tests multi-tenant

---

# # **12. Checklist finale SRE++ Multi-Tenant**

* [ ] org_id obligatoire dans toute donnée
* [ ] API filtre endpoints par tenant
* [ ] workers isolés par org ou pool
* [ ] connecteurs isolés par org
* [ ] MongoDB filtré par org
* [ ] encryption-at-rest + encryption per tenant
* [ ] quotas isolés par tenant
* [ ] tests multi-tenant faits
* [ ] CI multi-tenant activée
* [ ] logs tenant-scopés
* [ ] admin panel isolé par tenant
* [ ] aucun secret partagé entre agences

---

# # **13. Extension future — DOC-YY SaasentialCore Multi-Startup Contract**

**Mémorisé pour la suite.**

Les DOC-YY définiront :

* isolation inter-startup (Sparkmetriq, MusAI, EclipsAI, autres clients)
* séparation organisationnelle au niveau SaaSentialCore
* clés d’encryption par startup
* supervision mutualisée
* ressources partagées sécurisées
* gestion multi-cloud futur

Le modèle multi-startup est une **extension de ce contrat multi-tenant**, mais appliqué à une couche supérieure.

---

# # **14. Conclusion**

DOC-009 constitue la fondation **d'isolation multi-tenant avancée** pour Sparkmetriq.
C’est indispensable pour :

* sécurité,
* conformité,
* scalabilité commerciale,
* architecture SaaS professionnelle,
* multi-agences et multi-startups.

> Toute violation de DOC-009 est bloquante.
> Aucun module Sparkmetriq ne peut être mergé sans conformité multi-tenant.

---
