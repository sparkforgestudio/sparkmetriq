# api/routes/health.py
"""
Routes de santé et readiness pour musAI Platform.
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone

from api.core.settings import settings
from api.databases.databases import get_core_db, get_bi_db

router = APIRouter(prefix="/api", tags=["Health"])

# Timestamp de démarrage pour calculer l'uptime
START_AT = datetime.now(timezone.utc)


@router.get("/healthz")
async def healthz() -> dict:
    """Endpoint de santé (health check).
    
    Retourne l'état de l'application, l'uptime, la version et l'état des modules.
    Ne fait pas de vérification de connectivité (utiliser /readyz pour cela).
    
    Utilisé par les orchestrateurs (Kubernetes, load balancers) pour vérifier
    que l'application est en vie. Ne vérifie pas les dépendances externes.
    
    Returns:
        Dict avec:
            - status: "ok" si l'app fonctionne
            - uptime_s: Nombre de secondes depuis le démarrage
            - version: Version de l'application
            - environment: Environnement (development/staging/production)
            - modules: Dict des feature flags (BI, Scheduler, CloudPhone, etc.)
    """
    uptime_seconds = int((datetime.now(timezone.utc) - START_AT).total_seconds())
    
    return {
        "status": "ok",
        "uptime_s": uptime_seconds,
        "version": settings.app_version,
        "environment": settings.environment,
        "modules": {
            "BI": settings.enable_bi,
            "Scheduler": settings.enable_scheduler,
            "CloudPhone": settings.feature_cloudphone_enabled,
            "OTP": settings.feature_otp_enabled,
            "Translator": settings.feature_translator_enabled,
            "Recap": getattr(settings, "feature_convo_recap_enabled", False),
            "MessageBuilder": getattr(settings, "feature_message_builder_enabled", False),
            "LinkTracking": getattr(settings, "feature_link_tracking_enabled", False),
            "Collaboration": getattr(settings, "feature_collab_enabled", False),
        }
    }


@router.get("/readyz")
async def readyz() -> dict:
    """Endpoint de readiness (readiness check).
    
    Vérifie la connectivité aux bases de données (Core et BI si activée).
    Utilisé par les orchestrateurs (Kubernetes, etc.) pour vérifier si l'app
    est prête à recevoir du trafic (dépendances disponibles).
    
    Returns:
        Dict avec "ready": True si toutes les dépendances sont accessibles.
        
    Raises:
        HTTPException: 503 si une base de données n'est pas accessible,
            avec détails des erreurs dans le body.
    """
    errors = []
    
    # Vérifier la connexion Core
    try:
        db_core = get_core_db()
        await db_core.command("ping")
    except Exception as e:
        errors.append(f"Core DB: {str(e)}")
    
    # Vérifier la connexion BI si activée
    if settings.enable_bi:
        try:
            db_bi = get_bi_db()
            await db_bi.command("ping")
        except Exception as e:
            errors.append(f"BI DB: {str(e)}")
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "ready": False,
                "errors": errors
            }
        )
    
    return {"ready": True}

