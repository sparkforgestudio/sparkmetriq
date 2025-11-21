# api/routes/webhooks/tiktok.py
from fastapi import APIRouter, Request, HTTPException, Depends, status
from typing import Dict, Any
import json
import os
import logging
from datetime import datetime

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.services.content_distributor.connectors.tiktok import TikTokConnector
from api.databases.databases import db

# Configuration du logger
logger = logging.getLogger(__name__)

# Variables d'environnement
TIKTOK_WEBHOOK_SECRET = os.getenv("TIKTOK_WEBHOOK_SECRET")

router = APIRouter(prefix="/webhook/tiktok", tags=["TikTok Webhook"])

@router.post("/callback")
async def tiktok_webhook_callback(request: Request):
    """
    Webhook TikTok pour recevoir les notifications de publication et d'analytics.
    """
    try:
        # Récupération du payload
        body = await request.body()
        payload = json.loads(body.decode('utf-8'))
        
        # Vérification de la signature (optionnel mais recommandé)
        signature = request.headers.get("X-TikTok-Signature")
        if signature and TIKTOK_WEBHOOK_SECRET:
            if not TikTokConnector.verify_webhook_signature(
                body.decode('utf-8'), 
                signature, 
                TIKTOK_WEBHOOK_SECRET
            ):
                raise HTTPException(status_code=401, detail="Signature invalide")
        
        # Traitement selon le type d'événement
        event_type = payload.get("event")
        
        if event_type == "video.publish":
            await handle_video_publish_event(payload)
        elif event_type == "video.status":
            await handle_video_status_event(payload)
        elif event_type == "analytics":
            await handle_analytics_event(payload)
        else:
            logger.info(f"Événement TikTok non géré: {event_type}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Erreur webhook TikTok: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_video_publish_event(payload: Dict[str, Any]):
    """Gère les événements de publication de vidéo."""
    try:
        video_data = payload.get("data", {})
        publish_id = video_data.get("publish_id")
        video_id = video_data.get("video_id")
        status = video_data.get("status")
        
        # Mise à jour en base de données
        await db["tiktok_posts"].update_one(
            {"publish_id": publish_id},
            {
                "$set": {
                    "video_id": video_id,
                    "status": status,
                    "published_at": utcnow(),
                    "webhook_data": payload
                }
            }
        )
        
        logger.info(f"Vidéo TikTok publiée: {video_id} (publish_id: {publish_id})")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement publication: {e}")

async def handle_video_status_event(payload: Dict[str, Any]):
    """Gère les événements de changement de statut de vidéo."""
    try:
        video_data = payload.get("data", {})
        video_id = video_data.get("video_id")
        status = video_data.get("status")
        reason = video_data.get("reason")
        
        # Mise à jour du statut
        await db["tiktok_posts"].update_one(
            {"video_id": video_id},
            {
                "$set": {
                    "status": status,
                    "status_reason": reason,
                    "status_updated_at": utcnow(),
                    "webhook_data": payload
                }
            }
        )
        
        logger.info(f"Statut vidéo TikTok mis à jour: {video_id} -> {status}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement statut: {e}")

async def handle_analytics_event(payload: Dict[str, Any]):
    """Gère les événements d'analytics."""
    try:
        analytics_data = payload.get("data", {})
        video_id = analytics_data.get("video_id")
        metrics = analytics_data.get("metrics", {})
        
        # Sauvegarde des analytics
        await db["tiktok_analytics"].insert_one({
            "video_id": video_id,
            "metrics": metrics,
            "timestamp": utcnow(),
            "webhook_data": payload
        })
        
        logger.info(f"Analytics TikTok reçus pour vidéo: {video_id}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement analytics: {e}")

@router.get("/verify")
async def tiktok_webhook_verify(request: Request):
    """
    Endpoint de vérification pour TikTok (challenge-response).
    """
    try:
        # Récupération des paramètres de vérification
        challenge = request.query_params.get("hub.challenge")
        verify_token = request.query_params.get("hub.verify_token")
        
        # Vérification du token (doit correspondre à celui configuré dans TikTok)
        expected_token = os.getenv("TIKTOK_VERIFY_TOKEN")
        if verify_token != expected_token:
            raise HTTPException(status_code=403, detail="Token de vérification invalide")
        
        # Retour du challenge
        return int(challenge) if challenge else HTTPException(status_code=400, detail="Challenge manquant")
        
    except Exception as e:
        logger.error(f"Erreur vérification webhook TikTok: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{video_id}")
async def get_tiktok_video_analytics(
    video_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère les analytics d'une vidéo TikTok.
    """
    try:
        # Récupération des analytics depuis la base
        analytics = await db["tiktok_analytics"].find(
            {"video_id": video_id}
        ).sort("timestamp", -1).limit(30).to_list(length=30)
        
        return {
            "video_id": video_id,
            "analytics": analytics,
            "total_records": len(analytics)
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération analytics TikTok: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts")
async def get_tiktok_posts(
    limit: int = 20,
    status: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère la liste des posts TikTok.
    """
    try:
        query = {}
        if status:
            query["status"] = status
        
        posts = await db["tiktok_posts"].find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        return {
            "posts": posts,
            "total": len(posts)
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération posts TikTok: {e}")
        raise HTTPException(status_code=500, detail=str(e))
