# ✅ REFACTOR ACTION 1 : ÉLIMINATION DES ACCÈS DB DIRECTS

**Date**: 2024  
**Objectif**: Éliminer tous les accès DB directs dans `products/sparkpusher/api/routes/scheduler.py` et les remplacer par des appels au `SchedulerService` via `SaasentialCoreBridge`.

---

## 📋 RÉSUMÉ DES MODIFICATIONS

### 1. ✅ Enrichissement de `SaasentialCoreBridge`

**Fichier**: `api/services/core/saasential_bridge.py`

#### **Nouvelles méthodes ajoutées** :

```python
async def update_job_fields(
    self,
    job_id: str,
    fields: Dict[str, Any],
    job_doc: Optional[Dict[str, Any]] = None
) -> None:
    """
    Met à jour des champs arbitraires sur un job en utilisant la logique de SchedulerService.
    
    Cette méthode encapsule toute la logique d'accès DB pour les jobs.
    Elle délègue à SchedulerService._update_job_fields() qui gère :
    - La conversion des types (Enum -> value, etc.)
    - La construction du filtre MongoDB (_id ou job_id)
    - L'opération $set
    """
    scheduler_service = self.get_scheduler_service()
    await scheduler_service._update_job_fields(job_id=job_id, fields=fields, job_doc=job_doc)

@staticmethod
def to_mongo_safe(value: Any) -> Any:
    """
    Utilitaire pour rendre une valeur Mongo-safe si nécessaire.
    
    Cette méthode délègue à SchedulerService._to_mongo_safe() qui gère :
    - Enum -> Enum.value
    - Pydantic BaseModel -> model_dump()
    - dict/list/tuple/set -> conversion récursive
    - Exception -> str(message)
    """
    from saasentialcore.services.scheduler_service import SchedulerService
    return SchedulerService._to_mongo_safe(value)
```

**Méthodes déjà existantes utilisées** :
- ✅ `get_job_by_id()` - Déjà présente (ligne 324)
- ✅ `create_scheduled_job()` - Déjà présente (ligne 244)

---

### 2. ✅ Amélioration de `SchedulerService.get_job_by_id()`

**Fichier**: `saasentialcore/services/scheduler_service.py`

**Modification** : Amélioration pour gérer plusieurs formats d'ID :

```python
async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un job par son ID.

    Supporte plusieurs formats d'ID :
    - ObjectId MongoDB (_id)
    - job_id (string UUID)
    """
    from bson import ObjectId
    
    # Essayer d'abord avec _id (ObjectId ou string)
    try:
        oid = ObjectId(job_id)
        job = await self.collection.find_one({"_id": oid})
        if job:
            return job
    except Exception:
        pass
    
    # Essayer avec job_id (string UUID)
    job = await self.collection.find_one({"job_id": job_id})
    if job:
        return job
    
    # Essayer avec _id comme string (fallback)
    job = await self.collection.find_one({"_id": job_id})
    return job
```

---

### 3. ✅ Refactorisation de `products/sparkpusher/api/routes/scheduler.py`

#### **Modification 1** : `get_job_details()` - Récupération de job

**AVANT** :
```python
repo = JobsRepository()
job = await repo.get_job(job_id)
```

**APRÈS** :
```python
# ✅ Utiliser le bridge pour récupérer le job
bridge = SaasentialCoreBridge()
job = await bridge.get_job_by_id(job_id)
```

---

#### **Modification 2** : `reschedule_job()` - Récupération et mise à jour de job

**AVANT** :
```python
# Récupérer le job
db = get_core_db()
try:
    job = await db["scheduled_tasks"].find_one({"_id": job_id})
except Exception:
    job = await db["scheduled_tasks"].find_one({"job_id": job_id})

# ...

# Convertir les champs en types compatibles MongoDB
from saasentialcore.services.scheduler_service import SchedulerService
safe_update_fields = SchedulerService._to_mongo_safe(update_fields)

# Effectuer la mise à jour
db = get_core_db()
await db["scheduled_tasks"].update_one(
    {"_id": job.get("_id")},
    {"$set": safe_update_fields}
)
```

**APRÈS** :
```python
# ✅ Utiliser le bridge pour récupérer le job
bridge = SaasentialCoreBridge()
job = await bridge.get_job_by_id(job_id)

# ...

# ✅ Utiliser le bridge pour mettre à jour le job
# Le bridge gère automatiquement la conversion MongoDB-safe et l'opération $set
await bridge.update_job_fields(job_id=job_id, fields=update_fields, job_doc=job)
```

---

#### **Modification 3** : `schedule_post()` - Création de job

**AVANT** :
```python
# Stocker le payload dans scheduled_tasks avec structure complète
job_doc = {
    "_id": payload.job_id,
    "job_id": payload.job_id,
    "org_id": payload.org_id,
    # ... tous les champs
}

# Convertir le document en types compatibles MongoDB
from saasentialcore.services.scheduler_service import SchedulerService
safe_job_doc = SchedulerService._to_mongo_safe(job_doc)
safe_job_doc = jsonable_encoder(safe_job_doc)

# Insérer le job dans la base
db = get_core_db()
await db["scheduled_tasks"].insert_one(safe_job_doc)
```

**APRÈS** :
```python
# ✅ Utiliser le bridge pour créer le job
# Le bridge gère automatiquement la conversion MongoDB-safe et l'insertion
created_job_id = await bridge.create_scheduled_job(
    org_id=payload.org_id,
    payload=payload.model_dump(),
    scheduled_at=earliest_publish_at if earliest_publish_at else datetime.now(timezone.utc),
    job_id=payload.job_id,
    max_attempts=MAX_ATTEMPTS,
    muse_id=payload.muse_id,
    created_by_user_id=payload.created_by_user_id,
    dispatch_results=dispatch_results
)
```

---

### 4. ✅ Centralisation du logger

**Fichier**: `saasentialcore/products/sparkpusher/services/task.py`

**AVANT** :
```python
from api.services.scheduler.logger import scheduler_logger
```

**APRÈS** :
```python
from saasentialcore.services.scheduler_service import scheduler_logger
```

**Raison** : Le logger est défini dans `SchedulerService` (ligne 39), il est donc cohérent de l'utiliser directement depuis le core plutôt que depuis un module shim.

---

### 5. ✅ Nettoyage des imports

**Fichier**: `saasentialcore/products/sparkpusher/api/routes/scheduler.py`

**Imports supprimés** :
- ❌ `from api.databases.databases import get_core_db` (plus utilisé)
- ❌ `from api.repositories.jobs_repository import JobsRepository` (plus utilisé)
- ❌ `from fastapi.encoders import jsonable_encoder` (plus utilisé)

**Imports conservés** :
- ✅ `from api.services.core.saasential_bridge import SaasentialCoreBridge` (utilisé partout)

---

## 📊 RÉSULTAT FINAL

### ✅ Accès DB directs éliminés

| Endpoint | Avant | Après | Statut |
|----------|-------|-------|--------|
| `GET /jobs/{job_id}` | `JobsRepository.get_job()` | `bridge.get_job_by_id()` | ✅ **Conforme** |
| `PATCH /jobs/{job_id}/reschedule` | `db["scheduled_tasks"].find_one()` + `update_one()` | `bridge.get_job_by_id()` + `bridge.update_job_fields()` | ✅ **Conforme** |
| `POST /posts/schedule` | `db["scheduled_tasks"].insert_one()` | `bridge.create_scheduled_job()` | ✅ **Conforme** |

### ✅ Méthodes du bridge utilisées

- ✅ `bridge.get_job_by_id(job_id)` - 2 utilisations
- ✅ `bridge.update_job_fields(job_id, fields, job_doc)` - 1 utilisation
- ✅ `bridge.create_scheduled_job(...)` - 1 utilisation
- ✅ `bridge.check_quotas_before_scheduling(...)` - Déjà utilisé
- ✅ `bridge.increment_scheduled_on_create(...)` - Déjà utilisé

### ✅ Vérification de `task.py`

**Fichier**: `saasentialcore/products/sparkpusher/services/task.py`

- ✅ `dispatch_scheduled_posts()` utilise `bridge.scheduler.get_pending_jobs()` - **Conforme**
- ✅ `run_scheduled_job()` délègue à `bridge.scheduler.run_scheduled_job()` - **Conforme**
- ✅ Aucun accès DB direct détecté - **Conforme**

---

## 🎯 CONFORMITÉ ARCHITECTURALE

### ✅ Avant (Non-conforme)

```
products/sparkpusher/api/routes/scheduler.py
    ↓ (accès DB direct)
db["scheduled_tasks"].find_one()
db["scheduled_tasks"].update_one()
db["scheduled_tasks"].insert_one()
```

### ✅ Après (Conforme)

```
products/sparkpusher/api/routes/scheduler.py
    ↓ (via bridge)
SaasentialCoreBridge
    ↓ (délègue vers)
SchedulerService (core générique)
    ↓ (accès DB encapsulé)
db["scheduled_tasks"]
```

---

## 📝 EXEMPLE CONCRET : `reschedule_job()`

### **AVANT** (Non-conforme)

```python
@router.patch("/jobs/{job_id}/reschedule")
async def reschedule_job(job_id: str, body: RescheduleJobRequest, ...):
    # ❌ Accès DB direct
    db = get_core_db()
    try:
        job = await db["scheduled_tasks"].find_one({"_id": job_id})
    except Exception:
        job = await db["scheduled_tasks"].find_one({"job_id": job_id})
    
    # ... logique métier ...
    
    # ❌ Conversion manuelle + accès DB direct
    from saasentialcore.services.scheduler_service import SchedulerService
    safe_update_fields = SchedulerService._to_mongo_safe(update_fields)
    
    db = get_core_db()
    await db["scheduled_tasks"].update_one(
        {"_id": job.get("_id")},
        {"$set": safe_update_fields}
    )
```

### **APRÈS** (Conforme)

```python
@router.patch("/jobs/{job_id}/reschedule")
async def reschedule_job(job_id: str, body: RescheduleJobRequest, ...):
    # ✅ Utiliser le bridge pour récupérer le job
    bridge = SaasentialCoreBridge()
    job = await bridge.get_job_by_id(job_id)
    
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # ... logique métier ...
    
    # ✅ Utiliser le bridge pour mettre à jour le job
    # Le bridge gère automatiquement la conversion MongoDB-safe et l'opération $set
    await bridge.update_job_fields(job_id=job_id, fields=update_fields, job_doc=job)
```

---

## ✅ VALIDATION

### Checklist de conformité

- [x] ✅ Tous les accès DB directs éliminés dans `products/sparkpusher/api/routes/scheduler.py`
- [x] ✅ Toutes les opérations passent par `SaasentialCoreBridge`
- [x] ✅ `task.py` vérifié (déjà conforme)
- [x] ✅ Logger centralisé dans `SchedulerService`
- [x] ✅ Imports inutiles supprimés
- [x] ✅ `get_job_by_id()` amélioré pour gérer ObjectId et job_id
- [x] ✅ Aucune erreur de linter

---

## 🎉 RÉSULTAT

**ACTION 1 TERMINÉE AVEC SUCCÈS** ✅

- **Fichiers modifiés** : 3
  - `api/services/core/saasential_bridge.py` (enrichi)
  - `saasentialcore/services/scheduler_service.py` (amélioré)
  - `saasentialcore/products/sparkpusher/api/routes/scheduler.py` (refactorisé)
  - `saasentialcore/products/sparkpusher/services/task.py` (logger centralisé)

- **Accès DB directs éliminés** : 4
  - `find_one()` → `bridge.get_job_by_id()` (2 occurrences)
  - `update_one()` → `bridge.update_job_fields()` (1 occurrence)
  - `insert_one()` → `bridge.create_scheduled_job()` (1 occurrence)

- **Conformité architecturale** : ✅ **100% CONFORME**

---

**STATUT**: ✅ **ACTION 1 COMPLÉTÉE**

