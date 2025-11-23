# api/routes/platforms.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.platforms import (
    PlatformType, ContentRequest, ContentResponse, MultiPlatformContentRequest,
    MultiPlatformContentResponse, PlatformAnalytics, PlatformCredentials,
    TikTokContentRequest, FanvueContentRequest, OnlyFansContentRequest
)
from api.services.content_distributor.dispatcher import dispatch_content
from api.databases.databases import db

router = APIRouter(prefix="/api/platforms", tags=["Platforms"])

@router.post("/publish", response_model=MultiPlatformContentResponse)
async def publish_to_platforms(
    request: MultiPlatformContentRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Publie du contenu sur plusieurs plateformes simultanément.
    """
    try:
        results = {}
        total_success = 0
        total_errors = 0
        
        # Préparation des informations du modèle
        model_info = {
            "agency_id": request.agency_id,
            "muse_id": request.muse_id,
            "user_email": current_user.email
        }
        
        # Récupération des credentials pour chaque plateforme
        for platform in request.platforms:
            try:
                # Récupération des credentials de la plateforme
                credentials = await get_platform_credentials(request.agency_id, request.muse_id, platform)
                model_info.update(credentials)
                
                # Préparation du contenu pour la plateforme
                content = prepare_content_for_platform(request.content, platform)
                
                # Publication
                result = await dispatch_content(content, [platform.value], model_info)
                
                if result.get("status") == "success":
                    total_success += 1
                    results[platform] = ContentResponse(
                        platform=platform,
                        content_id=result.get("content_id", "unknown"),
                        status="success",
                        message="Publication réussie",
                        platform_response=result,
                        published_at=utcnow()
                    )
                else:
                    total_errors += 1
                    results[platform] = ContentResponse(
                        platform=platform,
                        content_id="",
                        status="error",
                        message=result.get("reason", "Erreur inconnue"),
                        error_details=str(result)
                    )
                    
            except Exception as e:
                total_errors += 1
                results[platform] = ContentResponse(
                    platform=platform,
                    content_id="",
                    status="error",
                    message=f"Erreur: {str(e)}",
                    error_details=str(e)
                )
        
        return MultiPlatformContentResponse(
            request_id=f"req_{utcnow().timestamp()}",
            results=results,
            total_success=total_success,
            total_errors=total_errors,
            completed_at=utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics", response_model=List[PlatformAnalytics])
async def get_platform_analytics(
    agency_id: str = Query(..., description="ID de l'agence"),
    muse_id: Optional[str] = Query(None, description="ID de la muse"),
    platform: Optional[PlatformType] = Query(None, description="Plateforme spécifique"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère les analytics pour les plateformes.
    """
    try:
        # Par défaut, 30 derniers jours
        if not start_date:
            start_date = utcnow() - timedelta(days=30)
        if not end_date:
            end_date = utcnow()
        
        # Construction de la requête
        query = {
            "agency_id": agency_id,
            "timestamp": {"$gte": start_date, "$lte": end_date}
        }
        
        if muse_id:
            query["muse_id"] = muse_id
        if platform:
            query["platform"] = platform.value
        
        # Récupération des logs de plateforme
        logs = await db["platform_logs"].find(query).to_list(length=1000)
        
        # Agrégation par plateforme
        platform_stats = {}
        for log in logs:
            platform_name = log.get("platform")
            if platform_name not in platform_stats:
                platform_stats[platform_name] = {
                    "total_posts": 0,
                    "total_views": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0,
                    "total_earnings": 0,
                    "successful_posts": 0
                }
            
            platform_stats[platform_name]["total_posts"] += 1
            if log.get("status") == "success":
                platform_stats[platform_name]["successful_posts"] += 1
            
            # Extraction des métriques depuis les métadonnées
            metadata = log.get("metadata", {})
            platform_stats[platform_name]["total_views"] += metadata.get("views", 0)
            platform_stats[platform_name]["total_likes"] += metadata.get("likes", 0)
            platform_stats[platform_name]["total_comments"] += metadata.get("comments", 0)
            platform_stats[platform_name]["total_shares"] += metadata.get("shares", 0)
            platform_stats[platform_name]["total_earnings"] += metadata.get("earnings", 0)
        
        # Conversion en réponse
        analytics = []
        for platform_name, stats in platform_stats.items():
            try:
                platform_type = PlatformType(platform_name)
                engagement_rate = 0
                if stats["total_views"] > 0:
                    engagement_rate = (stats["total_likes"] + stats["total_comments"] + stats["total_shares"]) / stats["total_views"] * 100
                
                analytics.append(PlatformAnalytics(
                    platform=platform_type,
                    period_start=start_date,
                    period_end=end_date,
                    total_earnings=stats["total_earnings"],
                    total_posts=stats["total_posts"],
                    total_views=stats["total_views"],
                    total_likes=stats["total_likes"],
                    total_comments=stats["total_comments"],
                    total_shares=stats["total_shares"],
                    engagement_rate=engagement_rate
                ))
            except ValueError:
                # Plateforme non reconnue, ignorer
                continue
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/credentials", response_model=List[PlatformCredentials])
async def get_platform_credentials_list(
    agency_id: str = Query(..., description="ID de l'agence"),
    muse_id: Optional[str] = Query(None, description="ID de la muse"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère la liste des credentials des plateformes.
    """
    try:
        query = {"agency_id": agency_id}
        if muse_id:
            query["muse_id"] = muse_id
        
        credentials = await db["platform_credentials"].find(query).to_list(length=100)
        
        return [
            PlatformCredentials(
                platform=PlatformType(cred["platform"]),
                credentials=cred["credentials"],
                is_active=cred.get("is_active", True),
                created_at=cred.get("created_at", utcnow()),
                updated_at=cred.get("updated_at", utcnow())
            )
            for cred in credentials
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/credentials", response_model=PlatformCredentials)
async def create_platform_credentials(
    credentials: PlatformCredentials,
    agency_id: str = Query(..., description="ID de l'agence"),
    muse_id: Optional[str] = Query(None, description="ID de la muse"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Crée ou met à jour les credentials d'une plateforme.
    """
    try:
        doc = {
            "platform": credentials.platform.value,
            "credentials": credentials.credentials,
            "is_active": credentials.is_active,
            "agency_id": agency_id,
            "muse_id": muse_id,
            "created_at": utcnow(),
            "updated_at": utcnow()
        }
        
        # Vérification si les credentials existent déjà
        existing = await db["platform_credentials"].find_one({
            "platform": credentials.platform.value,
            "agency_id": agency_id,
            "muse_id": muse_id
        })
        
        if existing:
            # Mise à jour
            await db["platform_credentials"].update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "credentials": credentials.credentials,
                    "is_active": credentials.is_active,
                    "updated_at": utcnow()
                }}
            )
        else:
            # Création
            await db["platform_credentials"].insert_one(doc)
        
        return credentials
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/credentials/{platform}")
async def delete_platform_credentials(
    platform: PlatformType,
    agency_id: str = Query(..., description="ID de l'agence"),
    muse_id: Optional[str] = Query(None, description="ID de la muse"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Supprime les credentials d'une plateforme.
    """
    try:
        query = {
            "platform": platform.value,
            "agency_id": agency_id
        }
        if muse_id:
            query["muse_id"] = muse_id
        
        result = await db["platform_credentials"].delete_one(query)
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Credentials non trouvés")
        
        return {"message": "Credentials supprimés avec succès"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === Fonctions utilitaires ===
async def get_platform_credentials(agency_id: str, muse_id: str, platform: PlatformType) -> Dict[str, Any]:
    """Récupère les credentials d'une plateforme."""
    credentials = await db["platform_credentials"].find_one({
        "platform": platform.value,
        "agency_id": agency_id,
        "muse_id": muse_id,
        "is_active": True
    })
    
    if not credentials:
        raise Exception(f"Credentials manquants pour {platform.value}")
    
    return credentials.get("credentials", {})

def prepare_content_for_platform(content: ContentRequest, platform: PlatformType) -> Dict[str, Any]:
    """Prépare le contenu pour une plateforme spécifique."""
    base_content = {
        "id": f"content_{utcnow().timestamp()}",
        "text": content.text,
        "title": content.title,
        "media_urls": [str(url) for url in content.media_urls] if content.media_urls else [],
        "price": content.price,
        "tags": content.tags,
        "scheduled_at": content.scheduled_at.isoformat() if content.scheduled_at else None,
        "metadata": content.metadata or {}
    }
    
    # Adaptations spécifiques par plateforme
    if platform == PlatformType.TIKTOK:
        if content.media_urls:
            base_content["video_url"] = str(content.media_urls[0])
        base_content["description"] = content.text
    
    elif platform in [PlatformType.ONLYFANS, PlatformType.FANVUE]:
        if content.media_urls:
            base_content["media_url"] = str(content.media_urls[0])
        base_content["caption"] = content.text
        base_content["is_premium"] = (content.price or 0) > 0
    
    return base_content




