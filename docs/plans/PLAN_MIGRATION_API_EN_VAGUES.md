# 🚀 PLAN DE MIGRATION API EN VAGUES GÉRABLES

**Date**: 2024  
**Objectif**: Organiser la migration de `api/` vers `products/*` en vagues prioritaires et gérables

**Contexte**:
- Routes conformes : 2/47 (4%)
- Services conformes : 10/90+ (11%)
- Statut global : ⚠️ **NON-CONFORME** (migration massive requise)

---

## 1. PRIORISATION DES ROUTES EN 3 VAGUES

### 📊 VAGUE 1 : TOP PRIORITÉS (Impact élevé, centralité, fréquence)

| Route | Produit | Destination | Impact | Fréquence | Complexité | Raison |
|-------|---------|-------------|--------|-----------|------------|--------|
| `calendar.py` | **SparkPusher** (S2) | `products/sparkpusher/api/routes/calendar.py` | 🔴 **CRITIQUE** | ⭐⭐⭐ | 🟡 Moyenne | Route S2 centrale, utilisée par le frontend calendrier |
| `muses.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/muses.py` | 🔴 **CRITIQUE** | ⭐⭐⭐ | 🟢 Faible | Route centrale, base de données des muses |
| `scheduler_stats.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/scheduler_stats.py` | 🔴 **CRITIQUE** | ⭐⭐⭐ | 🟡 Moyenne | Liée au scheduler, statistiques importantes |
| `platforms.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/platforms.py` | 🔴 **CRITIQUE** | ⭐⭐⭐ | 🟡 Moyenne | Gestion des plateformes, central |
| `assistant.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/assistant.py` | 🟡 **HAUTE** | ⭐⭐ | 🟡 Moyenne | Fonctionnalité IA importante |
| `ai_marketing.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/ai_marketing.py` | 🟡 **HAUTE** | ⭐⭐ | 🔴 Élevée | Module IA complexe mais important |
| `auth.py` | **Mixte** | `saasentialcore/services/auth_service.py` + `products/sparkmetriq/api/routes/auth.py` | 🔴 **CRITIQUE** | ⭐⭐⭐ | 🟡 Moyenne | Authentification, peut être partiellement générique |
| `users.py` | **Mixte** | `saasentialcore/services/user_service.py` + `products/sparkmetriq/api/routes/users.py` | 🔴 **CRITIQUE** | ⭐⭐⭐ | 🟡 Moyenne | Gestion utilisateurs, peut être partiellement générique |

**Total Vague 1**: 8 routes

---

### 📊 VAGUE 2 : ROUTES SECONDAIRES (Impact moyen, fonctionnalités importantes)

| Route | Produit | Destination | Impact | Fréquence | Complexité |
|-------|---------|-------------|--------|-----------|------------|
| `ppv_tracking.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/ppv_tracking.py` | 🟡 **MOYEN** | ⭐⭐ | 🟡 Moyenne |
| `tracking.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/tracking.py` | 🟡 **MOYEN** | ⭐⭐ | 🟡 Moyenne |
| `recap.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/recap.py` | 🟡 **MOYEN** | ⭐ | 🟢 Faible |
| `message_builder.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/message_builder.py` | 🟡 **MOYEN** | ⭐⭐ | 🟡 Moyenne |
| `intent.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/intent.py` | 🟡 **MOYEN** | ⭐⭐ | 🟡 Moyenne |
| `collab.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/collab.py` | 🟡 **MOYEN** | ⭐ | 🟡 Moyenne |
| `payments.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/payments.py` | 🟡 **MOYEN** | ⭐⭐ | 🟡 Moyenne |
| `ppv.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/ppv.py` | 🟡 **MOYEN** | ⭐⭐ | 🟡 Moyenne |
| `public_contents.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/public_contents.py` | 🟡 **MOYEN** | ⭐⭐ | 🟢 Faible |
| `otp.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/otp.py` | 🟡 **MOYEN** | ⭐ | 🔴 Élevée |
| `talent.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/talent.py` | 🟡 **MOYEN** | ⭐ | 🟡 Moyenne |
| `orgs.py` | **Mixte** | `saasentialcore/services/org_service.py` + `products/sparkmetriq/api/routes/orgs.py` | 🟡 **MOYEN** | ⭐⭐ | 🟡 Moyenne |
| `analytics*.py` (3 fichiers) | **Sparkmetriq** | `products/sparkmetriq/api/routes/analytics*.py` | 🟡 **MOYEN** | ⭐⭐ | 🟡 Moyenne |
| `bi_*.py` (2 fichiers) | **Sparkmetriq** | `products/sparkmetriq/api/routes/bi_*.py` | 🟡 **MOYEN** | ⭐ | 🟡 Moyenne |
| `webhooks/*.py` (8 fichiers) | **Sparkmetriq** | `products/sparkmetriq/api/routes/webhooks/*.py` | 🟡 **MOYEN** | ⭐⭐ | 🟢 Faible |
| `stats/*.py` (3 fichiers) | **Sparkmetriq** | `products/sparkmetriq/api/routes/stats/*.py` | 🟡 **MOYEN** | ⭐⭐ | 🟡 Moyenne |

**Total Vague 2**: ~25 routes

---

### 📊 VAGUE 3 : ROUTES LEGACY / PEU UTILISÉES (À déprécier éventuellement)

| Route | Produit | Destination | Impact | Fréquence | Action |
|-------|---------|-------------|--------|-----------|--------|
| `dispatcher.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/dispatcher.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | Migrer ou déprécier |
| `logs.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/logs.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | Migrer ou déprécier |
| `metrics.py` | **Mixte** | `saasentialcore/services/observability/` OU `products/sparkmetriq/api/routes/metrics.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | Analyser si générique |
| `media.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/media.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | Migrer ou déprécier |
| `translator.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/translator.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | Migrer ou déprécier |
| `redirect.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/redirect.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | Migrer ou déprécier |
| `session.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/session.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | Migrer ou déprécier |
| `ws_calendar.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/ws_calendar.py` | 🟢 **FAIBLE** | ⭐ | 🟡 Moyenne | WebSocket, migrer |
| `funnel_config.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/funnel_config.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | Migrer ou déprécier |
| `cloudphone.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/cloudphone.py` | 🟢 **FAIBLE** | ⭐ | 🟡 Moyenne | Feature flag, migrer |
| `chats.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/chats.py` | 🟢 **FAIBLE** | ⭐ | 🟡 Moyenne | Migrer |
| `analysis/*.py` (2 fichiers) | **Sparkmetriq** | `products/sparkmetriq/api/routes/analysis/*.py` | 🟢 **FAIBLE** | ⭐ | 🟡 Moyenne | Migrer |
| `*_test.py` (4 fichiers) | **Sparkmetriq** | `products/sparkmetriq/api/routes/*_test.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | **DÉPRÉCIER** (tests) |
| `admin.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/admin.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | Migrer |
| `bots.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/bots.py` | 🟢 **FAIBLE** | ⭐ | 🟡 Moyenne | Migrer |
| `auth_google.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/auth_google.py` | 🟢 **FAIBLE** | ⭐ | 🟡 Moyenne | Migrer |
| `tunnels_test.py` | **Sparkmetriq** | `products/sparkmetriq/api/routes/tunnels_test.py` | 🟢 **FAIBLE** | ⭐ | 🟢 Faible | **DÉPRÉCIER** (test) |

**Total Vague 3**: ~20 routes (dont 5 à déprécier)

---

## 2. EXEMPLES DÉTAILLÉS : REFACTOR AVANT/APRÈS

### 📋 Exemple 1 : `calendar.py` (SparkPusher S2)

#### **AVANT** : `api/routes/calendar.py`

```python
# api/routes/calendar.py
from api.databases.databases import db
from api.schemas.payload_schema import UnifiedPostPayload

@router.get("/posts")
async def get_calendar_posts(org_id: str, from_date: datetime, to_date: datetime):
    # ❌ Accès DB direct
    cursor = db["scheduled_tasks"].find({
        "org_id": org_id,
        "scheduled_at": {"$gte": from_date, "$lte": to_date}
    })
    jobs = await cursor.to_list(length=None)
    
    # ❌ Logique métier dans la route (reconstruction payload)
    events = []
    for job in jobs:
        payload_data = job.get("payload")
        if payload_data:
            payload = UnifiedPostPayload(**payload_data)
            events.append(CalendarPostEvent(
                id=str(job["_id"]),
                title=payload.caption[:50],
                scheduled_at=job["scheduled_at"],
                status=job["status"]
            ))
    
    return events
```

#### **APRÈS** : Structure refactorée

**Route** : `products/sparkpusher/api/routes/calendar.py`
```python
# products/sparkpusher/api/routes/calendar.py
from fastapi import APIRouter, Depends, Query
from products.sparkpusher.services.calendar_service import CalendarService
from api.core.auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["sparkpusher-calendar"])

@router.get("/posts")
async def get_calendar_posts(
    org_id: str = Query(...),
    from_date: datetime = Query(...),
    to_date: datetime = Query(...),
    status: Optional[JobStatus] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère les posts planifiés pour le calendrier S2.
    """
    # ✅ Délègue à un service
    service = CalendarService()
    events = await service.get_calendar_events(
        org_id=org_id,
        from_date=from_date,
        to_date=to_date,
        status=status,
        user_id=current_user.id
    )
    return events
```

**Service** : `products/sparkpusher/services/calendar_service.py`
```python
# products/sparkpusher/services/calendar_service.py
from api.services.core.saasential_bridge import SaasentialCoreBridge
from api.schemas.payload_schema import UnifiedPostPayload

class CalendarService:
    """
    Service de gestion du calendrier S2.
    
    Logique métier spécifique SparkPusher :
    - Reconstruction UnifiedPostPayload
    - Formatage des événements pour le calendrier
    """
    
    def __init__(self):
        self.bridge = SaasentialCoreBridge()
    
    async def get_calendar_events(
        self,
        org_id: str,
        from_date: datetime,
        to_date: datetime,
        status: Optional[str] = None,
        user_id: str = None
    ) -> List[CalendarPostEvent]:
        """
        Récupère les événements du calendrier.
        
        ✅ Utilise le core pour récupérer les jobs
        ✅ Logique métier spécifique S2 (reconstruction payload)
        """
        # ✅ Utilise le core via le bridge
        jobs = await self.bridge.list_jobs_for_calendar(
            org_id=org_id,
            from_date=from_date,
            to_date=to_date,
            status=status
        )
        
        # ✅ Logique métier spécifique S2
        events = []
        for job in jobs:
            payload_data = job.get("payload")
            if payload_data:
                payload = UnifiedPostPayload(**payload_data)
                events.append(CalendarPostEvent(
                    id=str(job.get("_id") or job.get("job_id")),
                    title=payload.caption[:50] if payload.caption else "Sans titre",
                    scheduled_at=job.get("scheduled_at"),
                    status=job.get("status"),
                    platforms=[t.platform for t in payload.targets]
                ))
        
        return events
```

**Shim** : `api/routes/calendar.py`
```python
# api/routes/calendar.py (SHIM)
"""
Shim de compatibilité pour les routes calendrier.
Délègue vers products.sparkpusher.api.routes.calendar.
"""

from fastapi import APIRouter
from products.sparkpusher.api.routes.calendar import router as sparkpusher_calendar_router
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["Calendar"])

# Inclure toutes les routes depuis SparkPusher
for route in sparkpusher_calendar_router.routes:
    router.routes.append(route)

# ⚠️ Log de dépréciation (optionnel)
@router.middleware("http")
async def deprecation_warning(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Deprecated"] = "true"
    response.headers["X-API-New-Endpoint"] = "/api/sparkpusher/calendar"
    logger.warning(
        f"Deprecated endpoint called: {request.url.path}",
        extra={"deprecated": True, "new_endpoint": "/api/sparkpusher/calendar"}
    )
    return response
```

---

### 📋 Exemple 2 : `muses.py` (Sparkmetriq)

#### **AVANT** : `api/routes/muses.py`

```python
# api/routes/muses.py
from api.databases.databases import get_core_db

@router.get("/")
async def list_muses(current_user: UserResponse = Depends(get_current_user)):
    # ❌ Accès DB direct
    db = get_core_db()
    cursor = db["muses"].find({"org_id": current_user.org_id}).sort("name", 1)
    muses = await cursor.to_list(length=None)
    
    # ❌ Logique métier dans la route (transformations)
    items = []
    for muse in muses:
        muse_id = str(muse.get("_id") or muse.get("muse_id", ""))
        muse_name = muse.get("name") or muse.get("display_name") or muse_id
        items.append(MuseSummary(id=muse_id, name=muse_name))
    
    return items
```

#### **APRÈS** : Structure refactorée

**Route** : `products/sparkmetriq/api/routes/muses.py`
```python
# products/sparkmetriq/api/routes/muses.py
from fastapi import APIRouter, Depends
from products.sparkmetriq.services.muses_service import MusesService
from api.core.auth import get_current_user

router = APIRouter(prefix="/muses", tags=["sparkmetriq-muses"])

@router.get("/", response_model=List[MuseSummary])
async def list_muses(
    current_user: UserResponse = Depends(get_current_user)
) -> List[MuseSummary]:
    """
    Liste les muses de l'organisation.
    """
    # ✅ Délègue à un service
    service = MusesService()
    return await service.list_muses(org_id=current_user.org_id)
```

**Service** : `products/sparkmetriq/services/muses_service.py`
```python
# products/sparkmetriq/services/muses_service.py
from api.databases.databases import get_core_db
from api.schemas.muses import MuseSummary

class MusesService:
    """
    Service de gestion des muses pour Sparkmetriq.
    
    Logique métier spécifique Sparkmetriq :
    - Gestion des muses et catégories
    - Transformations de données
    """
    
    async def list_muses(self, org_id: str) -> List[MuseSummary]:
        """
        Liste les muses d'une organisation.
        
        ✅ Logique métier spécifique Sparkmetriq
        """
        db = get_core_db()
        cursor = db["muses"].find({"org_id": org_id}).sort("name", 1)
        muses = await cursor.to_list(length=None)
        
        # ✅ Logique métier spécifique (transformations)
        items = []
        for muse in muses:
            muse_id = str(muse.get("_id") or muse.get("muse_id", ""))
            muse_name = muse.get("name") or muse.get("display_name") or muse_id
            items.append(MuseSummary(id=muse_id, name=muse_name))
        
        return items
    
    async def get_muse_categories(self, org_id: str) -> List[MuseCategory]:
        """Récupère les catégories de muses."""
        db = get_core_db()
        cursor = db["muse_categories"].find({"org_id": org_id})
        categories = await cursor.to_list(length=None)
        return [MuseCategory(**cat) for cat in categories]
```

**Shim** : `api/routes/muses.py`
```python
# api/routes/muses.py (SHIM)
"""
Shim de compatibilité pour les routes muses.
Délègue vers products.sparkmetriq.api.routes.muses.
"""

from fastapi import APIRouter
from products.sparkmetriq.api.routes.muses import router as sparkmetriq_muses_router

router = APIRouter(prefix="/muses", tags=["Muses"])

# Inclure toutes les routes depuis Sparkmetriq
for route in sparkmetriq_muses_router.routes:
    router.routes.append(route)
```

---

### 📋 Exemple 3 : `scheduler_stats.py` (Sparkmetriq)

#### **AVANT** : `api/routes/scheduler_stats.py`

```python
# api/routes/scheduler_stats.py
from api.databases.databases import db

@router.get("/stats/by-muse")
async def get_stats_by_muse(org_id: str, muse_id: str):
    # ❌ Agrégation MongoDB directe dans la route
    pipeline = [
        {"$match": {"org_id": org_id, "muse_id": muse_id}},
        {"$group": {
            "_id": "$platform",
            "total": {"$sum": 1},
            "success": {"$sum": {"$cond": [{"$eq": ["$status", "SUCCESS"]}, 1, 0]}}
        }}
    ]
    results = await db["platform_logs"].aggregate(pipeline).to_list(None)
    return results
```

#### **APRÈS** : Structure refactorée

**Route** : `products/sparkmetriq/api/routes/scheduler_stats.py`
```python
# products/sparkmetriq/api/routes/scheduler_stats.py
from products.sparkmetriq.services.scheduler_stats_service import SchedulerStatsService

@router.get("/stats/by-muse")
async def get_stats_by_muse(org_id: str, muse_id: str):
    """
    Récupère les statistiques de scheduler par muse.
    """
    # ✅ Délègue à un service
    service = SchedulerStatsService()
    return await service.get_stats_by_muse(org_id=org_id, muse_id=muse_id)
```

**Service** : `products/sparkmetriq/services/scheduler_stats_service.py`
```python
# products/sparkmetriq/services/scheduler_stats_service.py
from api.databases.databases import db

class SchedulerStatsService:
    """
    Service de statistiques du scheduler pour Sparkmetriq.
    
    Logique métier spécifique Sparkmetriq :
    - Agrégations MongoDB complexes
    - Calculs de statistiques
    """
    
    async def get_stats_by_muse(self, org_id: str, muse_id: str) -> Dict[str, Any]:
        """
        Récupère les statistiques par muse.
        
        ✅ Logique métier spécifique Sparkmetriq (agrégations)
        """
        pipeline = [
            {"$match": {"org_id": org_id, "muse_id": muse_id}},
            {"$group": {
                "_id": "$platform",
                "total": {"$sum": 1},
                "success": {"$sum": {"$cond": [{"$eq": ["$status", "SUCCESS"]}, 1, 0]}}
            }}
        ]
        results = await db["platform_logs"].aggregate(pipeline).to_list(None)
        return results
```

---

## 3. STRATÉGIE DE SHIMS DE COMPATIBILITÉ

### 3.1. Principe général

**Objectif** : Maintenir les anciens endpoints (`/api/calendar`, `/api/muses`, etc.) tout en redirigeant vers les nouvelles routes produits.

**Durée de transition** : 3-6 mois (selon adoption frontend)

---

### 3.2. Pattern de shim standard

```python
# api/routes/<nom>.py (SHIM)
"""
Shim de compatibilité pour les routes <nom>.
Délègue vers products.<produit>.api.routes.<nom>.

⚠️ DÉPRÉCIÉ : Cette route sera supprimée dans une future version.
Utilisez /api/<produit>/<nom> à la place.
"""

from fastapi import APIRouter, Request, Response
from products.<produit>.api.routes.<nom> import router as <produit>_<nom>_router
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/<nom>", tags=["<Nom>"])

# Inclure toutes les routes depuis le produit
for route in <produit>_<nom>_router.routes:
    router.routes.append(route)

# Middleware de dépréciation (optionnel)
@router.middleware("http")
async def deprecation_warning(request: Request, call_next):
    """
    Ajoute des headers de dépréciation aux réponses.
    """
    response = await call_next(request)
    
    # Headers de dépréciation
    response.headers["X-API-Deprecated"] = "true"
    response.headers["X-API-Deprecated-Since"] = "2024-XX-XX"
    response.headers["X-API-New-Endpoint"] = f"/api/<produit>/<nom>"
    response.headers["X-API-Migration-Guide"] = "https://docs.example.com/migration"
    
    # Log pour monitoring
    logger.warning(
        f"Deprecated endpoint called: {request.url.path}",
        extra={
            "deprecated": True,
            "old_endpoint": str(request.url.path),
            "new_endpoint": f"/api/<produit>/<nom>",
            "user_id": getattr(request.state, "user_id", None)
        }
    )
    
    return response
```

---

### 3.3. Exemples concrets de shims

#### **Shim 1** : `api/routes/calendar.py` (SparkPusher)

```python
# api/routes/calendar.py (SHIM)
"""
Shim de compatibilité pour les routes calendrier S2.
Délègue vers products.sparkpusher.api.routes.calendar.

⚠️ DÉPRÉCIÉ : Utilisez /api/sparkpusher/calendar à la place.
"""

from fastapi import APIRouter, Request
from products.sparkpusher.api.routes.calendar import router as sparkpusher_calendar_router
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["Calendar"])

# Inclure toutes les routes depuis SparkPusher
for route in sparkpusher_calendar_router.routes:
    router.routes.append(route)

# Middleware de dépréciation
@router.middleware("http")
async def deprecation_warning(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-API-Deprecated"] = "true"
    response.headers["X-API-New-Endpoint"] = "/api/sparkpusher/calendar"
    logger.warning(f"Deprecated endpoint: {request.url.path} → /api/sparkpusher/calendar")
    return response
```

#### **Shim 2** : `api/routes/muses.py` (Sparkmetriq)

```python
# api/routes/muses.py (SHIM)
"""
Shim de compatibilité pour les routes muses.
Délègue vers products.sparkmetriq.api.routes.muses.

⚠️ DÉPRÉCIÉ : Utilisez /api/sparkmetriq/muses à la place.
"""

from fastapi import APIRouter
from products.sparkmetriq.api.routes.muses import router as sparkmetriq_muses_router

router = APIRouter(prefix="/muses", tags=["Muses"])

# Inclure toutes les routes depuis Sparkmetriq
for route in sparkmetriq_muses_router.routes:
    router.routes.append(route)
```

#### **Shim 3** : `api/routes/scheduler_stats.py` (Sparkmetriq)

```python
# api/routes/scheduler_stats.py (SHIM)
"""
Shim de compatibilité pour les statistiques du scheduler.
Délègue vers products.sparkmetriq.api.routes.scheduler_stats.
"""

from fastapi import APIRouter
from products.sparkmetriq.api.routes.scheduler_stats import router as sparkmetriq_scheduler_stats_router

router = APIRouter(prefix="/scheduler/stats", tags=["Scheduler Stats"])

# Inclure toutes les routes depuis Sparkmetriq
for route in sparkmetriq_scheduler_stats_router.routes:
    router.routes.append(route)
```

---

### 3.4. Mise à jour de `api/main.py`

```python
# api/main.py

# Routes historiques (shims) - PRÉFIXE /api
from api.routes.calendar import router as calendar_router
from api.routes.muses import router as muses_router
from api.routes.scheduler_stats import router as scheduler_stats_router

app.include_router(calendar_router, prefix="/api", tags=["Calendar"])
app.include_router(muses_router, prefix="/api", tags=["Muses"])
app.include_router(scheduler_stats_router, prefix="/api", tags=["Scheduler Stats"])

# Routes nouvelles (optionnel, pour migration progressive)
from products.sparkpusher.api.routes.calendar import router as sparkpusher_calendar_router
from products.sparkmetriq.api.routes.muses import router as sparkmetriq_muses_router
from products.sparkmetriq.api.routes.scheduler_stats import router as sparkmetriq_scheduler_stats_router

app.include_router(sparkpusher_calendar_router, prefix="/api/sparkpusher", tags=["SparkPusher-Calendar"])
app.include_router(sparkmetriq_muses_router, prefix="/api/sparkmetriq", tags=["Sparkmetriq-Muses"])
app.include_router(sparkmetriq_scheduler_stats_router, prefix="/api/sparkmetriq", tags=["Sparkmetriq-Scheduler-Stats"])
```

---

### 3.5. Documentation de migration

**Fichier** : `docs/API_MIGRATION_GUIDE.md`

```markdown
# Guide de Migration API

## Endpoints Dépréciés

| Ancien Endpoint | Nouveau Endpoint | Produit | Date de dépréciation |
|----------------|------------------|---------|---------------------|
| `/api/calendar/posts` | `/api/sparkpusher/calendar/posts` | SparkPusher | 2024-XX-XX |
| `/api/muses/` | `/api/sparkmetriq/muses/` | Sparkmetriq | 2024-XX-XX |
| `/api/scheduler/stats/by-muse` | `/api/sparkmetriq/scheduler/stats/by-muse` | Sparkmetriq | 2024-XX-XX |

## Headers de Dépréciation

Les anciens endpoints retournent les headers suivants :
- `X-API-Deprecated: true`
- `X-API-New-Endpoint: /api/<produit>/<route>`
- `X-API-Migration-Guide: https://docs.example.com/migration`

## Plan de Suppression

Les shims seront supprimés après une période de transition de 6 mois.
```

---

## 4. PLAN DE TRAVAIL EN 3 SPRINTS

### 🚀 SPRINT 1 : VAGUE 1 (Top priorités) - 2-3 semaines

**Objectif** : Migrer les 8 routes les plus critiques

#### **Routes à migrer** (8 routes)

1. ✅ `calendar.py` → `products/sparkpusher/api/routes/calendar.py`
2. ✅ `muses.py` → `products/sparkmetriq/api/routes/muses.py`
3. ✅ `scheduler_stats.py` → `products/sparkmetriq/api/routes/scheduler_stats.py`
4. ✅ `platforms.py` → `products/sparkmetriq/api/routes/platforms.py`
5. ✅ `assistant.py` → `products/sparkmetriq/api/routes/assistant.py`
6. ✅ `ai_marketing.py` → `products/sparkmetriq/api/routes/ai_marketing.py`
7. ✅ `auth.py` → Analyser et migrer (générique vs spécifique)
8. ✅ `users.py` → Analyser et migrer (générique vs spécifique)

#### **Services à créer** (~10 services)

1. `products/sparkpusher/services/calendar_service.py`
2. `products/sparkmetriq/services/muses_service.py`
3. `products/sparkmetriq/services/scheduler_stats_service.py`
4. `products/sparkmetriq/services/platforms_service.py`
5. `products/sparkmetriq/services/assistant_service.py`
6. `products/sparkmetriq/services/ai_marketing_service.py` (ou réutiliser `api/services/ai_marketing/`)
7. `saasentialcore/services/auth_service.py` (si générique)
8. `saasentialcore/services/user_service.py` (si générique)
9. `products/sparkmetriq/services/auth_service.py` (si spécifique)
10. `products/sparkmetriq/services/user_service.py` (si spécifique)

#### **Shims à créer** (8 shims)

1. `api/routes/calendar.py` (shim)
2. `api/routes/muses.py` (shim)
3. `api/routes/scheduler_stats.py` (shim)
4. `api/routes/platforms.py` (shim)
5. `api/routes/assistant.py` (shim)
6. `api/routes/ai_marketing.py` (shim)
7. `api/routes/auth.py` (shim)
8. `api/routes/users.py` (shim)

#### **Livrables Sprint 1**

- ✅ 8 routes migrées vers `products/*/api/routes/`
- ✅ ~10 services créés dans `products/*/services/` ou `saasentialcore/services/`
- ✅ 8 shims de compatibilité créés dans `api/routes/`
- ✅ Tests E2E mis à jour
- ✅ Documentation de migration créée

**Estimation** : 2-3 semaines (1 développeur)

---

### 🚀 SPRINT 2 : VAGUE 2 (Routes secondaires) - 3-4 semaines

**Objectif** : Migrer les ~25 routes secondaires

#### **Routes à migrer** (~25 routes)

1. `ppv_tracking.py` → `products/sparkmetriq/api/routes/ppv_tracking.py`
2. `tracking.py` → `products/sparkmetriq/api/routes/tracking.py`
3. `recap.py` → `products/sparkmetriq/api/routes/recap.py`
4. `message_builder.py` → `products/sparkmetriq/api/routes/message_builder.py`
5. `intent.py` → `products/sparkmetriq/api/routes/intent.py`
6. `collab.py` → `products/sparkmetriq/api/routes/collab.py`
7. `payments.py` → `products/sparkmetriq/api/routes/payments.py`
8. `ppv.py` → `products/sparkmetriq/api/routes/ppv.py`
9. `public_contents.py` → `products/sparkmetriq/api/routes/public_contents.py`
10. `otp.py` → `products/sparkmetriq/api/routes/otp.py`
11. `talent.py` → `products/sparkmetriq/api/routes/talent.py`
12. `orgs.py` → Analyser (générique vs spécifique)
13. `analytics_conversations.py` → `products/sparkmetriq/api/routes/analytics_conversations.py`
14. `analytics_bi.py` → `products/sparkmetriq/api/routes/analytics_bi.py`
15. `analytics_muses.py` → `products/sparkmetriq/api/routes/analytics_muses.py`
16. `bi_pricing.py` → `products/sparkmetriq/api/routes/bi_pricing.py`
17. `bi_insights.py` → `products/sparkmetriq/api/routes/bi_insights.py`
18. `webhooks/*.py` (8 fichiers) → `products/sparkmetriq/api/routes/webhooks/*.py`
19. `stats/*.py` (3 fichiers) → `products/sparkmetriq/api/routes/stats/*.py`

#### **Services à migrer/créer** (~30 services)

- Migrer `api/services/ppv_tracking/` → `products/sparkmetriq/services/ppv_tracking/`
- Migrer `api/services/tracking/` → `products/sparkmetriq/services/tracking/`
- Migrer `api/services/messaging/` → `products/sparkmetriq/services/messaging/`
- Migrer `api/services/intent/` → `products/sparkmetriq/services/intent/`
- Migrer `api/services/collab/` → `products/sparkmetriq/services/collab/`
- Migrer `api/services/payment_gateway/` → `products/sparkmetriq/services/payment_gateway/`
- Migrer `api/services/otp/` → `products/sparkmetriq/services/otp/`
- Migrer `api/services/talent/` → `products/sparkmetriq/services/talent/`
- Migrer `api/services/analytics/` → `products/sparkmetriq/services/analytics/`
- Migrer `api/services/bi/` → `products/sparkmetriq/services/bi/`
- Etc.

#### **Livrables Sprint 2**

- ✅ ~25 routes migrées
- ✅ ~30 services migrés/créés
- ✅ ~25 shims créés
- ✅ Tests E2E mis à jour
- ✅ Documentation complétée

**Estimation** : 3-4 semaines (1-2 développeurs)

---

### 🚀 SPRINT 3 : VAGUE 3 (Routes legacy) + Finalisation - 2-3 semaines

**Objectif** : Migrer les routes legacy et finaliser la migration

#### **Routes à migrer** (~15 routes, 5 à déprécier)

1. `dispatcher.py` → `products/sparkmetriq/api/routes/dispatcher.py`
2. `logs.py` → `products/sparkmetriq/api/routes/logs.py`
3. `metrics.py` → Analyser (générique vs spécifique)
4. `media.py` → `products/sparkmetriq/api/routes/media.py`
5. `translator.py` → `products/sparkmetriq/api/routes/translator.py`
6. `redirect.py` → `products/sparkmetriq/api/routes/redirect.py`
7. `session.py` → `products/sparkmetriq/api/routes/session.py`
8. `ws_calendar.py` → `products/sparkmetriq/api/routes/ws_calendar.py`
9. `funnel_config.py` → `products/sparkmetriq/api/routes/funnel_config.py`
10. `cloudphone.py` → `products/sparkmetriq/api/routes/cloudphone.py`
11. `chats.py` → `products/sparkmetriq/api/routes/chats.py`
12. `analysis/*.py` → `products/sparkmetriq/api/routes/analysis/*.py`
13. `admin.py` → `products/sparkmetriq/api/routes/admin.py`
14. `bots.py` → `products/sparkmetriq/api/routes/bots.py`
15. `auth_google.py` → `products/sparkmetriq/api/routes/auth_google.py`

#### **Routes à déprécier** (5 routes)

1. ❌ `instagram_test.py` → **SUPPRIMER** (test)
2. ❌ `threads_test.py` → **SUPPRIMER** (test)
3. ❌ `snapchat_test.py` → **SUPPRIMER** (test)
4. ❌ `tunnels_test.py` → **SUPPRIMER** (test)
5. ❌ `analysis_tunnels.py` → Analyser (peut-être déprécier)

#### **Services à migrer/créer** (~15 services)

- Migrer `api/services/logs/` → `products/sparkmetriq/services/logs/` OU `saasentialcore/services/observability/`
- Migrer `api/services/cloudphone/` → `products/sparkmetriq/services/cloudphone/`
- Migrer `api/services/chat_omnichannel/` → `products/sparkmetriq/services/chat_omnichannel/`
- Etc.

#### **Nettoyage final**

1. ✅ Supprimer les fichiers obsolètes (`scheduler_engine.py`, `content_distributor/scheduler.py`)
2. ✅ Vérifier qu'aucun import `api.services.*` ne reste dans les routes produits
3. ✅ Finaliser la documentation
4. ✅ Audit final de conformité

#### **Livrables Sprint 3**

- ✅ ~15 routes migrées
- ✅ ~15 services migrés/créés
- ✅ 5 routes dépréciées/supprimées
- ✅ Nettoyage des fichiers obsolètes
- ✅ Audit final de conformité
- ✅ Documentation finale

**Estimation** : 2-3 semaines (1 développeur)

---

## 5. RÉSUMÉ ET MÉTRIQUES

### 📊 Métriques globales

| Métrique | Avant | Après Sprint 1 | Après Sprint 2 | Après Sprint 3 |
|----------|-------|----------------|----------------|----------------|
| **Routes conformes** | 2/47 (4%) | 10/47 (21%) | 35/47 (74%) | 47/47 (100%) |
| **Services conformes** | 10/90+ (11%) | 20/90+ (22%) | 60/90+ (67%) | 90+/90+ (100%) |
| **Score de conformité** | 10% | 21% | 70% | 100% |

### 🎯 Objectifs par sprint

- **Sprint 1** : Migrer les routes critiques (8 routes) → **21% de conformité**
- **Sprint 2** : Migrer les routes secondaires (25 routes) → **70% de conformité**
- **Sprint 3** : Finaliser et nettoyer (15 routes) → **100% de conformité**

### ⏱️ Estimation totale

- **Sprint 1** : 2-3 semaines
- **Sprint 2** : 3-4 semaines
- **Sprint 3** : 2-3 semaines

**Total** : 7-10 semaines (1-2 développeurs)

---

## 6. CHECKLIST DE VALIDATION

### ✅ Après chaque migration de route

- [ ] Route migrée vers `products/*/api/routes/`
- [ ] Service créé dans `products/*/services/` ou `saasentialcore/services/`
- [ ] Shim créé dans `api/routes/` (délégation)
- [ ] Tests E2E mis à jour
- [ ] Documentation mise à jour
- [ ] Headers de dépréciation ajoutés (si applicable)
- [ ] Vérification que l'ancien endpoint fonctionne toujours
- [ ] Vérification que le nouvel endpoint fonctionne

### ✅ Après chaque sprint

- [ ] Tous les tests passent
- [ ] Aucune régression détectée
- [ ] Documentation complète
- [ ] Audit de conformité effectué
- [ ] Revue de code effectuée

---

**STATUT**: ✅ **PLAN PRÊT POUR EXÉCUTION**

