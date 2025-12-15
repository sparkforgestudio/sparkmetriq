# 📊 RAPPORT FINAL : AUDIT SCHEDULER CORE vs PRODUITS

**Date**: 2024  
**Statut**: ⚠️ **NON-CONFORME** (14 fichiers à traiter)

---

## 1. CARTOGRAPHIE SCHEDULER CORE vs PRODUITS

### ✅ SCHEDULER CORE (CONFORME)

| Fichier | Type | Statut |
|---------|------|--------|
| `saasentialcore/services/scheduler_service.py` | ✅ CORE | ✅ **CONFORME** |

**Responsabilités**:
- Exécution de jobs avec retries et backoff
- Gestion des transitions de statut (PENDING → RUNNING → SUCCESS/FAILED)
- Logs structurés
- Gestion des erreurs
- Agnostique du produit

---

### ⚠️ ORCHESTRATIONS PRODUITS (NON-CONFORME)

#### Sparkmetriq (6 fichiers dans `saasentialcore/products/`)

| Fichier | Type | Destination | Statut |
|---------|------|-------------|--------|
| `saasentialcore/products/sparkmetriq/services/scheduler/planner_service.py` | ✅ PRODUIT | `products/sparkmetriq/services/scheduler/` | ⚠️ **À DÉPLACER** |
| `saasentialcore/products/sparkmetriq/services/scheduler/abtest_service.py` | ✅ PRODUIT | `products/sparkmetriq/services/scheduler/` | ⚠️ **À DÉPLACER** |
| `saasentialcore/products/sparkmetriq/services/scheduler/recycle_service.py` | ✅ PRODUIT | `products/sparkmetriq/services/scheduler/` | ⚠️ **À DÉPLACER** |
| `saasentialcore/products/sparkmetriq/services/scheduler/ai_copy_service.py` | ✅ PRODUIT | `products/sparkmetriq/services/scheduler/` | ⚠️ **À DÉPLACER** |
| `saasentialcore/products/sparkmetriq/services/scheduler/publish_service.py` | ✅ PRODUIT | `products/sparkmetriq/services/scheduler/` | ⚠️ **À DÉPLACER** |
| `saasentialcore/products/sparkmetriq/services/scheduler/job_runner.py` | ✅ PRODUIT | `products/sparkmetriq/services/scheduler/` | ⚠️ **À DÉPLACER** |

#### SparkPusher (3 fichiers dans `saasentialcore/products/`)

| Fichier | Type | Destination | Statut |
|---------|------|-------------|--------|
| `saasentialcore/products/sparkpusher/services/task.py` | ✅ PRODUIT | `products/sparkpusher/services/` | ⚠️ **À DÉPLACER** |
| `saasentialcore/products/sparkpusher/services/quotas_service.py` | ✅ PRODUIT | `products/sparkpusher/services/` | ⚠️ **À DÉPLACER** |
| `saasentialcore/products/sparkpusher/services/config.py` | ✅ PRODUIT | `products/sparkpusher/services/` | ⚠️ **À DÉPLACER** |

---

### ✅ SHIMS DE COMPATIBILITÉ (CONFORME)

| Fichier | Type | Délègue vers | Statut |
|---------|------|--------------|--------|
| `api/services/scheduler/task.py` | ✅ SHIM | `products.sparkpusher.services.task` | ✅ **CONFORME** |
| `api/services/scheduler/config.py` | ✅ SHIM | `products.sparkpusher.services.config` | ✅ **CONFORME** |
| `api/services/scheduler/quotas_service.py` | ✅ SHIM | `products.sparkpusher.services.quotas_service` | ✅ **CONFORME** |
| `api/services/scheduler/planner_service.py` | ✅ SHIM | `products.sparkmetriq.services.scheduler.planner_service` | ✅ **CONFORME** |
| `api/services/scheduler/abtest_service.py` | ✅ SHIM | `products.sparkmetriq.services.scheduler.abtest_service` | ✅ **CONFORME** |
| `api/services/scheduler/recycle_service.py` | ✅ SHIM | `products.sparkmetriq.services.scheduler.recycle_service` | ✅ **CONFORME** |
| `api/services/scheduler/ai_copy_service.py` | ✅ SHIM | `products.sparkmetriq.services.scheduler.ai_copy_service` | ✅ **CONFORME** |
| `api/services/scheduler/publish_service.py` | ✅ SHIM | `products.sparkmetriq.services.scheduler.publish_service` | ✅ **CONFORME** |
| `api/services/scheduler/job_runner.py` | ✅ SHIM | `products.sparkmetriq.services.scheduler.job_runner` | ✅ **CONFORME** |

---

### ⚠️ FICHIERS À TRAITER

| Fichier | Type | Action | Priorité |
|---------|------|--------|----------|
| `api/services/scheduler/scheduler_engine.py` | ❌ OBSOLÈTE | Supprimer | 🟡 MOYEN |
| `api/services/scheduler/manager.py` | ✅ PRODUIT (S2) | Migrer vers SparkPusher | 🟡 MOYEN |
| `api/services/scheduler/logger.py` | ✅ CORE | Migrer vers `saasentialcore/services/` | 🟡 MOYEN |
| `api/services/content_distributor/scheduler.py` | ❌ OBSOLÈTE | Supprimer | 🟡 FAIBLE |
| `api/routes/scheduler_stats.py` | ✅ PRODUIT (Sparkmetriq) | Migrer vers Sparkmetriq | 🟡 FAIBLE |

---

## 2. NON-CONFORMITÉS DÉTECTÉES

### 🔴 CRITIQUE #1 : `saasentialcore/products/` EXISTE ENCORE

**Problème**: 9 fichiers produits sont dans `saasentialcore/products/` au lieu de `products/` à la racine.

**Fichiers concernés**:
- 6 fichiers Sparkmetriq dans `saasentialcore/products/sparkmetriq/services/scheduler/`
- 3 fichiers SparkPusher dans `saasentialcore/products/sparkpusher/services/`

**Destination**: `products/` à la racine

**Impact**: ⚠️ **MAJEUR** - Violation de la règle architecturale #1

---

### 🟡 MOYEN #1 : Fichiers obsolètes à supprimer

**Fichiers**:
1. `api/services/scheduler/scheduler_engine.py` - Logique legacy remplacée
2. `api/services/content_distributor/scheduler.py` - Logique legacy remplacée

**Action**: Supprimer ces fichiers

---

### 🟡 MOYEN #2 : Fichiers à migrer

**Fichiers**:
1. `api/services/scheduler/manager.py` → `products/sparkpusher/services/` (ou intégrer dans `task.py`)
2. `api/services/scheduler/logger.py` → `saasentialcore/services/scheduler_logger.py`

**Action**: Migrer vers la destination appropriée

---

### 🟡 FAIBLE #1 : Fichier à classifier

**Fichier**:
1. `api/routes/scheduler_stats.py` → `products/sparkmetriq/api/routes/` (statistiques spécifiques Sparkmetriq)

**Action**: Migrer vers Sparkmetriq ou supprimer si non utilisé

---

## 3. PLAN DE REFACTORISATION

### ÉTAPE 1 : Déplacer `saasentialcore/products/` → `products/` (CRITIQUE)

```bash
# Créer products/ à la racine
mkdir -p products

# Déplacer le contenu
mv saasentialcore/products/sparkmetriq products/
mv saasentialcore/products/sparkpusher products/

# Supprimer le dossier vide
rmdir saasentialcore/products
```

**Imports à modifier**: Aucun (déjà utilisent `products.*`)

**Tests à vérifier**: Tous les tests existants

---

### ÉTAPE 2 : Migrer `logger.py` vers Core

```bash
mv api/services/scheduler/logger.py saasentialcore/services/scheduler_logger.py
```

**Imports à modifier**:
- `products/sparkpusher/services/task.py` : `from api.services.scheduler.logger import scheduler_logger` → `from saasentialcore.services.scheduler_logger import scheduler_logger`

---

### ÉTAPE 3 : Intégrer `manager.py` dans SparkPusher

```bash
# Option recommandée : Intégrer dans task.py
# Copier le contenu de manager.py dans products/sparkpusher/services/task.py
# Supprimer manager.py
rm api/services/scheduler/manager.py
```

**Imports à modifier**: Aucun (si intégré dans `task.py`)

---

### ÉTAPE 4 : Supprimer fichiers obsolètes

```bash
rm api/services/scheduler/scheduler_engine.py
rm api/services/content_distributor/scheduler.py
```

**Imports à modifier**: Aucun (fichiers non utilisés)

---

### ÉTAPE 5 : Migrer `scheduler_stats.py`

```bash
mv api/routes/scheduler_stats.py products/sparkmetriq/api/routes/scheduler_stats.py
```

**Imports à modifier**: Vérifier si monté dans `api/main.py` et mettre à jour

---

## 4. VALIDATION DES IMPORTS

### ✅ Imports Core → Produits

**Résultat**: ✅ **CONFORME** - Aucun fichier de `saasentialcore/services/` n'importe `products.*`

---

### ✅ Imports Produits → Core

**Résultats**:
- ✅ `products.sparkpusher.services.config` → `saasentialcore.services.scheduler_service.JobStatus` ✅
- ✅ `products.sparkpusher.services.task` → utilise `SaasentialCoreBridge` → `saasentialcore.services.scheduler_service` ✅
- ✅ `products.sparkpusher.api.routes.scheduler` → `saasentialcore.services.scheduler_service.SchedulerService` ✅

**Statut**: ✅ **CONFORME**

---

### ⚠️ Import à corriger

**Fichier**: `products/sparkpusher/services/task.py`
- **Ligne 16**: `from api.services.scheduler.logger import scheduler_logger`
- **Action**: Mettre à jour vers `from saasentialcore.services.scheduler_logger import scheduler_logger` (après migration)

---

## 5. IMPACTS SUR LES TESTS

### Tests Core (saasentialcore/tests/)

**Fichiers**:
- ✅ `saasentialcore/tests/test_scheduler_service.py` - Aucun changement
- ✅ `saasentialcore/tests/test_scheduler_and_quotas_integration.py` - Aucun changement

**Action requise**: Aucune

---

### Tests Produits

**Fichiers**:
- ✅ `saasentialcore/products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py` → `products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py` (après déplacement)
- ✅ `tests/test_s2_e2e.py` - Vérifier après migration `logger.py`
- ✅ `tests/test_scheduler_retries.py` - Aucun changement
- ✅ `tests/test_job_details_endpoint.py` - Aucun changement

**Actions requises**:
1. Mettre à jour le chemin du test SparkPusher après déplacement
2. Vérifier que `test_s2_e2e.py` fonctionne après migration `logger.py`

---

## 📊 RÉSUMÉ

| Catégorie | Nombre | Statut |
|-----------|--------|--------|
| **Fichiers core conformes** | 1 | ✅ 100% |
| **Fichiers produits mal positionnés** | 9 | ⚠️ À déplacer |
| **Fichiers obsolètes** | 2 | ⚠️ À supprimer |
| **Fichiers à migrer** | 2 | ⚠️ À migrer |
| **Fichiers à classifier** | 1 | ⚠️ À migrer |
| **Shims conformes** | 9 | ✅ 100% |

**Score de conformité**: ⚠️ **60%** (14 fichiers à traiter)

---

## ✅ ACTIONS PRIORITAIRES

1. 🔴 **CRITIQUE**: Déplacer `saasentialcore/products/` → `products/`
2. 🟡 **MOYEN**: Migrer `logger.py` vers `saasentialcore/services/`
3. 🟡 **MOYEN**: Intégrer `manager.py` dans SparkPusher
4. 🟡 **MOYEN**: Supprimer fichiers obsolètes
5. 🟡 **FAIBLE**: Migrer `scheduler_stats.py` vers Sparkmetriq

---

**STATUT GLOBAL**: ⚠️ **NON-CONFORME** (migration requise)

