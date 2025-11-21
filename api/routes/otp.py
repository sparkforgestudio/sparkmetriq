# api/routes/otp.py
"""
Routes FastAPI pour le système OTP semi-manuel agnostique.
Jamais de code OTP en clair - approche sécurisée.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from api.core.auth import get_current_user
from api.core.settings import settings
from api.core.feature_gate import require_feature
from api.services.orgs import get_entitlements
from api.schemas.users import UserResponse
from api.schemas.otp import (
    OTPReserveIn, OTPPollOut, OTPAcknowledgeIn, OTPApplyIn, OTPApplyOut,
    OTPSessionOut, OTPSessionListResponse, OTPSessionSearchParams,
    OTPProviderInfo, OTPProviderListResponse, OTPPoolConfig, OTPPoolListResponse,
    OTPBudgetConfig, OTPBudgetResponse, OTPMetrics, OTPAnalyticsRequest, OTPAnalyticsResponse,
    OTPError, OTPErrorResponse, OTPConfig, OTPConfigResponse
)
from api.services.otp.sessions import (
    reserve_otp_session, poll_otp_session, acknowledge_otp_session, apply_otp_session,
    otp_session_manager
)
from api.services.otp.providers.registry import (
    provider_registry, health_check_adapters, list_available_adapters
)
from api.services.otp.policy import (
    get_supported_countries, get_app_requirements, validate_session_constraints
)
from api.databases.databases import db

router = APIRouter(prefix="/otp", tags=["OTP"])

# --- Garde-fou global (si module monté par erreur) ---
if not settings.feature_otp_enabled:
    def _feature_off():
        from fastapi import status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OTP module disabled globally"
        )


# --- Helper pour vérifier l'entitlement ---
async def check_otp_entitlement(current_user: UserResponse):
    """
    Vérifie que l'organisation a accès à OTP.
    
    Args:
        current_user: Utilisateur actuel
        
    Raises:
        HTTPException: 403 si OTP n'est pas activé pour l'organisation
    """
    entitlements = await get_entitlements(current_user.org_id)
    require_feature(entitlements, "otp")


# ---------- SESSION MANAGEMENT ----------

@router.post("/reserve", response_model=OTPPollOut)
async def reserve_otp_endpoint(
    payload: OTPReserveIn,
    current_user: UserResponse = Depends(get_current_user)
):
    """Réserver un numéro OTP pour une session."""
    # Vérifier l'entitlement OTP
    await check_otp_entitlement(current_user)
    
    try:
        return await reserve_otp_session(payload, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reservation failed: {str(e)}")

@router.post("/poll/{session_id}", response_model=OTPPollOut)
async def poll_otp_endpoint(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Poller une session OTP pour récupérer le code."""
    try:
        return await poll_otp_session(session_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Poll failed: {str(e)}")

@router.post("/ack/{session_id}", response_model=dict)
async def acknowledge_otp_endpoint(
    session_id: str,
    payload: OTPAcknowledgeIn,
    current_user: UserResponse = Depends(get_current_user)
):
    """Accuser réception d'un code OTP."""
    try:
        return await acknowledge_otp_session(session_id, current_user.id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Acknowledge failed: {str(e)}")

@router.post("/apply/{session_id}", response_model=OTPApplyOut)
async def apply_otp_endpoint(
    session_id: str,
    payload: OTPApplyIn,
    current_user: UserResponse = Depends(get_current_user)
):
    """Appliquer le résultat d'un code OTP."""
    try:
        result = await apply_otp_session(session_id, current_user.id, payload)
        return OTPApplyOut(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Apply failed: {str(e)}")

@router.post("/cancel/{session_id}", response_model=dict)
async def cancel_otp_endpoint(
    session_id: str,
    reason: str = Query("user_cancelled"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Annuler une session OTP."""
    try:
        return await otp_session_manager.cancel(session_id, current_user.id, reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cancel failed: {str(e)}")

@router.post("/ban/{session_id}", response_model=dict)
async def ban_otp_endpoint(
    session_id: str,
    reason: str = Query("fraud_detected"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Bannir une session OTP."""
    try:
        return await otp_session_manager.ban(session_id, current_user.id, reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ban failed: {str(e)}")

# ---------- SESSION QUERIES ----------

@router.get("/sessions", response_model=OTPSessionListResponse)
async def list_otp_sessions_endpoint(
    app: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    provider: Optional[str] = None,
    device_id: Optional[str] = None,
    slot_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """Lister les sessions OTP avec filtres."""
    params = OTPSessionSearchParams(
        app=app,
        country=country,
        state=state,
        provider=provider,
        device_id=device_id,
        slot_id=slot_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )
    
    query = {"org_id": current_user.id}
    
    # Appliquer les filtres
    if params.app:
        query["app"] = params.app
    if params.country:
        query["country"] = params.country
    if params.state:
        query["state"] = params.state
    if params.provider:
        query["provider"] = params.provider
    if params.device_id:
        query["device_id"] = params.device_id
    if params.slot_id:
        query["slot_id"] = params.slot_id
    
    # Filtres de date
    if params.start_date or params.end_date:
        query["created_at"] = {}
        if params.start_date:
            query["created_at"]["$gte"] = params.start_date
        if params.end_date:
            query["created_at"]["$lte"] = params.end_date
    
    # Pagination
    skip = (params.page - 1) * params.page_size
    
    # Compter le total
    total = await db["otp_sessions"].count_documents(query)
    
    # Récupérer les documents
    cursor = db["otp_sessions"].find(query).sort("created_at", -1).skip(skip).limit(params.page_size)
    docs = await cursor.to_list(None)
    
    # Convertir en OTPSessionOut
    sessions = []
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        sessions.append(OTPSessionOut(**doc))
    
    return OTPSessionListResponse(
        items=sessions,
        total=total,
        page=params.page,
        page_size=params.page_size
    )

@router.get("/sessions/{session_id}", response_model=OTPSessionOut)
async def get_otp_session_endpoint(
    session_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupérer une session OTP par ID."""
    doc = await db["otp_sessions"].find_one({
        "_id": ObjectId(session_id),
        "org_id": current_user.id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return OTPSessionOut(**doc)

# ---------- PROVIDER MANAGEMENT ----------

@router.get("/providers", response_model=OTPProviderListResponse)
async def list_otp_providers_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Lister les providers OTP disponibles."""
    providers_info = list_available_adapters()
    health_results = await health_check_adapters()
    
    providers = []
    primary_provider = None
    
    for provider_info in providers_info:
        health = health_results.get(provider_info["name"], {})
        
        providers.append(OTPProviderInfo(
            name=provider_info["name"],
            status=health.get("status", "unknown"),
            health_score=health.get("success_rate", 0.0),
            success_rate=health.get("success_rate", 0.0),
            avg_response_time=health.get("avg_response_time"),
            supported_countries=health.get("available_countries", []),
            supported_apps=health.get("supported_apps", []),
            last_health_check=datetime.now()
        ))
        
        if provider_info["is_primary"]:
            primary_provider = provider_info["name"]
    
    return OTPProviderListResponse(
        providers=providers,
        primary_provider=primary_provider
    )

@router.get("/providers/{provider_name}/health", response_model=dict)
async def get_provider_health_endpoint(
    provider_name: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Vérifier la santé d'un provider spécifique."""
    try:
        provider = provider_registry.get_provider(provider_name)
        health = await provider.health()
        return health
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ---------- POOL MANAGEMENT ----------

@router.get("/pools", response_model=OTPPoolListResponse)
async def list_otp_pools_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Lister les pools OTP configurés."""
    # Pour V1, retourner des pools mockés
    pools = [
        OTPPoolConfig(
            pool_name="instagram_us",
            app="instagram",
            country="US",
            provider="http_json",
            max_concurrent=5,
            daily_limit=50,
            cost_per_sms=0.05,
            quality_threshold=0.8
        ),
        OTPPoolConfig(
            pool_name="telegram_eu",
            app="telegram",
            country="FR",
            provider="http_json",
            max_concurrent=10,
            daily_limit=100,
            cost_per_sms=0.03,
            quality_threshold=0.9
        )
    ]
    
    # Stats mockées
    stats = [
        {
            "pool_name": "instagram_us",
            "total_reserved": 25,
            "successful": 20,
            "failed": 5,
            "success_rate": 0.8,
            "avg_response_time": 45.5,
            "daily_usage": 15,
            "daily_limit": 50,
            "remaining_quota": 35
        },
        {
            "pool_name": "telegram_eu",
            "total_reserved": 45,
            "successful": 42,
            "failed": 3,
            "success_rate": 0.93,
            "avg_response_time": 32.1,
            "daily_usage": 30,
            "daily_limit": 100,
            "remaining_quota": 70
        }
    ]
    
    return OTPPoolListResponse(pools=pools, stats=stats)

# ---------- BUDGET & QUOTAS ----------

@router.get("/budget", response_model=OTPBudgetResponse)
async def get_otp_budget_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Récupérer la configuration et le statut du budget OTP."""
    # Configuration mockée
    config = OTPBudgetConfig(
        org_id=current_user.id,
        daily_budget=100.0,
        monthly_budget=2000.0,
        per_app_limits={"instagram": 50, "telegram": 100},
        per_country_limits={"US": 30, "FR": 20},
        max_concurrent_sessions=10
    )
    
    # Statut mocké
    status = {
        "org_id": current_user.id,
        "daily_spent": 25.5,
        "monthly_spent": 450.0,
        "daily_remaining": 74.5,
        "monthly_remaining": 1550.0,
        "concurrent_sessions": 3,
        "max_concurrent_sessions": 10,
        "quota_exceeded": False,
        "budget_exceeded": False
    }
    
    return OTPBudgetResponse(config=config, status=status)

@router.put("/budget", response_model=OTPBudgetResponse)
async def update_otp_budget_endpoint(
    budget_config: OTPBudgetConfig,
    current_user: UserResponse = Depends(get_current_user)
):
    """Mettre à jour la configuration du budget OTP."""
    # Pour V1, simuler la mise à jour
    budget_config.org_id = current_user.id
    
    # Retourner la configuration mise à jour
    status = {
        "org_id": current_user.id,
        "daily_spent": 0.0,
        "monthly_spent": 0.0,
        "daily_remaining": budget_config.daily_budget,
        "monthly_remaining": budget_config.monthly_budget,
        "concurrent_sessions": 0,
        "max_concurrent_sessions": budget_config.max_concurrent_sessions,
        "quota_exceeded": False,
        "budget_exceeded": False
    }
    
    return OTPBudgetResponse(config=budget_config, status=status)

# ---------- ANALYTICS & METRICS ----------

@router.get("/metrics", response_model=OTPMetrics)
async def get_otp_metrics_endpoint(
    days: int = Query(7, ge=1, le=365),
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupérer les métriques OTP."""
    stats = await otp_session_manager.get_session_stats(current_user.id, days)
    
    return OTPMetrics(
        total_sessions=stats["total_sessions"],
        successful_sessions=stats["by_state"].get("APPLIED_SUCCESS", 0),
        failed_sessions=stats["by_state"].get("APPLIED_FAILED", 0) + stats["by_state"].get("FAILED", 0),
        success_rate=stats["success_rate"],
        avg_response_time=45.5,  # Mocké
        total_cost=stats["total_sessions"] * 0.05,  # Mocké
        sessions_by_app={"instagram": 10, "telegram": 15},  # Mocké
        sessions_by_country={"US": 12, "FR": 8},  # Mocké
        sessions_by_provider={"http_json": 20},  # Mocké
        time_period=f"{days}_days"
    )

@router.post("/analytics", response_model=OTPAnalyticsResponse)
async def get_otp_analytics_endpoint(
    analytics_request: OTPAnalyticsRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupérer les analytics OTP détaillées."""
    # Pour V1, retourner des données mockées
    metrics = OTPMetrics(
        total_sessions=150,
        successful_sessions=120,
        failed_sessions=30,
        success_rate=0.8,
        avg_response_time=42.5,
        total_cost=7.5,
        sessions_by_app={"instagram": 60, "telegram": 90},
        sessions_by_country={"US": 80, "FR": 70},
        sessions_by_provider={"http_json": 150},
        time_period="custom"
    )
    
    trends = [
        {"date": "2024-01-01", "sessions": 20, "success_rate": 0.85},
        {"date": "2024-01-02", "sessions": 25, "success_rate": 0.80},
        {"date": "2024-01-03", "sessions": 30, "success_rate": 0.75}
    ]
    
    breakdown = {
        "by_hour": {"0": 5, "1": 3, "2": 2},
        "by_app": {"instagram": 60, "telegram": 90},
        "by_country": {"US": 80, "FR": 70}
    }
    
    return OTPAnalyticsResponse(
        metrics=metrics,
        trends=trends,
        breakdown=breakdown
    )

# ---------- CONFIGURATION ----------

@router.get("/config", response_model=OTPConfigResponse)
async def get_otp_config_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Récupérer la configuration OTP."""
    config = OTPConfig()
    
    return OTPConfigResponse(
        config=config,
        last_updated=datetime.now(),
        updated_by=current_user.email
    )

@router.put("/config", response_model=OTPConfigResponse)
async def update_otp_config_endpoint(
    config: OTPConfig,
    current_user: UserResponse = Depends(get_current_user)
):
    """Mettre à jour la configuration OTP."""
    # Pour V1, simuler la mise à jour
    return OTPConfigResponse(
        config=config,
        last_updated=datetime.now(),
        updated_by=current_user.email
    )

# ---------- UTILITY ENDPOINTS ----------

@router.get("/supported-countries/{app}", response_model=List[str])
async def get_supported_countries_endpoint(
    app: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupérer les pays supportés pour une app."""
    return get_supported_countries(app)

@router.get("/app-requirements/{app}", response_model=dict)
async def get_app_requirements_endpoint(
    app: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Récupérer les exigences d'une app."""
    return get_app_requirements(app)

@router.post("/validate-constraints", response_model=dict)
async def validate_constraints_endpoint(
    constraints: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """Valider des contraintes de session."""
    is_valid, reason = validate_session_constraints(constraints)
    
    return {
        "valid": is_valid,
        "reason": reason
    }

# ---------- HEALTH CHECK ----------

@router.get("/health", response_model=dict)
async def otp_health_check_endpoint(current_user: UserResponse = Depends(get_current_user)):
    """Vérifier la santé du service OTP."""
    try:
        # Vérifier la santé des providers
        health_results = await health_check_adapters()
        
        # Vérifier la base de données
        session_count = await db["otp_sessions"].count_documents({"org_id": current_user.id})
        
        return {
            "status": "healthy",
            "providers": health_results,
            "database": "connected",
            "session_count": session_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
