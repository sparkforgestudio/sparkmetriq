# PLAN D'EXTRACTION S2 VERS SPARKPUSHER

**Date de création**: 2024  
**Statut**: ✅ Migration en cours

---

## 📋 OBJECTIF

Extraire le module S2 (Content Studio / Publish) depuis la codebase historique vers `products/sparkpusher/` en tant que produit indépendant commercialisable.

---

## 🎯 ROUTES À DÉPLACER

### Routes S2 (SparkPusher)

**Source**: `api/routes/scheduler.py`  
**Destination**: `products/sparkpusher/api/routes/scheduler.py`

Routes concernées :
- ✅ `POST /api/scheduler/posts/schedule` - Planifier un post multi-plateformes
- ✅ `GET /api/scheduler/jobs/{job_id}` - Détails d'un job
- ✅ `PATCH /api/scheduler/jobs/{job_id}/reschedule` - Replanifier un job
- ✅ `GET /api/scheduler/calendar` - Calendrier des posts

**Statut**: ✅ **MIGRÉ**

---

## 🔧 SERVICES À FACTORISER / DÉPLACER

### Services Core (saasentialcore)

**Destination**: `saasentialcore/services/`

- ✅ `scheduler_service.py` - Moteur générique de scheduling (jobs, retries, backoff)
- ✅ `quotas_service.py` - Gestion générique des quotas par organisation
- ✅ `auth_service.py` - Authentification générique
- ✅ `org_service.py` - Gestion des organisations

**Statut**: ✅ **DANS SAASENTIALCORE**

### Services S2 (SparkPusher)

**Destination**: `products/sparkpusher/services/`

- ✅ `task.py` - Exécution des jobs S2 (dispatch, payload unifié)
- ✅ `quotas_service.py` - Vérification des quotas spécifiques S2 (UnifiedPostPayload)
- ✅ `config.py` - Configuration S2 (MAX_ATTEMPTS, BACKOFF_SECONDS, JobStatus)

**Statut**: ✅ **MIGRÉ**

### Services Sparkmetriq (non-S2)

**Destination**: `products/sparkmetriq/services/scheduler/`

- ✅ `planner_service.py` - Gestion des drafts, planification hebdomadaire
- ✅ `abtest_service.py` - Tests A/B pour le contenu
- ✅ `recycle_service.py` - Recyclage intelligent de contenu
- ✅ `ai_copy_service.py` - Génération de contenu IA
- ✅ `publish_service.py` - Exécution des publications Sparkmetriq
- ✅ `job_runner.py` - Gestionnaire APScheduler pour Sparkmetriq

**Statut**: ✅ **MIGRÉ**

---

## 📦 SCHÉMAS & REPOSITORIES À MUTUALISER

### Schémas Core (saasentialcore)

**Destination**: `saasentialcore/models/schemas/`

- ✅ `job_schema.py` - Schémas génériques de jobs
- ✅ `quotas_schema.py` - Schémas génériques de quotas
- ✅ `org_schema.py` - Schémas génériques d'organisations
- ✅ `user_schema.py` - Schémas génériques d'utilisateurs

**Statut**: ✅ **DANS SAASENTIALCORE**

### Schémas S2 (SparkPusher)

**Destination**: `api/schemas/` (partagé pour l'instant)

- ✅ `payload_schema.py` - UnifiedPostPayload, MediaItem, PublishOptions
- ✅ `scheduler.py` - SchedulePostResponse, RescheduleJobRequest, etc.
- ✅ `job_details_schema.py` - JobDetails, JobPlatformStatus

**Statut**: ✅ **PARTAGÉ (à migrer vers products/sparkpusher/schemas/ si nécessaire)**

---

## 📝 ÉTAPES DE MIGRATION

### ✅ Phase 1 : Structure de base
- [x] Créer `products/sparkpusher/` à la racine
- [x] Créer `products/sparkmetriq/` à la racine
- [x] Créer la structure `api/routes/`, `services/`, `tests/`

### ✅ Phase 2 : Migration des routes S2
- [x] Déplacer routes S2 vers `products/sparkpusher/api/routes/scheduler.py`
- [x] Créer shim de compatibilité dans `api/routes/scheduler.py`
- [x] Mettre à jour `api/main.py` pour monter les routes

### ✅ Phase 3 : Migration des services S2
- [x] Déplacer `task.py` vers `products/sparkpusher/services/`
- [x] Déplacer `quotas_service.py` (S2) vers `products/sparkpusher/services/`
- [x] Déplacer `config.py` (S2) vers `products/sparkpusher/services/`
- [x] Créer shims de compatibilité dans `api/services/scheduler/`

### ✅ Phase 4 : Migration des services Sparkmetriq
- [x] Déplacer services scheduler Sparkmetriq vers `products/sparkmetriq/services/scheduler/`
- [x] Créer routes Sparkmetriq dans `products/sparkmetriq/api/routes/scheduler.py`
- [x] Créer shims de compatibilité dans `api/services/scheduler/`

### ✅ Phase 5 : Migration de `saasentialcore/products/` vers `products/`
- [x] Déplacer `saasentialcore/products/` → `products/` à la racine
- [x] Mettre à jour tous les imports `saasentialcore.products.*` → `products.*`
- [x] Mettre à jour les règles Cursor

### ⏳ Phase 6 : Nettoyage final
- [ ] Supprimer `saasentialcore/products/` (après vérification)
- [ ] Supprimer `saasentialcore/app/api/` (vide)
- [ ] Supprimer dossiers vides dans `products/sparkpusher/admin_panel/`
- [ ] Vérifier que tous les tests passent

---

## ⚠️ RISQUES IDENTIFIÉS

### Risque 1 : Imports cassés
**Mitigation**: 
- Création de shims de compatibilité dans `api/`
- Mise à jour progressive des imports
- Tests à chaque étape

### Risque 2 : Dépendances circulaires
**Mitigation**:
- `products/sparkpusher` ne doit dépendre QUE de `saasentialcore`
- `products/sparkmetriq` ne doit dépendre QUE de `saasentialcore`
- Pas de dépendance entre `sparkpusher` et `sparkmetriq`

### Risque 3 : Tests cassés
**Mitigation**:
- Relancer tous les tests après chaque étape
- Maintenir les shims jusqu'à ce que tous les tests passent
- Mettre à jour progressivement les tests pour utiliser les nouveaux chemins

---

## ✅ VALIDATION POST-MIGRATION

- [x] `products/` existe à la racine
- [ ] `saasentialcore/products/` n'existe plus
- [x] Tous les imports utilisent `products.*` (pas `saasentialcore.products.*`)
- [ ] Tous les tests passent
- [ ] Aucune référence à `saasentialcore.products` dans le codebase
- [x] `PLAN_EXTRACTION_S2_SPARKPUSHER.md` existe à la racine

---

## 📊 STATUT GLOBAL

**Progression**: 90% ✅

**Prochaines étapes**:
1. Supprimer `saasentialcore/products/` après vérification finale
2. Nettoyer les dossiers vides
3. Relancer tous les tests
4. Valider la conformité architecturale

