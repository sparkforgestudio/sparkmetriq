# 🔍 AUDIT DE SÉPARATION CORE vs PRODUIT - SCHEDULER

**Date**: 2024  
**Objectif**: Vérifier et renforcer la séparation entre le scheduler générique (`saasentialcore/services/`) et les orchestrations spécifiques aux produits (`products/*/services/`).

---

## 1. CARTOGRAPHIE DU SCHEDULER CORE

### 1.1. Fonctions publiques de `saasentialcore/services/scheduler_service.py`

| Fonction | Signature | Rôle | Statut |
|----------|-----------|------|--------|
| `run_scheduled_job()` | `async (job_id, executor_callback, job_doc=None)` | Exécute un job avec retries/backoff, transitions de statut, logs | ✅ Générique |
| `create_job()` | `async (job_data: Dict) -> Dict` | Crée un nouveau job en base | ✅ Générique |
| `get_job_by_id()` | `async (job_id: str) -> Optional[Dict]` | Récupère un job par ID | ✅ Générique |
| `get_pending_jobs()` | `async (limit: int = 100) -> list` | Liste les jobs prêts à être exécutés | ✅ Générique |
| `_update_job_fields()` | `async (job_id, fields, job_doc=None)` | Met à jour des champs d'un job | ✅ Générique (privé) |
| `_to_mongo_safe()` | `static (value: Any) -> Any` | Convertit des valeurs en types compatibles MongoDB | ✅ Générique (utilitaire) |
| `_is_success()` | `(result: Any) -> bool` | Détermine si un résultat indique un succès | ✅ Générique (peut être surchargé) |
| `_extract_job_metadata()` | `(job_doc: Dict) -> Dict` | Extrait les métadonnées pour les logs | ✅ Générique (peut être surchargé) |

**Total**: 8 fonctions (6 publiques, 2 privées/utilitaires)

---

### 1.2. Usages du scheduler core dans les produits

#### ✅ **SparkPusher** (`saasentialcore/products/sparkpusher/services/task.py`)

| Fonction core utilisée | Contexte | Statut |
|------------------------|----------|--------|
| `bridge.scheduler.run_scheduled_job()` | Exécution d'un job S2 via callback `execute_s2_job` | ✅ **Conforme** |
| `bridge.scheduler.get_pending_jobs()` | Récupération des jobs prêts à être exécutés | ✅ **Conforme** |

**Verdict**: ✅ **EXCELLENT** - SparkPusher délègue correctement au core via `SaasentialCoreBridge`.

---

#### ⚠️ **SparkPusher** (`saasentialcore/products/sparkpusher/api/routes/scheduler.py`)

| Fonction core utilisée | Contexte | Statut |
|------------------------|----------|--------|
| `SchedulerService._to_mongo_safe()` | Conversion de `update_fields` et `job_doc` avant insertion/update | ⚠️ **Non-conforme** (accès direct à méthode privée) |
| Accès DB direct | `db["scheduled_tasks"].find_one()`, `update_one()`, `insert_one()` | ❌ **Non-conforme** (devrait utiliser SchedulerService) |

**Problèmes détectés** :
- **Ligne 206-209** : Accès DB direct pour récupérer un job → devrait utiliser `bridge.get_job_by_id()`
- **Ligne 271** : Accès DB direct pour update → devrait utiliser `SchedulerService._update_job_fields()` via bridge
- **Ligne 386** : Accès DB direct pour insertion → devrait utiliser `bridge.create_scheduled_job()`
- **Lignes 266, 378** : Utilisation directe de `SchedulerService._to_mongo_safe()` (méthode privée) → devrait être encapsulée dans le bridge

**Verdict**: ❌ **NON-CONFORME** - Accès DB direct au lieu d'utiliser le core.

---

#### ❌ **Sparkmetriq** (`saasentialcore/products/sparkmetriq/services/scheduler/job_runner.py`)

| Fonction core utilisée | Contexte | Statut |
|------------------------|----------|--------|
| **Aucune** | Utilise APScheduler directement | ❌ **Non-conforme** (n'utilise pas le core) |

**Problèmes détectés** :
- **Lignes 16-26** : Gestion APScheduler directe (`AsyncIOScheduler`) → devrait utiliser `SchedulerService` pour la persistance
- **Lignes 28-49** : `schedule_draft()` utilise APScheduler directement → devrait créer un job via `SchedulerService.create_job()` puis utiliser APScheduler uniquement pour le déclenchement
- **Lignes 87-99** : `_run_job()` exécute directement sans passer par `SchedulerService.run_scheduled_job()` → pas de retries/backoff standardisés
- **Lignes 101-122** : `resync_jobs()` accès DB direct (`db["scheduled_drafts"].find()`) → devrait utiliser le core

**Verdict**: ❌ **NON-CONFORME** - Sparkmetriq n'utilise pas le scheduler core, utilise APScheduler directement.

---

#### ⚠️ **Sparkmetriq** (`saasentialcore/products/sparkmetriq/services/scheduler/publish_service.py`)

| Fonction core utilisée | Contexte | Statut |
|------------------------|----------|--------|
| **Aucune** | Accès DB direct pour logs et drafts | ⚠️ **Partiellement conforme** |

**Problèmes détectés** :
- **Lignes 29, 104, 117, 163, 173, 183, 201** : Accès DB direct (`db["scheduled_drafts"]`, `db["publish_logs"]`) → spécifique Sparkmetriq (drafts), mais les logs pourraient être génériques

**Verdict**: ⚠️ **PARTIELLEMENT CONFORME** - Logique spécifique Sparkmetriq (drafts), mais certains patterns pourraient être génériques.

---

## 2. DÉTECTION DE LA LOGIQUE GÉNÉRIQUE RESTANTE

### 2.1. Blocs génériques détectés dans les services produit

#### 🔴 **CRITIQUE : Accès DB direct dans SparkPusher routes**

**Fichier**: `saasentialcore/products/sparkpusher/api/routes/scheduler.py`

| Ligne | Code | Problème | Solution proposée |
|-------|------|----------|-------------------|
| 206-209 | `db["scheduled_tasks"].find_one({"_id": job_id})` | Accès DB direct | Utiliser `bridge.get_job_by_id(job_id)` |
| 271 | `db["scheduled_tasks"].update_one(filter, {"$set": update_fields})` | Accès DB direct | Utiliser `bridge.scheduler._update_job_fields()` (via méthode publique du bridge) |
| 386 | `db["scheduled_tasks"].insert_one(safe_job_doc)` | Accès DB direct | Utiliser `bridge.create_scheduled_job()` |
| 266, 378 | `SchedulerService._to_mongo_safe()` | Accès à méthode privée | Encapsuler dans `bridge.to_mongo_safe()` ou méthode publique |

**Logique générique à extraire** :
- **Création de job** : `create_job()` existe déjà dans core, mais les routes font l'insertion directe
- **Mise à jour de job** : `_update_job_fields()` existe mais est privée, devrait être publique ou via bridge
- **Récupération de job** : `get_job_by_id()` existe, mais les routes font `find_one()` direct

**Proposition** :
```python
# Dans SaasentialCoreBridge, ajouter :
async def update_job_fields(self, job_id: str, fields: Dict[str, Any]) -> None:
    """Met à jour des champs d'un job."""
    await self.get_scheduler_service()._update_job_fields(job_id, fields)

def to_mongo_safe(self, value: Any) -> Any:
    """Convertit une valeur en types compatibles MongoDB."""
    return SchedulerService._to_mongo_safe(value)
```

---

#### 🟡 **MOYEN : Gestion APScheduler dans Sparkmetriq**

**Fichier**: `saasentialcore/products/sparkmetriq/services/scheduler/job_runner.py`

| Ligne | Code | Problème | Solution proposée |
|-------|------|----------|-------------------|
| 16-26 | `AsyncIOScheduler()` global | Scheduler APScheduler direct | Intégrer avec `SchedulerService` pour persistance |
| 28-49 | `schedule_draft()` avec APScheduler | Pas de persistance dans `scheduled_tasks` | Créer job via `SchedulerService.create_job()` puis déclencher APScheduler |
| 87-99 | `_run_job()` sans retries | Pas de retries/backoff standardisés | Utiliser `SchedulerService.run_scheduled_job()` |

**Logique générique à extraire** :
- **Intégration APScheduler + SchedulerService** : Pattern pour déclencher APScheduler depuis un job persistant
- **Resynchronisation de jobs** : Pattern pour charger les jobs depuis DB et les programmer dans APScheduler

**Proposition** :
```python
# Dans saasentialcore/services/scheduler_service.py, ajouter :
async def schedule_with_apscheduler(
    self,
    job_id: str,
    scheduled_at: datetime,
    apscheduler: AsyncIOScheduler,
    executor_callback: Callable
) -> str:
    """
    Crée un job persistant et le programme dans APScheduler.
    
    Args:
        job_id: ID du job
        scheduled_at: Date de planification
        apscheduler: Instance APScheduler
        executor_callback: Callback d'exécution
    
    Returns:
        ID du job APScheduler
    """
    # Créer le job en base
    job_data = {
        "job_id": job_id,
        "scheduled_at": scheduled_at,
        "status": JobStatus.PENDING
    }
    await self.create_job(job_data)
    
    # Programmer dans APScheduler
    trigger = DateTrigger(run_date=scheduled_at)
    apscheduler_job_id = apscheduler.add_job(
        lambda: self.run_scheduled_job(job_id, executor_callback),
        trigger=trigger,
        id=job_id,
        replace_existing=True
    )
    
    return apscheduler_job_id.id
```

---

#### 🟢 **FAIBLE : Logs de publication dans Sparkmetriq**

**Fichier**: `saasentialcore/products/sparkmetriq/services/scheduler/publish_service.py`

| Ligne | Code | Problème | Solution proposée |
|-------|------|----------|-------------------|
| 104, 163 | `db["publish_logs"].insert_one()` | Logs spécifiques Sparkmetriq | Garder spécifique (format Sparkmetriq) |

**Verdict**: ✅ **Spécifique Sparkmetriq** - Les logs de publication sont spécifiques au format Sparkmetriq (drafts, tenant_id), pas besoin d'extraire.

---

### 2.2. Résumé des blocs génériques à extraire

| Fichier produit | Bloc générique | Nouvelle fonction core proposée | Priorité |
|-----------------|----------------|--------------------------------|----------|
| `sparkpusher/api/routes/scheduler.py` | Accès DB direct pour jobs | `bridge.update_job_fields()`, `bridge.to_mongo_safe()` | 🔴 **CRITIQUE** |
| `sparkmetriq/services/scheduler/job_runner.py` | Intégration APScheduler + persistance | `SchedulerService.schedule_with_apscheduler()` | 🟡 **MOYEN** |
| `sparkmetriq/services/scheduler/job_runner.py` | Resynchronisation jobs | `SchedulerService.resync_jobs_from_db()` | 🟡 **MOYEN** |

---

## 3. CONTRÔLE DU SENS DES DÉPENDANCES

### 3.1. Vérification des imports

#### ✅ **saasentialcore/services/scheduler_service.py**

```bash
grep -r "from products\." saasentialcore/services/scheduler_service.py
# Résultat: Aucun import de products.* ✅
```

**Verdict**: ✅ **CONFORME** - Le core n'importe jamais `products.*`.

---

#### ✅ **Produits → Core**

```bash
# SparkPusher
grep -r "from saasentialcore" saasentialcore/products/sparkpusher/
# Résultat: ✅ Imports corrects (scheduler_service, JobStatus)

# Sparkmetriq
grep -r "from saasentialcore" saasentialcore/products/sparkmetriq/
# Résultat: ⚠️ Aucun import (n'utilise pas le core)
```

**Verdict**: 
- ✅ **SparkPusher** : Importe correctement le core
- ❌ **Sparkmetriq** : N'importe pas le core (n'utilise pas `SchedulerService`)

---

#### ⚠️ **Bridge → Produits (dépendance légitime)**

**Fichier**: `api/services/core/saasential_bridge.py`

| Ligne | Import | Raison | Statut |
|-------|--------|--------|--------|
| 21 | `from api.services.scheduler.quotas_service import QuotasService as SparkmetriqQuotasService` | Service spécifique Sparkmetriq pour quotas avec `UnifiedPostPayload` | ⚠️ **Acceptable** (shim) |
| 201-204 | `from api.services.observability.metrics import increment_s2_scheduler_job` | Métriques spécifiques Sparkmetriq | ⚠️ **Acceptable** (callbacks) |

**Verdict**: ⚠️ **ACCEPTABLE** - Le bridge importe des services spécifiques pour les callbacks, mais c'est une dépendance légitime (injection de dépendances).

---

### 3.2. Résumé des dépendances

| Module | Importe products.* ? | Importe saasentialcore.* ? | Statut |
|-------|---------------------|----------------------------|--------|
| `saasentialcore/services/scheduler_service.py` | ❌ Non | ✅ Oui (modèles) | ✅ **Conforme** |
| `products/sparkpusher/services/task.py` | ❌ Non | ✅ Oui (via bridge) | ✅ **Conforme** |
| `products/sparkpusher/api/routes/scheduler.py` | ❌ Non | ⚠️ Oui (direct `_to_mongo_safe`) | ⚠️ **Partiellement conforme** |
| `products/sparkmetriq/services/scheduler/job_runner.py` | ❌ Non | ❌ Non | ❌ **Non-conforme** (n'utilise pas le core) |
| `api/services/core/saasential_bridge.py` | ⚠️ Oui (shims) | ✅ Oui | ⚠️ **Acceptable** (bridge) |

**Verdict global**: ⚠️ **PARTIELLEMENT CONFORME** - Pas d'inversion de dépendances critiques, mais Sparkmetriq n'utilise pas le core.

---

## 4. PLAN D'ACTION POUR RENFORCER LA SÉPARATION

### 4.1. Actions critiques (priorité 🔴)

#### **Action 1 : Éliminer les accès DB directs dans SparkPusher routes**

**Fichier**: `saasentialcore/products/sparkpusher/api/routes/scheduler.py`

**Modifications** :

1. **Ajouter méthodes publiques dans `SaasentialCoreBridge`** :
```python
# Dans api/services/core/saasential_bridge.py

async def update_job_fields(self, job_id: str, fields: Dict[str, Any]) -> None:
    """
    Met à jour des champs d'un job.
    
    Args:
        job_id: ID du job
        fields: Dictionnaire des champs à mettre à jour
    """
    await self.get_scheduler_service()._update_job_fields(job_id, fields)

@staticmethod
def to_mongo_safe(value: Any) -> Any:
    """
    Convertit une valeur en types compatibles MongoDB.
    
    Args:
        value: Valeur à convertir
    
    Returns:
        Valeur compatible MongoDB
    """
    from saasentialcore.services.scheduler_service import SchedulerService
    return SchedulerService._to_mongo_safe(value)
```

2. **Remplacer les accès DB directs dans `sparkpusher/api/routes/scheduler.py`** :
```python
# Ligne 206-209 : Remplacer
# job = await db["scheduled_tasks"].find_one({"_id": job_id})
# Par:
job = await bridge.get_job_by_id(job_id)

# Ligne 271 : Remplacer
# await db["scheduled_tasks"].update_one(filter, {"$set": update_fields})
# Par:
await bridge.update_job_fields(job_id, update_fields)

# Ligne 386 : Remplacer
# await db["scheduled_tasks"].insert_one(safe_job_doc)
# Par:
job_id = await bridge.create_scheduled_job(
    org_id=job_doc["org_id"],
    payload=job_doc["payload"],
    scheduled_at=job_doc["scheduled_at"],
    job_id=job_doc.get("job_id"),
    **extra_fields
)

# Lignes 266, 378 : Remplacer
# safe_update_fields = SchedulerService._to_mongo_safe(update_fields)
# Par:
safe_update_fields = SaasentialCoreBridge.to_mongo_safe(update_fields)
```

**Impact**: ✅ Élimine tous les accès DB directs dans SparkPusher routes.

---

### 4.2. Actions moyennes (priorité 🟡)

#### **Action 2 : Intégrer Sparkmetriq avec SchedulerService**

**Fichier**: `saasentialcore/products/sparkmetriq/services/scheduler/job_runner.py`

**Modifications** :

1. **Ajouter méthode dans `SchedulerService`** :
```python
# Dans saasentialcore/services/scheduler_service.py

async def schedule_with_apscheduler(
    self,
    job_id: str,
    scheduled_at: datetime,
    apscheduler: AsyncIOScheduler,
    executor_callback: Callable[[Dict[str, Any]], Awaitable[Any]]
) -> str:
    """
    Crée un job persistant et le programme dans APScheduler.
    
    Cette méthode permet d'intégrer APScheduler avec la persistance
    et les retries standardisés de SchedulerService.
    
    Args:
        job_id: ID unique du job
        scheduled_at: Date de planification
        apscheduler: Instance APScheduler
        executor_callback: Callback d'exécution async
    
    Returns:
        ID du job APScheduler
    """
    from apscheduler.triggers.date import DateTrigger
    
    # Créer le job en base via le service générique
    job_data = {
        "job_id": job_id,
        "scheduled_at": scheduled_at,
        "status": JobStatus.PENDING,
        "attempt": 0
    }
    await self.create_job(job_data)
    
    # Programmer dans APScheduler avec callback qui utilise SchedulerService
    trigger = DateTrigger(run_date=scheduled_at)
    
    async def apscheduler_callback():
        """Callback APScheduler qui délègue à SchedulerService."""
        await self.run_scheduled_job(job_id, executor_callback)
    
    apscheduler_job = apscheduler.add_job(
        apscheduler_callback,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        misfire_grace_time=300
    )
    
    return apscheduler_job.id
```

2. **Adapter `job_runner.py` pour utiliser le core** :
```python
# Dans products/sparkmetriq/services/scheduler/job_runner.py

from api.services.core.saasential_bridge import SaasentialCoreBridge

_bridge = SaasentialCoreBridge()

async def schedule_draft(draft: Dict[str, Any]) -> str:
    """Programme un draft pour publication."""
    run_at = draft["scheduled_at"]
    
    if run_at <= datetime.now(timezone.utc):
        return "past_date"
    
    # Utiliser le core pour créer le job persistant
    job_id = str(draft["_id"])
    
    # Callback d'exécution spécifique Sparkmetriq
    async def execute_sparkmetriq_job(job_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un job Sparkmetriq (publication de draft)."""
        draft_id = job_doc.get("draft_id") or job_doc.get("_id")
        tenant_id = job_doc.get("tenant_id") or job_doc.get("org_id")
        return await execute_publish(str(draft_id), str(tenant_id))
    
    # Créer le job persistant et le programmer dans APScheduler
    apscheduler_job_id = await _bridge.scheduler.schedule_with_apscheduler(
        job_id=job_id,
        scheduled_at=run_at,
        apscheduler=scheduler,
        executor_callback=execute_sparkmetriq_job
    )
    
    return apscheduler_job_id
```

**Impact**: ✅ Sparkmetriq utilise le core pour la persistance et les retries, tout en gardant APScheduler pour le déclenchement.

---

#### **Action 3 : Resynchronisation de jobs**

**Ajouter méthode dans `SchedulerService`** :
```python
# Dans saasentialcore/services/scheduler_service.py

async def resync_jobs_for_apscheduler(
    self,
    apscheduler: AsyncIOScheduler,
    executor_callback: Callable[[Dict[str, Any]], Awaitable[Any]],
    filter_query: Optional[Dict[str, Any]] = None
) -> int:
    """
    Resynchronise les jobs depuis la base vers APScheduler.
    
    Utile au démarrage pour recharger les jobs planifiés.
    
    Args:
        apscheduler: Instance APScheduler
        executor_callback: Callback d'exécution
        filter_query: Filtre MongoDB optionnel pour les jobs à resynchroniser
    
    Returns:
        Nombre de jobs resynchronisés
    """
    now = self._utcnow()
    
    # Construire la requête
    query = {
        "status": JobStatus.PENDING,
        "$or": [
            {"scheduled_at": {"$gte": now}},
            {"next_run_at": {"$gte": now}}
        ]
    }
    if filter_query:
        query.update(filter_query)
    
    # Récupérer les jobs
    cursor = self.collection.find(query)
    jobs = await cursor.to_list(length=None)
    
    # Programmer chaque job dans APScheduler
    synced_count = 0
    for job_doc in jobs:
        job_id = str(job_doc.get("job_id") or job_doc.get("_id"))
        scheduled_at = job_doc.get("scheduled_at") or job_doc.get("next_run_at")
        
        if scheduled_at and scheduled_at > now:
            try:
                await self.schedule_with_apscheduler(
                    job_id=job_id,
                    scheduled_at=scheduled_at,
                    apscheduler=apscheduler,
                    executor_callback=executor_callback
                )
                synced_count += 1
            except Exception as e:
                scheduler_logger.error(
                    f"Failed to resync job {job_id}",
                    extra={"job_id": job_id, "error": str(e)}
                )
    
    return synced_count
```

**Impact**: ✅ Pattern générique pour resynchroniser les jobs au démarrage.

---

### 4.3. Tableau récapitulatif du plan d'action

| Fichier produit | Bloc générique à extraire | Nouvelle fonction core | Emplacement | Priorité |
|-----------------|---------------------------|----------------------|-------------|----------|
| `sparkpusher/api/routes/scheduler.py` | Accès DB direct (`find_one`, `update_one`, `insert_one`) | `bridge.update_job_fields()`, `bridge.to_mongo_safe()` | `api/services/core/saasential_bridge.py` | 🔴 **CRITIQUE** |
| `sparkmetriq/services/scheduler/job_runner.py` | Intégration APScheduler + persistance | `SchedulerService.schedule_with_apscheduler()` | `saasentialcore/services/scheduler_service.py` | 🟡 **MOYEN** |
| `sparkmetriq/services/scheduler/job_runner.py` | Resynchronisation jobs | `SchedulerService.resync_jobs_for_apscheduler()` | `saasentialcore/services/scheduler_service.py` | 🟡 **MOYEN** |

---

## 5. CONTRAT FINAL CORE vs PRODUIT

### 5.1. Règles architecturales

#### **`saasentialcore/services/scheduler_service.py` = Primitives génériques robustes**

**Responsabilités** :
- ✅ Exécution de jobs avec retries/backoff standardisés
- ✅ Gestion des transitions de statut (PENDING → RUNNING → SUCCESS/FAILED)
- ✅ Persistance des jobs dans MongoDB
- ✅ Logs structurés et métriques
- ✅ Intégration avec APScheduler (si nécessaire)
- ✅ Resynchronisation de jobs

**Interdictions** :
- ❌ Aucune logique métier spécifique à un produit
- ❌ Aucun import de `products.*`
- ❌ Aucune connaissance de `UnifiedPostPayload`, `DraftIn`, etc.

---

#### **`products/*/services/` = Orchestration et règles métier**

**Responsabilités** :
- ✅ Orchestration des appels au core (via `SaasentialCoreBridge`)
- ✅ Logique métier spécifique (ex: reconstruction `UnifiedPostPayload`, AB tests, recyclage)
- ✅ Callbacks d'exécution métier (ex: `execute_s2_job`, `execute_sparkmetriq_job`)
- ✅ Gestion des formats spécifiques (ex: conversion legacy, adaptation de contenu)

**Interdictions** :
- ❌ Accès DB direct pour les jobs (`scheduled_tasks`) → utiliser `SchedulerService`
- ❌ Réimplémentation de retries/backoff → utiliser `SchedulerService.run_scheduled_job()`
- ❌ Gestion manuelle des statuts → laisser `SchedulerService` gérer

---

### 5.2. Flux de dépendances cible

```
┌─────────────────────────────────────┐
│  products/sparkpusher/services/     │
│  products/sparkmetriq/services/     │
│  (Orchestration métier)              │
└──────────────┬──────────────────────┘
               │ utilise
               ▼
┌─────────────────────────────────────┐
│  api/services/core/                  │
│  saasential_bridge.py                │
│  (Bridge / Adapter)                   │
└──────────────┬──────────────────────┘
               │ délègue vers
               ▼
┌─────────────────────────────────────┐
│  saasentialcore/services/            │
│  scheduler_service.py                │
│  (Primitives génériques)              │
└─────────────────────────────────────┘
```

**Règle**: Les produits ne doivent jamais accéder directement à `SchedulerService`, toujours via `SaasentialCoreBridge`.

---

## 6. RÉSUMÉ ET RECOMMANDATIONS

### 6.1. Score de conformité actuel

| Aspect | Score | Commentaire |
|--------|-------|-------------|
| **Séparation core vs produit** | 60% | SparkPusher bon, Sparkmetriq n'utilise pas le core |
| **Accès DB directs** | 40% | SparkPusher routes accèdent directement à `scheduled_tasks` |
| **Sens des dépendances** | 90% | Pas d'inversion critique, mais Sparkmetriq ignore le core |
| **Réutilisation du core** | 50% | SparkPusher utilise bien, Sparkmetriq pas du tout |

**Score global**: ⚠️ **60% CONFORME**

---

### 6.2. Actions prioritaires

1. 🔴 **CRITIQUE** : Éliminer les accès DB directs dans `sparkpusher/api/routes/scheduler.py` (Action 1)
2. 🟡 **MOYEN** : Intégrer Sparkmetriq avec `SchedulerService` (Action 2)
3. 🟡 **MOYEN** : Ajouter resynchronisation générique (Action 3)

---

### 6.3. Bénéfices attendus

- ✅ **Robustesse** : Tous les jobs bénéficient des retries/backoff standardisés
- ✅ **Observabilité** : Logs et métriques uniformes
- ✅ **Maintenabilité** : Logique générique centralisée
- ✅ **Testabilité** : Core testable indépendamment des produits

---

**Statut**: ⚠️ **PARTIELLEMENT CONFORME** - Actions de refactorisation requises.

