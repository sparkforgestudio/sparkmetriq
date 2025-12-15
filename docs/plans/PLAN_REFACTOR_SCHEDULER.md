# 🔧 PLAN DE REFACTORISATION SCHEDULER

**Date**: 2024  
**Objectif**: Corriger toutes les non-conformités de séparation core vs produits

---

## 📋 RÉSUMÉ DES ACTIONS

| Action | Fichiers | Priorité | Statut |
|--------|----------|----------|--------|
| Déplacer `saasentialcore/products/` → `products/` | 9 fichiers | 🔴 CRITIQUE | ⏳ En attente |
| Supprimer `scheduler_engine.py` (obsolète) | 1 fichier | 🟡 MOYEN | ⏳ En attente |
| Migrer `manager.py` vers SparkPusher | 1 fichier | 🟡 MOYEN | ⏳ En attente |
| Migrer `logger.py` vers Core | 1 fichier | 🟡 MOYEN | ⏳ En attente |
| Supprimer `content_distributor/scheduler.py` (obsolète) | 1 fichier | 🟡 FAIBLE | ⏳ En attente |
| Analyser `scheduler_stats.py` | 1 fichier | 🟡 FAIBLE | ⏳ En attente |

---

## 🔴 PRIORITÉ 1 : DÉPLACER `saasentialcore/products/` → `products/`

### Fichiers concernés (9 fichiers)

**Sparkmetriq (6 fichiers)**:
1. `saasentialcore/products/sparkmetriq/services/scheduler/planner_service.py`
2. `saasentialcore/products/sparkmetriq/services/scheduler/abtest_service.py`
3. `saasentialcore/products/sparkmetriq/services/scheduler/recycle_service.py`
4. `saasentialcore/products/sparkmetriq/services/scheduler/ai_copy_service.py`
5. `saasentialcore/products/sparkmetriq/services/scheduler/publish_service.py`
6. `saasentialcore/products/sparkmetriq/services/scheduler/job_runner.py`

**SparkPusher (3 fichiers)**:
7. `saasentialcore/products/sparkpusher/services/task.py`
8. `saasentialcore/products/sparkpusher/services/quotas_service.py`
9. `saasentialcore/products/sparkpusher/services/config.py`

### Commandes de déplacement

```bash
# Créer le dossier products/ à la racine si nécessaire
mkdir -p products

# Déplacer le contenu complet
mv saasentialcore/products/sparkmetriq products/
mv saasentialcore/products/sparkpusher products/

# Supprimer le dossier vide
rmdir saasentialcore/products
```

### Imports à modifier

**Aucun import à modifier** - Les imports utilisent déjà `products.*` :
- ✅ `from products.sparkmetriq.services.scheduler.planner_service import ...`
- ✅ `from products.sparkpusher.services.task import ...`

### Tests à vérifier

- ✅ `saasentialcore/products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py` → `products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py`
- ✅ `tests/test_s2_e2e.py` (imports déjà corrects)
- ✅ `tests/test_job_details_endpoint.py` (imports déjà corrects)

---

## 🟡 PRIORITÉ 2 : NETTOYER FICHIERS OBSOLÈTES

### Action 1 : Supprimer `api/services/scheduler/scheduler_engine.py`

**Raison**: Fichier obsolète, logique legacy remplacée par `saasentialcore.services.scheduler_service`

**Commande**:
```bash
rm api/services/scheduler/scheduler_engine.py
```

**Imports à modifier**: Aucun (fichier non utilisé)

---

### Action 2 : Supprimer `api/services/content_distributor/scheduler.py`

**Raison**: Fichier obsolète, logique legacy remplacée par `saasentialcore.services.scheduler_service` + `products.sparkpusher.services.task`

**Commande**:
```bash
rm api/services/content_distributor/scheduler.py
```

**Imports à modifier**: Aucun (fichier non utilisé)

---

## 🟡 PRIORITÉ 3 : MIGRER FICHIERS MIXTES

### Action 1 : Migrer `api/services/scheduler/manager.py` vers SparkPusher

**Raison**: Contient la logique de démarrage APScheduler pour `dispatch_scheduled_posts` (spécifique S2)

**Option recommandée**: Intégrer dans `products/sparkpusher/services/task.py`

**Commande**:
```bash
# Lire le contenu de manager.py
cat api/services/scheduler/manager.py

# Ajouter le contenu dans products/sparkpusher/services/task.py
# (ajouter les fonctions start_scheduler, etc.)

# Supprimer manager.py
rm api/services/scheduler/manager.py
```

**Imports à modifier**:
- Chercher `from api.services.scheduler.manager import ...`
- Remplacer par `from products.sparkpusher.services.task import start_scheduler, ...`

---

### Action 2 : Migrer `api/services/scheduler/logger.py` vers Core

**Raison**: Logger structuré générique (utilisable par tous les produits)

**Commande**:
```bash
mv api/services/scheduler/logger.py saasentialcore/services/scheduler_logger.py
```

**Imports à modifier**:
- `products/sparkpusher/services/task.py` : `from api.services.scheduler.logger import scheduler_logger` → `from saasentialcore.services.scheduler_logger import scheduler_logger`
- Chercher tous les autres `from api.services.scheduler.logger import ...`
- Mettre à jour vers `saasentialcore.services.scheduler_logger`

**Note**: Le handler Telegram est optionnel et peut rester dans `api/` ou être déplacé si spécifique

---

## 🟡 PRIORITÉ 4 : MIGRER `api/routes/scheduler_stats.py`

**Action**: Fichier identifié comme **PRODUIT** (statistiques spécifiques Sparkmetriq)

**Commande**:
```bash
# Migrer vers Sparkmetriq
mv api/routes/scheduler_stats.py products/sparkmetriq/api/routes/scheduler_stats.py
```

**Imports à modifier**:
- Vérifier si la route est montée dans `api/main.py`
- Si oui, mettre à jour l'import ou monter depuis `products/sparkmetriq/api/routes/scheduler_stats`

**Alternative**: Si la route n'est pas utilisée, supprimer le fichier

---

## ✅ VALIDATION POST-REFACTOR

### Vérifications à effectuer

1. ✅ `products/` existe à la racine
2. ✅ `saasentialcore/products/` n'existe plus
3. ✅ Tous les imports utilisent `products.*` (pas `saasentialcore.products.*`)
4. ✅ Aucun fichier obsolète dans `api/services/scheduler/`
5. ✅ `logger.py` dans `saasentialcore/services/`
6. ✅ Tous les tests passent

### Tests à relancer

```bash
# Tests core
pytest saasentialcore/tests/test_scheduler_service.py -v
pytest saasentialcore/tests/test_scheduler_and_quotas_integration.py -v

# Tests produits
pytest products/sparkpusher/tests/test_s2_scheduler_sparkpusher.py -v
pytest tests/test_s2_e2e.py -v
pytest tests/test_scheduler_retries.py -v
pytest tests/test_job_details_endpoint.py -v
```

---

## 📊 ORDRE D'EXÉCUTION RECOMMANDÉ

1. **Étape 1** : Déplacer `saasentialcore/products/` → `products/` (CRITIQUE)
2. **Étape 2** : Migrer `logger.py` → `saasentialcore/services/scheduler_logger.py`
3. **Étape 3** : Intégrer `manager.py` dans `products/sparkpusher/services/task.py`
4. **Étape 4** : Supprimer fichiers obsolètes (`scheduler_engine.py`, `content_distributor/scheduler.py`)
5. **Étape 5** : Analyser et classifier `scheduler_stats.py`
6. **Étape 6** : Relancer tous les tests
7. **Étape 7** : Vérifier la conformité architecturale

---

**STATUT**: ⏳ **EN ATTENTE D'EXÉCUTION**

