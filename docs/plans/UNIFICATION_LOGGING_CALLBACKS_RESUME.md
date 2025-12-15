# ✅ UNIFICATION LOGGING ET CALLBACKS SCHEDULER

**Date**: 2024  
**Objectif**: Unifier le logging et renforcer les callbacks (metrics, on_success) pour une observabilité SRE complète.

---

## 📋 RÉSUMÉ DES MODIFICATIONS

### 1. ✅ Centralisation du Logger

**Fichier** : `saasentialcore/services/scheduler_service.py`

#### **Stratégie adoptée** : Logger unique dans le core

**AVANT** :
- `saasentialcore/services/scheduler_service.py` : `scheduler_logger = logging.getLogger("scheduler")`
- `api/services/scheduler/logger.py` : `scheduler_logger = logging.getLogger("scheduler")` (redondant)
- `products/sparkpusher/services/task.py` : Import depuis le core (déjà corrigé)

**APRÈS** :
- ✅ **Logger unique** : `saasentialcore/services/scheduler_service.py`
- ✅ **Suppression** : `api/services/scheduler/logger.py` (redondant)
- ✅ **Support handlers optionnels** : Handler Telegram ajouté dans le core si disponible

**Code** :
```python
# Logger structuré pour le scheduler (centralisé)
# Ce logger est utilisé par tous les modules du scheduler (core et produits)
scheduler_logger = logging.getLogger("scheduler")
scheduler_logger.setLevel(logging.INFO)

# Configuration du logger si aucun handler n'est déjà configuré
if not scheduler_logger.handlers:
    # Handler console par défaut
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [scheduler] %(message)s")
    handler.setFormatter(formatter)
    scheduler_logger.addHandler(handler)
    
    # Handler Telegram optionnel (si disponible)
    try:
        from logs.telegram_handler import TelegramLogHandler
        telegram_handler = TelegramLogHandler()
        telegram_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        telegram_handler.setFormatter(telegram_formatter)
        scheduler_logger.addHandler(telegram_handler)
    except ImportError:
        pass
```

**Imports** :
- ✅ `products/sparkpusher/services/task.py` : `from saasentialcore.services.scheduler_service import scheduler_logger`
- ✅ `products/sparkmetriq/services/scheduler/job_runner.py` : `from saasentialcore.services.scheduler_service import scheduler_logger`

---

### 2. ✅ Renforcement de `metrics_callback`

**Fichier** : `saasentialcore/services/scheduler_service.py`

#### **Appels de `metrics_callback`** :

**AVANT** :
- ✅ Appelé lors de SUCCESS (ligne 256-257)
- ✅ Appelé lors de FAILED (ligne 297-298)
- ❌ **Manquant** : Appel lors de RUNNING

**APRÈS** :
- ✅ Appelé lors de RUNNING (ajouté)
- ✅ Appelé lors de SUCCESS
- ✅ Appelé lors de FAILED

**Code ajouté** :
```python
# Log de début
scheduler_logger.info(
    f"Starting job {job_id} (attempt {attempt}/{self.max_attempts})",
    extra={...}
)

# ✅ Métriques : job démarré (RUNNING)
if self.metrics_callback:
    self.metrics_callback(org_id, "RUNNING", metadata)

# Mettre à jour le statut à RUNNING
await self._update_job_fields(...)
```

**Signature** :
```python
metrics_callback(org_id: str, status: str, metadata: Dict[str, Any]) -> None
```

**Implémentation dans le bridge** :
```python
def metrics_callback(org_id: str, status: str, metadata: Dict[str, Any]) -> None:
    """Publie les métriques spécifiques à Sparkmetriq/S2."""
    platforms = metadata.get("platforms", [])
    increment_s2_scheduler_job(org_id=org_id, status=status, platforms=platforms)
    if status == "FAILED":
        increment_s2_scheduler_failure(org_id=org_id, platforms=platforms)
```

**Métriques publiées** :
- `scheduler.job.running` : Job démarré
- `scheduler.job.success` : Job réussi
- `scheduler.job.failed` : Job échoué définitivement

---

### 3. ✅ Enrichissement de `on_success_callback` pour S2

**Fichier** : `api/services/core/saasential_bridge.py`

#### **Implémentation enrichie** :

**AVANT** :
```python
async def on_success_callback(org_id: str, job_data: Dict[str, Any]) -> None:
    """Met à jour les quotas après un succès via le bridge."""
    await self.decrement_scheduled_on_success(org_id)
    await self.increment_published_today(org_id, delta=1)
```

**APRÈS** :
```python
async def on_success_callback(org_id: str, job_data: Dict[str, Any]) -> None:
    """
    Callback appelé après un succès de publication S2.
    
    Actions :
    1. Met à jour les quotas (décrémente scheduled_posts, incrémente published_today)
    2. Enregistre l'historique de publication dans dispatch_results (déjà dans job_data)
    3. Log structuré de succès avec détails par plateforme
    """
    from saasentialcore.services.scheduler_service import scheduler_logger
    from datetime import datetime, timezone
    
    # 1. Mise à jour des quotas
    await self.decrement_scheduled_on_success(org_id)
    await self.increment_published_today(org_id, delta=1)
    
    # 2. Extraire les résultats de publication depuis job_data
    result = job_data.get("result")
    if result and isinstance(result, dict):
        # result est un dict {platform: {status, external_id, error, ...}}
        successful_platforms = []
        failed_platforms = []
        
        for platform, platform_result in result.items():
            if platform_result.get("status") == "ok":
                successful_platforms.append(platform)
            else:
                failed_platforms.append(platform)
        
        # 3. Log structuré de succès avec détails par plateforme
        scheduler_logger.info(
            f"Job {job_data.get('job_id', 'unknown')} published successfully",
            extra={
                "event": "scheduler.job.publish_success",
                "job_id": job_data.get("job_id"),
                "org_id": org_id,
                "successful_platforms": successful_platforms,
                "failed_platforms": failed_platforms,
                "total_platforms": len(result),
                "muse_id": job_data.get("payload", {}).get("muse_id"),
                "published_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Note: L'historique de publication est déjà stocké dans job_data["result"]
        # qui est persisté dans scheduled_tasks via _update_job_fields() dans SchedulerService
```

**Fonctionnalités** :
- ✅ Mise à jour des quotas (déjà présent)
- ✅ Extraction des résultats par plateforme depuis `job_data["result"]`
- ✅ Log structuré avec détails par plateforme (succès/échec)
- ✅ Historique de publication stocké dans `job_data["result"]` (persisté dans `scheduled_tasks`)

**Accès à l'historique** :
```python
# Les résultats de publication sont stockés dans scheduled_tasks :
job = await db["scheduled_tasks"].find_one({"job_id": job_id})
dispatch_results = job.get("result", {})  # {platform: {status, external_id, error, ...}}
```

---

## 📊 RÉSULTAT FINAL

### ✅ Logger unifié

| Module | Import | Statut |
|--------|--------|--------|
| `saasentialcore/services/scheduler_service.py` | Définition | ✅ Source unique |
| `products/sparkpusher/services/task.py` | `from saasentialcore.services.scheduler_service import scheduler_logger` | ✅ Conforme |
| `products/sparkmetriq/services/scheduler/job_runner.py` | `from saasentialcore.services.scheduler_service import scheduler_logger` | ✅ Conforme |
| `api/services/scheduler/logger.py` | ❌ Supprimé | ✅ Redondance éliminée |

### ✅ Callbacks renforcés

#### **metrics_callback** :

| Événement | Appelé | Métrique |
|-----------|--------|----------|
| RUNNING | ✅ Oui (ajouté) | `scheduler.job.running` |
| SUCCESS | ✅ Oui | `scheduler.job.success` |
| FAILED | ✅ Oui | `scheduler.job.failed` |

#### **on_success_callback** :

| Action | Implémentée | Détails |
|--------|-------------|---------|
| Mise à jour quotas | ✅ Oui | `decrement_scheduled_on_success`, `increment_published_today` |
| Log structuré | ✅ Oui | Détails par plateforme (succès/échec) |
| Historique publication | ✅ Oui | Stocké dans `job_data["result"]` (persisté dans `scheduled_tasks`) |

---

## 🎯 EXEMPLE CONCRET : Flux d'observabilité

### **1. Job démarre (RUNNING)**

```python
# Dans SchedulerService.run_scheduled_job()
scheduler_logger.info(
    f"Starting job {job_id} (attempt {attempt}/{self.max_attempts})",
    extra={
        "event": "scheduler.job.start",
        "job_id": job_id,
        "org_id": org_id,
        "attempt": attempt,
        "status": "RUNNING",
        "platforms": ["instagram", "tiktok"]
    }
)

# ✅ Métrique publiée
metrics_callback(org_id, "RUNNING", {"platforms": ["instagram", "tiktok"]})
# → increment_s2_scheduler_job(org_id=org_id, status="RUNNING", platforms=["instagram", "tiktok"])
```

### **2. Job réussit (SUCCESS)**

```python
# Dans SchedulerService.run_scheduled_job()
scheduler_logger.info(
    f"Job {job_id} completed successfully",
    extra={
        "event": "scheduler.job.success",
        "job_id": job_id,
        "org_id": org_id,
        "status": "SUCCESS",
        "platforms": ["instagram", "tiktok"]
    }
)

# ✅ Métrique publiée
metrics_callback(org_id, "SUCCESS", {"platforms": ["instagram", "tiktok"]})
# → increment_s2_scheduler_job(org_id=org_id, status="SUCCESS", platforms=["instagram", "tiktok"])

# ✅ Callback de succès appelé
await on_success_callback(org_id, job_data)
# → Met à jour quotas
# → Log structuré avec détails par plateforme
# → Historique stocké dans job_data["result"]
```

### **3. Log structuré de succès (on_success_callback)**

```python
# Dans SaasentialCoreBridge.on_success_callback()
scheduler_logger.info(
    f"Job {job_id} published successfully",
    extra={
        "event": "scheduler.job.publish_success",
        "job_id": job_id,
        "org_id": org_id,
        "successful_platforms": ["instagram", "tiktok"],
        "failed_platforms": [],
        "total_platforms": 2,
        "muse_id": "muse_123",
        "published_at": "2024-01-15T10:30:00Z"
    }
)
```

---

## ✅ VALIDATION

### Checklist de conformité

- [x] ✅ Logger centralisé dans `saasentialcore/services/scheduler_service.py`
- [x] ✅ `api/services/scheduler/logger.py` supprimé (redondant)
- [x] ✅ Tous les modules importent depuis le core
- [x] ✅ Handler Telegram optionnel ajouté dans le core
- [x] ✅ `metrics_callback` appelé pour RUNNING, SUCCESS, FAILED
- [x] ✅ `on_success_callback` enrichi avec logs structurés et historique
- [x] ✅ Historique de publication stocké dans `job_data["result"]`
- [x] ✅ Aucune erreur de linter

---

## 🎉 RÉSULTAT

**UNIFICATION LOGGING ET CALLBACKS TERMINÉE AVEC SUCCÈS** ✅

- **Fichiers modifiés** : 2
  - `saasentialcore/services/scheduler_service.py` (logger enrichi, metrics_callback RUNNING)
  - `api/services/core/saasential_bridge.py` (on_success_callback enrichi)

- **Fichiers supprimés** : 1
  - `api/services/scheduler/logger.py` (redondant)

- **Observabilité** : ✅ **COMPLÈTE**
  - Logger unifié avec handlers optionnels
  - Métriques pour tous les états (RUNNING, SUCCESS, FAILED)
  - Logs structurés avec détails par plateforme
  - Historique de publication persisté

---

**STATUT**: ✅ **UNIFICATION COMPLÉTÉE**

