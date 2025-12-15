# 📐 SCHÉMA DE L'ARCHITECTURE

**Date**: 2024  
**Version**: Post-migration `products/` à la racine

---

## 🏗️ STRUCTURE GLOBALE DU MONOREPO

```
musai-musemgtm-platform/
│
├── 📦 saasentialcore/                    # MODULE CORE GÉNÉRIQUE
│   ├── app/
│   │   └── core/                         # Configuration générique uniquement
│   │       ├── config.py                 # Settings génériques
│   │       ├── deps.py                   # Dépendances FastAPI génériques
│   │       └── security.py               # Sécurité générique (JWT, etc.)
│   │
│   ├── models/
│   │   ├── db/                           # Modèles de persistance core
│   │   │   ├── job.py                    # Modèle générique de job
│   │   │   ├── org.py                    # Modèle d'organisation
│   │   │   ├── quotas.py                 # Modèle de quotas
│   │   │   └── user.py                   # Modèle d'utilisateur
│   │   │
│   │   └── schemas/                      # Schémas Pydantic core
│   │       ├── job_schema.py
│   │       ├── org_schema.py
│   │       ├── quotas_schema.py
│   │       └── user_schema.py
│   │
│   ├── services/                         # Services génériques réutilisables
│   │   ├── scheduler_service.py          # Moteur générique de scheduling
│   │   ├── quotas_service.py             # Gestion générique des quotas
│   │   ├── auth_service.py               # Authentification générique
│   │   ├── org_service.py                # Gestion des organisations
│   │   └── metrics_service.py            # Métriques génériques
│   │
│   └── tests/                            # Tests d'intégration génériques
│       ├── test_scheduler_service.py
│       ├── test_quotas_service.py
│       ├── test_auth_service.py
│       └── test_scheduler_and_quotas_integration.py
│
├── 📦 products/                          # PRODUITS COMMERCIAUX (à la racine)
│   │
│   ├── sparkmetriq/                      # PRODUIT 1 : Suite globale historique
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── scheduler.py          # Routes spécifiques Sparkmetriq
│   │   │                                 # (drafts, AB tests, recycle, etc.)
│   │   │
│   │   ├── services/
│   │   │   └── scheduler/
│   │   │       ├── planner_service.py    # Gestion des drafts
│   │   │       ├── abtest_service.py      # Tests A/B
│   │   │       ├── recycle_service.py     # Recyclage de contenu
│   │   │       ├── ai_copy_service.py     # Génération IA
│   │   │       ├── publish_service.py     # Publication Sparkmetriq
│   │   │       └── job_runner.py          # APScheduler Sparkmetriq
│   │   │
│   │   ├── admin_panel/                  # Module Python (vide, réservé)
│   │   └── tests/                        # Tests spécifiques Sparkmetriq
│   │
│   └── sparkpusher/                      # PRODUIT 2 : S2 (Content Studio)
│       ├── api/
│       │   └── routes/
│       │       └── scheduler.py          # Routes S2
│       │                                 # (POST /posts/schedule, GET /jobs/{id}, etc.)
│       │
│       ├── services/
│       │   ├── task.py                   # Exécution jobs S2
│       │   ├── quotas_service.py         # Vérification quotas S2
│       │   └── config.py                 # Configuration S2
│       │
│       ├── admin_panel/                  # Module Python (vide, réservé)
│       └── tests/
│           └── test_s2_scheduler_sparkpusher.py
│
├── 📦 api/                               # API HISTORIQUE (shims de compatibilité)
│   ├── routes/
│   │   └── scheduler.py                  # Shim qui délègue vers products/*
│   │
│   ├── services/
│   │   ├── scheduler/                    # Shims de compatibilité
│   │   │   ├── task.py                   # → products.sparkpusher.services.task
│   │   │   ├── config.py                 # → products.sparkpusher.services.config
│   │   │   ├── quotas_service.py         # → products.sparkpusher.services.quotas_service
│   │   │   ├── planner_service.py        # → products.sparkmetriq.services.scheduler.planner_service
│   │   │   ├── abtest_service.py         # → products.sparkmetriq.services.scheduler.abtest_service
│   │   │   ├── recycle_service.py        # → products.sparkmetriq.services.scheduler.recycle_service
│   │   │   ├── ai_copy_service.py        # → products.sparkmetriq.services.scheduler.ai_copy_service
│   │   │   ├── publish_service.py        # → products.sparkmetriq.services.scheduler.publish_service
│   │   │   └── job_runner.py             # → products.sparkmetriq.services.scheduler.job_runner
│   │   │
│   │   └── core/
│   │       └── saasential_bridge.py      # Bridge vers saasentialcore
│   │
│   ├── schemas/                          # Schémas partagés (à migrer progressivement)
│   │   ├── payload_schema.py             # UnifiedPostPayload, MediaItem, etc.
│   │   ├── scheduler.py                  # SchedulePostResponse, etc.
│   │   └── job_details_schema.py         # JobDetails, JobPlatformStatus
│   │
│   └── main.py                           # Point d'entrée FastAPI
│
├── 📦 frontend/                          # FRONTEND NEXT.JS (séparé)
│   └── admin_panel/
│       └── pages/
│           └── content/
│               ├── create.tsx            # Page création post S2
│               ├── calendar.tsx           # Calendrier S2
│               └── job/[jobId].tsx        # Détails job S2
│
├── 📦 tests/                             # TESTS E2E APPLICATION
│   ├── test_s2_e2e.py                    # Tests E2E S2
│   ├── test_job_details_endpoint.py
│   ├── test_calendar_endpoint.py
│   ├── test_scheduler_retries.py
│   └── test_org_quotas.py
│
├── 📦 scripts/                           # Scripts utilitaires
│
└── 📄 PLAN_EXTRACTION_S2_SPARKPUSHER.md # Plan d'extraction S2
```

---

## 🔄 FLUX DE DÉPENDANCES

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUITS (products/)                      │
│                                                               │
│  ┌──────────────────┐          ┌──────────────────┐         │
│  │  sparkmetriq/    │          │  sparkpusher/    │         │
│  │                  │          │  (S2)            │         │
│  │  - Routes        │          │  - Routes        │         │
│  │  - Services      │          │  - Services      │         │
│  │  - Tests         │          │  - Tests         │         │
│  └────────┬─────────┘          └────────┬─────────┘         │
│           │                               │                  │
│           └───────────────┬───────────────┘                  │
│                           │                                  │
│                           ▼                                  │
│              ┌──────────────────────┐                       │
│              │   saasentialcore/    │                       │
│              │                      │                       │
│              │  - services/         │                       │
│              │  - models/           │                       │
│              │  - app/core/         │                       │
│              └──────────────────────┘                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    API HISTORIQUE (api/)                    │
│                                                               │
│  - routes/scheduler.py  (shim)                              │
│  - services/scheduler/* (shims)                              │
│  - main.py              (point d'entrée)                     │
│                                                               │
│  Délègue vers products/* via shims de compatibilité         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 RÈGLES DE SÉPARATION

### ✅ saasentialcore/ (CORE GÉNÉRIQUE)
- ✅ Services génériques réutilisables
- ✅ Modèles et schémas core (jobs, quotas, orgs, users)
- ✅ Configuration générique
- ❌ **PAS de routes API spécifiques produit**
- ❌ **PAS de logique métier spécifique**

### ✅ products/sparkmetriq/ (SUITE GLOBALE)
- ✅ Routes multi-modules historiques
- ✅ Services spécifiques Sparkmetriq (drafts, AB tests, recycle)
- ✅ S'appuie sur `saasentialcore` pour le core
- ❌ **PAS de dépendance vers sparkpusher**

### ✅ products/sparkpusher/ (PRODUIT S2)
- ✅ Routes S2 (scheduler de posts, calendrier)
- ✅ Services S2 (task, quotas_service, config)
- ✅ S'appuie sur `saasentialcore` pour le core
- ❌ **PAS de dépendance vers sparkmetriq**

### ✅ api/ (SHIMS DE COMPATIBILITÉ)
- ✅ Délègue vers `products/*` via shims
- ✅ Maintient la compatibilité avec le code existant
- ✅ Point d'entrée FastAPI (`main.py`)

---

## 🎯 PRINCIPES ARCHITECTURAUX

1. **Séparation core/produits**
   - `saasentialcore/` = générique réutilisable
   - `products/` = spécifique par produit

2. **Indépendance des produits**
   - `sparkmetriq` et `sparkpusher` sont indépendants
   - Aucune dépendance entre produits
   - Chaque produit dépend uniquement de `saasentialcore`

3. **Shims de compatibilité**
   - `api/` maintient les imports historiques
   - Délègue vers `products/*` en interne
   - Permet une migration progressive

4. **Séparation frontend/backend**
   - Frontend dans `frontend/`
   - Backend dans `saasentialcore/`, `products/`, `api/`

---

## 📊 HIÉRARCHIE DES IMPORTS

```
┌─────────────────────────────────────────┐
│  products/sparkpusher/                  │
│  └─→ saasentialcore.services.*          │
│  └─→ saasentialcore.models.*            │
│  └─→ api.schemas.* (partagé)            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  products/sparkmetriq/                  │
│  └─→ saasentialcore.services.*          │
│  └─→ saasentialcore.models.*            │
│  └─→ api.schemas.* (partagé)            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  api/                                   │
│  └─→ products.sparkpusher.*            │
│  └─→ products.sparkmetriq.*             │
│  └─→ saasentialcore.*                  │
└─────────────────────────────────────────┘
```

---

## ✅ CONFORMITÉ

- ✅ `products/` à la racine (pas dans `saasentialcore/`)
- ✅ `saasentialcore/` contient uniquement le core générique
- ✅ Pas de routes API dans `saasentialcore/app/`
- ✅ Séparation frontend/backend respectée
- ✅ Indépendance des produits garantie

**Statut**: ✅ **100% CONFORME**

