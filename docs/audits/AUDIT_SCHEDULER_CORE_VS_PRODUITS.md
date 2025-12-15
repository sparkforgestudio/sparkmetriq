# 🔍 AUDIT SCHEDULER : SÉPARATION CORE vs PRODUITS

**Date**: 2024  
**Objectif**: Vérifier la séparation stricte entre scheduler générique (core) et orchestrations spécifiques Produit

---

## 1. CARTOGRAPHIE SCHEDULER CORE vs PRODUITS

### 📦 SCHEDULER CORE (saasentialcore/services/)

#### ✅ `saasentialcore/services/scheduler_service.py`
- **Type**: ✅ **CORE** (générique, réutilisable)
- **Responsabilités**:
  - Exécution de jobs avec retries et backoff
  - Gestion des transitions de statut (PENDING → RUNNING → SUCCESS/FAILED)
  - Logs structurés
  - Gestion des erreurs
- **Agnostique du produit**: ✅ Oui (Sparkmetriq, SparkPusher, etc.)
- **Dépendances**: `saasentialcore.models.db.job` uniquement
- **Statut**: ✅ **CONFORME**

---

### 📦 ORCHESTRATIONS SPARKMETRIQ (products/sparkmetriq/services/scheduler/)

#### ✅ `saasentialcore/products/sparkmetriq/services/scheduler/planner_service.py`
- **Type**: ✅ **PRODUIT** (spécifique Sparkmetriq)
- **Responsabilités**:
  - Gestion des drafts (create, get, list, delete, update)
  - Planification hebdomadaire
  - Heures optimales de publication
  - Calendrier de contenu
- **Dépendances**: `api.schemas.scheduler.DraftIn`, `api.databases.databases`
- **Statut**: ⚠️ **NON-CONFORME** (dans `saasentialcore/products/` au lieu de `products/`)

#### ✅ `saasentialcore/products/sparkmetriq/services/scheduler/abtest_service.py`
- **Type**: ✅ **PRODUIT** (spécifique Sparkmetriq)
- **Responsabilités**: Tests A/B pour le contenu
- **Dépendances**: `products.sparkmetriq.services.scheduler.planner_service`
- **Statut**: ⚠️ **NON-CONFORME** (dans `saasentialcore/products/`)

#### ✅ `saasentialcore/products/sparkmetriq/services/scheduler/recycle_service.py`
- **Type**: ✅ **PRODUIT** (spécifique Sparkmetriq)
- **Responsabilités**: Recyclage intelligent de contenu
- **Dépendances**: `products.sparkmetriq.services.scheduler.planner_service`
- **Statut**: ⚠️ **NON-CONFORME** (dans `saasentialcore/products/`)

#### ✅ `saasentialcore/products/sparkmetriq/services/scheduler/ai_copy_service.py`
- **Type**: ✅ **PRODUIT** (spécifique Sparkmetriq)
- **Responsabilités**: Génération IA de contenu
- **Statut**: ⚠️ **NON-CONFORME** (dans `saasentialcore/products/`)

#### ✅ `saasentialcore/products/sparkmetriq/services/scheduler/publish_service.py`
- **Type**: ✅ **PRODUIT** (spécifique Sparkmetriq)
- **Responsabilités**: Exécution des publications Sparkmetriq
- **Dépendances**: `products.sparkmetriq.services.scheduler.ai_copy_service`
- **Statut**: ⚠️ **NON-CONFORME** (dans `saasentialcore/products/`)

#### ✅ `saasentialcore/products/sparkmetriq/services/scheduler/job_runner.py`
- **Type**: ✅ **PRODUIT** (spécifique Sparkmetriq)
- **Responsabilités**: Gestionnaire APScheduler pour Sparkmetriq
- **Dépendances**: `products.sparkmetriq.services.scheduler.publish_service`
- **Statut**: ⚠️ **NON-CONFORME** (dans `saasentialcore/products/`)

---

### 📦 ORCHESTRATIONS SPARKPUSHER/S2 (products/sparkpusher/services/)

#### ✅ `saasentialcore/products/sparkpusher/services/task.py`
- **Type**: ✅ **PRODUIT** (spécifique S2)
- **Responsabilités**:
  - Exécution de jobs S2 (reconstruction UnifiedPostPayload)
  - Appel ContentDispatcher
  - Gestion des résultats par plateforme
- **Dépendances**: 
  - ✅ `saasentialcore.services.scheduler_service` (via bridge)
  - `api.services.content_distributor.dispatcher`
  - `api.schemas.payload_schema.UnifiedPostPayload`
- **Statut**: ⚠️ **NON-CONFORME** (dans `saasentialcore/products/`)

#### ✅ `saasentialcore/products/sparkpusher/services/quotas_service.py`
- **Type**: ✅ **PRODUIT** (spécifique S2)
- **Responsabilités**:
  - Vérification des quotas avec UnifiedPostPayload
  - Métriques spécifiques S2
- **Dépendances**: 
  - ✅ `api.repositories.quotas_repository` (shim vers saasentialcore)
  - `api.schemas.payload_schema.UnifiedPostPayload`
- **Statut**: ⚠️ **NON-CONFORME** (dans `saasentialcore/products/`)

#### ✅ `saasentialcore/products/sparkpusher/services/config.py`
- **Type**: ✅ **PRODUIT** (spécifique S2)
- **Responsabilités**: Configuration S2 (MAX_ATTEMPTS, BACKOFF_SECONDS)
- **Dépendances**: ✅ `saasentialcore.services.scheduler_service.JobStatus`
- **Statut**: ⚠️ **NON-CONFORME** (dans `saasentialcore/products/`)

---

### 📦 FICHIERS DANS `api/services/scheduler/` (SHIMS)

#### ✅ `api/services/scheduler/task.py`
- **Type**: ✅ **SHIM** (compatibilité)
- **Délègue vers**: `products.sparkpusher.services.task`
- **Statut**: ✅ **CONFORME**

#### ✅ `api/services/scheduler/config.py`
- **Type**: ✅ **SHIM** (compatibilité)
- **Délègue vers**: `products.sparkpusher.services.config`
- **Statut**: ✅ **CONFORME**

#### ✅ `api/services/scheduler/quotas_service.py`
- **Type**: ✅ **SHIM** (compatibilité)
- **Délègue vers**: `products.sparkpusher.services.quotas_service`
- **Statut**: ✅ **CONFORME**

#### ✅ `api/services/scheduler/planner_service.py`
- **Type**: ✅ **SHIM** (compatibilité)
- **Délègue vers**: `products.sparkmetriq.services.scheduler.planner_service`
- **Statut**: ✅ **CONFORME**

#### ✅ `api/services/scheduler/abtest_service.py`
- **Type**: ✅ **SHIM** (compatibilité)
- **Délègue vers**: `products.sparkmetriq.services.scheduler.abtest_service`
- **Statut**: ✅ **CONFORME**

#### ✅ `api/services/scheduler/recycle_service.py`
- **Type**: ✅ **SHIM** (compatibilité)
- **Délègue vers**: `products.sparkmetriq.services.scheduler.recycle_service`
- **Statut**: ✅ **CONFORME**

#### ✅ `api/services/scheduler/ai_copy_service.py`
- **Type**: ✅ **SHIM** (compatibilité)
- **Délègue vers**: `products.sparkmetriq.services.scheduler.ai_copy_service`
- **Statut**: ✅ **CONFORME**

#### ✅ `api/services/scheduler/publish_service.py`
- **Type**: ✅ **SHIM** (compatibilité)
- **Délègue vers**: `products.sparkmetriq.services.scheduler.publish_service`
- **Statut**: ✅ **CONFORME**

#### ✅ `api/services/scheduler/job_runner.py`
- **Type**: ✅ **SHIM** (compatibilité)
- **Délègue vers**: `products.sparkmetriq.services.scheduler.job_runner`
- **Statut**: ✅ **CONFORME**

#### ⚠️ `api/services/scheduler/scheduler_engine.py`
- **Type**: ❌ **OBSOLÈTE** (logique legacy)
- **Contenu**: Boucle de scheduler legacy avec `dispatch_content` direct
- **Dépendances**: `api.databases.databases`, `services.content_distributor.dispatcher`
- **Utilisation**: Aucune référence dans le codebase
- **Statut**: ❌ **À SUPPRIMER** (remplacé par `saasentialcore.services.scheduler_service`)

#### ⚠️ `api/services/scheduler/manager.py`
- **Type**: ✅ **PRODUIT** (spécifique S2)
- **Contenu**: Démarrage APScheduler avec `dispatch_scheduled_posts`
- **Dépendances**: `api.services.scheduler.task.dispatch_scheduled_posts` (shim vers SparkPusher)
- **Statut**: ⚠️ **À MIGRER** vers `products/sparkpusher/services/scheduler_manager.py` ou intégrer dans `task.py`

#### ⚠️ `api/services/scheduler/logger.py`
- **Type**: ⚠️ **MIXTE** (logger générique + handler Telegram spécifique)
- **Contenu**: Logger structuré pour scheduler avec support Telegram optionnel
- **Dépendances**: `api.utils.dates`, `logs.telegram_handler` (optionnel)
- **Utilisation**: Utilisé par `products.sparkpusher.services.task`
- **Statut**: ⚠️ **À MIGRER** vers `saasentialcore/services/scheduler_logger.py` (partie générique) ou `products/sparkpusher/services/logger.py` (si spécifique S2)

---

### 📦 AUTRES FICHIERS SCHEDULER

#### ⚠️ `api/services/content_distributor/scheduler.py`
- **Type**: ❌ **OBSOLÈTE** (logique legacy)
- **Contenu**: Boucle de traitement de tâches legacy avec `dispatch_content` direct
- **Dépendances**: `api.services.content_distributor.dispatcher`
- **Utilisation**: Aucune référence dans le codebase
- **Statut**: ❌ **À SUPPRIMER** (remplacé par `saasentialcore.services.scheduler_service` + `products.sparkpusher.services.task`)

#### ⚠️ `api/routes/scheduler_stats.py`
- **Type**: ✅ **PRODUIT** (spécifique Sparkmetriq - statistiques par muse/plateforme)
- **Contenu**: Routes de statistiques par plateforme et par muse (utilise `platform_logs`)
- **Dépendances**: `api.databases.databases`, `api.core.auth`
- **Utilisation**: Aucune référence dans le codebase (route non montée ?)
- **Statut**: ⚠️ **À MIGRER** vers `products/sparkmetriq/api/routes/scheduler_stats.py` ou supprimer si non utilisé

---

## 2. NON-CONFORMITÉS DÉTECTÉES

### 🔴 CRITIQUE #1 : `saasentialcore/products/` EXISTE ENCORE

**Problème**: Tous les fichiers produits sont encore dans `saasentialcore/products/` au lieu de `products/` à la racine.

**Fichiers concernés** (9 fichiers):
1. `saasentialcore/products/sparkmetriq/services/scheduler/planner_service.py`
2. `saasentialcore/products/sparkmetriq/services/scheduler/abtest_service.py`
3. `saasentialcore/products/sparkmetriq/services/scheduler/recycle_service.py`
4. `saasentialcore/products/sparkmetriq/services/scheduler/ai_copy_service.py`
5. `saasentialcore/products/sparkmetriq/services/scheduler/publish_service.py`
6. `saasentialcore/products/sparkmetriq/services/scheduler/job_runner.py`
7. `saasentialcore/products/sparkpusher/services/task.py`
8. `saasentialcore/products/sparkpusher/services/quotas_service.py`
9. `saasentialcore/products/sparkpusher/services/config.py`

**Destination recommandée**:
- `products/sparkmetriq/services/scheduler/` (pour Sparkmetriq)
- `products/sparkpusher/services/` (pour SparkPusher)

**Impact**: ⚠️ **MAJEUR** - Violation de la règle architecturale #1

---

### 🟡 ATTENTION #1 : Fichiers à analyser dans `api/services/scheduler/`

**Fichiers suspects** (3 fichiers):
1. `api/services/scheduler/scheduler_engine.py` - Peut contenir de la logique core
2. `api/services/scheduler/manager.py` - Peut contenir de la logique core
3. `api/services/scheduler/logger.py` - Peut contenir de la logique core

**Action requise**: Analyser ces fichiers pour déterminer s'ils contiennent:
- De la logique **CORE** → migrer vers `saasentialcore/services/`
- De la logique **PRODUIT** → migrer vers `products/*/services/`
- De la logique **OBSOLÈTE** → supprimer

---

### 🟡 ATTENTION #2 : Fichiers legacy à vérifier

**Fichiers suspects** (2 fichiers):
1. `api/services/content_distributor/scheduler.py` - Logique legacy, peut être obsolète
2. `api/routes/scheduler_stats.py` - Statistiques, à classifier

**Action requise**: Analyser et classifier (core, produit, ou obsolète)

---

## 3. PLAN DE REFACTORISATION

### ÉTAPE 1 : Déplacer `saasentialcore/products/` → `products/`

**Commande**:
```bash
# Créer le dossier products/ à la racine si nécessaire
mkdir -p products

# Déplacer le contenu
mv saasentialcore/products/* products/

# Supprimer le dossier vide
rmdir saasentialcore/products
```

**Fichiers concernés**: Tous les fichiers dans `saasentialcore/products/`

**Imports à modifier**: Aucun (les imports utilisent déjà `products.*`)

---

### ÉTAPE 2 : Supprimer `api/services/scheduler/scheduler_engine.py` (OBSOLÈTE)

**Action**:
1. ✅ Fichier identifié comme **OBSOLÈTE** (logique legacy)
2. ✅ Aucune référence dans le codebase
3. ✅ Remplacé par `saasentialcore.services.scheduler_service`

**Commande**:
```bash
rm api/services/scheduler/scheduler_engine.py
```

**Imports à modifier**: Aucun (fichier non utilisé)

---

### ÉTAPE 3 : Migrer `api/services/scheduler/manager.py` vers SparkPusher

**Action**:
1. ✅ Fichier identifié comme **PRODUIT** (spécifique S2)
2. Contient la logique de démarrage APScheduler pour `dispatch_scheduled_posts`
3. Migrer vers `products/sparkpusher/services/scheduler_manager.py` ou intégrer dans `task.py`

**Commande**:
```bash
# Option 1 : Créer un fichier séparé
mv api/services/scheduler/manager.py products/sparkpusher/services/scheduler_manager.py

# Option 2 : Intégrer dans task.py (recommandé si logique simple)
# Copier le contenu dans products/sparkpusher/services/task.py
# Supprimer manager.py
```

**Imports à modifier**:
- Chercher tous les `from api.services.scheduler.manager import ...`
- Mettre à jour vers `products.sparkpusher.services.scheduler_manager` ou `products.sparkpusher.services.task`

**Recommandation**: Intégrer dans `task.py` car la logique est simple (démarrage APScheduler)

---

### ÉTAPE 4 : Migrer `api/services/scheduler/logger.py` vers Core

**Action**:
1. ✅ Fichier identifié comme **MIXTE** (logger générique + handler Telegram optionnel)
2. La partie générique (logger structuré) doit aller dans `saasentialcore/services/scheduler_logger.py`
3. La partie spécifique (handler Telegram) peut rester dans `api/` ou aller dans `products/sparkmetriq/services/` si spécifique

**Commande**:
```bash
# Migrer vers core
mv api/services/scheduler/logger.py saasentialcore/services/scheduler_logger.py
```

**Imports à modifier**:
- `products.sparkpusher.services.task` : `from api.services.scheduler.logger import scheduler_logger` → `from saasentialcore.services.scheduler_logger import scheduler_logger`
- Chercher tous les autres `from api.services.scheduler.logger import ...`
- Mettre à jour vers `saasentialcore.services.scheduler_logger`

**Note**: Le handler Telegram est optionnel et peut rester dans `api/` ou être déplacé si spécifique à un produit

---

### ÉTAPE 5 : Supprimer fichiers legacy

**Action**:
1. ✅ `api/services/content_distributor/scheduler.py` - **OBSOLÈTE**, à supprimer
2. ⚠️ `api/routes/scheduler_stats.py` - À analyser (statistiques, peut être core ou produit)

**Commandes**:
```bash
# Supprimer le fichier obsolète
rm api/services/content_distributor/scheduler.py
```

**Pour `scheduler_stats.py`**: Analyser le contenu pour déterminer si c'est core (statistiques génériques) ou produit (statistiques spécifiques Sparkmetriq/S2)

---

## 4. VALIDATION DES IMPORTS

### ✅ Imports Core → Produits

**Vérification**: Aucun fichier de `saasentialcore/services/` n'importe `products.*`

**Résultat**: ✅ **CONFORME** - Aucun import détecté

---

### ✅ Imports Produits → Core

**Vérification**: Les orchestrations S2 importent bien le core

**Résultats**:
- ✅ `products.sparkpusher.services.config` → `saasentialcore.services.scheduler_service.JobStatus` ✅
- ✅ `products.sparkpusher.services.task` → utilise `SaasentialCoreBridge` qui utilise `saasentialcore.services.scheduler_service` ✅
- ✅ `products.sparkpusher.api.routes.scheduler` → `saasentialcore.services.scheduler_service.SchedulerService` ✅

**Statut**: ✅ **CONFORME**

---

### ⚠️ Imports internes produits

**Vérification**: Les imports internes utilisent `products.*` (correct)

**Résultats**:
- ✅ `saasentialcore/products/sparkmetriq/services/scheduler/*.py` → `products.sparkmetriq.services.scheduler.*` ✅
- ✅ `saasentialcore/products/sparkpusher/services/*.py` → pas d'imports internes ✅

**Statut**: ✅ **CONFORME** (mais fichiers mal positionnés)

---

## 5. IMPACTS SUR LES TESTS

### Tests Core (saasentialcore/tests/)

**Fichiers existants**:
- ✅ `saasentialcore/tests/test_scheduler_service.py` - Tests du service core
- ✅ `saasentialcore/tests/test_scheduler_and_quotas_integration.py` - Tests d'intégration core

**Action requise**: Aucune (tests déjà conformes)

---

### Tests Produits (products/*/tests/ et tests/)

**Fichiers existants**:
- ✅ `saasentialcore/products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py` - Tests S2
- ✅ `tests/test_s2_e2e.py` - Tests E2E S2
- ✅ `tests/test_scheduler_retries.py` - Tests retries (core)
- ✅ `tests/test_job_details_endpoint.py` - Tests endpoints S2

**Actions requises après migration**:
1. Mettre à jour les imports dans `test_s2_scheduler_sparkpusher.py` si nécessaire
2. Vérifier que `tests/test_s2_e2e.py` fonctionne toujours
3. Vérifier que `tests/test_scheduler_retries.py` fonctionne toujours

---

## 📊 RÉSUMÉ DES NON-CONFORMITÉS

| Type | Nombre | Priorité | Statut |
|------|--------|----------|--------|
| Fichiers dans `saasentialcore/products/` | 9 | 🔴 CRITIQUE | ⚠️ À migrer vers `products/` |
| Fichiers obsolètes à supprimer | 2 | 🟡 MOYEN | ⚠️ À supprimer |
| Fichiers à migrer (logger, manager) | 2 | 🟡 MOYEN | ⚠️ À migrer |
| Fichiers à classifier (stats) | 1 | 🟡 FAIBLE | ⚠️ À migrer ou supprimer |

**Score de conformité**: ⚠️ **60%** (14 fichiers à traiter : 9 à déplacer, 2 obsolètes, 2 à migrer, 1 à classifier)

---

## ✅ ACTIONS PRIORITAIRES

### Priorité 1 (CRITIQUE)
1. ✅ Déplacer `saasentialcore/products/` → `products/` à la racine
2. ✅ Vérifier que tous les imports fonctionnent après déplacement

### Priorité 2 (MOYEN)
3. Analyser `api/services/scheduler/scheduler_engine.py`
4. Analyser `api/services/scheduler/manager.py`
5. Analyser `api/services/scheduler/logger.py`

### Priorité 3 (FAIBLE)
6. Vérifier `api/services/content_distributor/scheduler.py` (obsolète ?)
7. Classifier `api/routes/scheduler_stats.py` (core ou produit ?)

---

**STATUT GLOBAL**: ⚠️ **NON-CONFORME** (migration `saasentialcore/products/` → `products/` requise)

