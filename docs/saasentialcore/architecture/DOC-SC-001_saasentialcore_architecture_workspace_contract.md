Voici la **version propre, corrigée, finale et cohérente** de :

# ✅ **DOC-SC-001 — SaasentialCore Architecture & Workspace Contract**

*(remplace totalement la version précédente qui contenait des mentions “DOC-YY” et d’autres incohérences)*

Tu peux **copier-coller directement** ce Markdown dans :

```
docs/saasentialcore/architecture/DOC-SC-001_saasentialcore_architecture_workspace_contract.md
```

---

# 📘 `DOC-SC-001_saasentialcore_architecture_workspace_contract.md`

```markdown
---
title: DOC-SC-001 — SaasentialCore Architecture & Workspace Contract
version: 1.0
status: Stable
category: SaasentialCore / Multi-Startup / Architecture
last_updated: 2025-02-13
---

# 1. Objectif du document

Ce document constitue le **contrat d’architecture officiel** du workspace SaasentialCore.  
Il définit :

- la structure du monorepo,
- les frontières strictes entre `saasentialcore/`, `products/*`, `api/`, `frontend/`, `tests/`,
- les règles de dépendance autorisées,
- les responsabilités du socle multi-startup,
- les invariants permettant d'ajouter de nouveaux produits sans casser les existants.

SaasentialCore sert de **fondation technique unique** à toutes les startups / produits hébergés dans l’écosystème (Sparkmetriq, Sparkpusher, futurs modules).

Tout code doit respecter DOC-SC-001 pour être accepté.

---

# 2. Topologie du workspace

Le workspace officiel :

```

products/
sparkmetriq/      # Produit principal
sparkpusher/      # Variante packagée S2
saasentialcore/       # Socle multi-startup
api/                  # Façade FastAPI unifiée
frontend/             # Frontends (admin panel, consoles)
tests/                # Tests globaux
docs/                 # Documentation (architecture, audits, modules…)

```

Cette topologie est **stable** et ne doit pas être modifiée sans mise à jour de DOC-SC-001.

---

# 3. Rôle de chaque répertoire

## 3.1. `saasentialcore/` — Le socle technique
C’est le **core multi-startup**.  
Il contient :

- modèles globaux (Users, Organisations, Startups, Tenants),
- services transverses (auth, RBAC global, configuration, observabilité),
- intégrations bas niveau (Mongo, RabbitMQ, Vault…),
- loaders de configuration (aligné avec DOC-019),
- DI container & providers (aligné avec DOC-SC-003),
- événements globaux (aligné avec DOC-SC-006).

**Il ne contient aucune logique métier produit.**

---

## 3.2. `products/*` — Domaines métiers
Chaque dossier représente un produit complet :

```

products/sparkmetriq/
products/sparkpusher/
products/<nouveau-produit>/

```

Un produit :

- implémente son domaine métier,
- déclare ses propres services,
- fournit ses schémas et routes internes,
- importe `saasentialcore/`,
- n’écrit jamais de code dans SaasentialCore.

Exemples Sparkmetriq :

- Scheduler S2
- Dispatcher
- Connecteurs
- UnifiedPostPayload
- Analytics & SLO

---

## 3.3. `api/` — Façade FastAPI unifiée
Ce dossier :

- monte les routes des produits,
- applique middlewares (auth, logs, rate-limiting…),
- expose OpenAPI,
- contient les shims temporaires (cf. DOC-002),
- ne contient **aucune logique métier**.

---

## 3.4. `frontend/`
Frontends (Next.js / React) :

```

frontend/admin_panel/
frontend/sparkpusher_console/
frontend/shared_ui/

```

Rôle :

- interface utilisateur multi-startup,
- communication **uniquement via API HTTP**,
- jamais de logique backend,
- respecte DOC-011 pour l’Admin Panel.

---

## 3.5. `tests/`
Doit contenir :

```

tests/unit/
tests/integration/
tests/e2e/
tests/smoke/

```

Règles :

- un test ne doit jamais casser la séparation core/produit,
- les tests E2E valident les interactions entre SaasentialCore + produits,
- les tests architecture vérifient les règles DOC-SC-001.

---

# 4. Règles de dépendance (non négociables)

Modèle directionnel :

```

saasentialcore/        → dépend de personne
products/*             → dépendent de saasentialcore/
api/                   → dépend de saasentialcore/ + produits/*
frontend/              → dépend de api/ (jamais du backend interne)
tests/                 → dépend de tout (mode test only)

```

## Interdictions :

- ❌ `saasentialcore/` ne doit **jamais** importer `products/*`.
- ❌ Les produits ne doivent **jamais** dépendre entre eux.
- ❌ `frontend/` ne doit jamais importer du Python backend.
- ❌ `api/` ne doit contenir aucun service métier lourd.
- ❌ aucun produit ne doit redéfinir un composant déjà présent dans SaasentialCore.

---

# 5. Responsabilités de SaasentialCore

SaasentialCore doit fournir :

### 5.1. Identité & Organisations
- Users
- Organisations
- Startups
- Multi-tenant global (DOC-SC-004)

### 5.2. AuthN / AuthZ global
- JWT globaux (DOC-SC-005)
- RBAC cross-produits

### 5.3. Configuration unifiée
- Settings & secrets centralisés (DOC-019)
- Environment management

### 5.4. DI Container
- Providers communs (Mongo, cache, message broker)
- Injection cross-produits (DOC-SC-003)

### 5.5. Observabilité
- logs, traces, métriques
- dashboards core (DOC-SC-009)

### 5.6. Événements transverses
- bus interne multi-produits (DOC-SC-006)

---

# 6. Règles d’intégration des produits

Un produit doit :

- importer les services Core via DI,
- définir ses propres domaines & services,
- proposer ses schémas & routes internes,
- exposer ses endpoints via `api/`,
- ne jamais utiliser de config globale hors Settings.

Exemple Sparkmetriq :

```

products/sparkmetriq/
domain/
services/
schemas/
connectors/
s2/
s3/
s4/

```

---

# 7. API — Contrat d’utilisation du Core

- toutes les routes utilisent des dépendances (`Depends`) provenant de SaasentialCore,
- aucune route ne doit accéder directement à une DB,
- aucune route ne doit instancier un service produit **sans DI**,
- les shims doivent respecter DOC-002.

---

# 8. Tests — Stratégie multi-couches

### Unitaires :
- saasentialcore/
- produits

### Intégration :
- API + DB + services

### E2E :
Flux complets :
`Scheduler → Dispatcher → RabbitMQ → Worker → Connecteur`

### Tests architecture :
- vérification des dépendances interdites,
- conformité DOC-SC-001.

---

# 9. CI/CD — Règles obligatoires

Un job CI doit bloquer le merge si :

- un produit importe `saasentialcore/` dans le mauvais sens,
- `saasentialcore/` importe un produit,
- le frontend accède à du code backend,
- `api/` contient de la logique métier,
- un produit modifie le Core,
- un fichier Core dépend d’un répertoire produit.

---

# 10. Invariants (obligatoires)

1. SaasentialCore est **agnostique produit**.  
2. Les produits consomment le Core mais ne le modifient jamais.  
3. L’API est **une façade**, pas un moteur métier.  
4. Le frontend dépend **exclusivement** de l’API.  
5. Les tests couvrent interactions Core ↔ Produits.  
6. Toute nouvelle startup doit respecter DOC-SC-001.

---

# 11. Checklist d’onboarding développeur

- [ ] Comprendre la séparation Core / Produits / API / Frontend / Tests  
- [ ] Ne jamais écrire de logique métier dans `api/`  
- [ ] Toujours vérifier si un code doit vivre dans Core ou dans un produit  
- [ ] Respecter les règles de dépendance  
- [ ] Implémenter les tests au bon niveau  
- [ ] Lire tous les DOC-SC-00X avant contribution

---

# 12. Conclusion

DOC-SC-001 définit la **charpente du monorepo multi-startup** :

- séparation nette Core ↔ Produits,
- compatibilité multi-produits,
- évolutivité sans casse,
- cohérence structurelle,
- fondation pour les prochains documents DOC-SC-002 → DOC-SC-010.

Toute PR violant ce contrat est **bloquée automatiquement**.

```

---

# DOC-SC-001_saasentialcore_architecture_workspace_contract.md
