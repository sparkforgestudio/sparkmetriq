# api/routes/webhooks/manyvids.py
from fastapi import APIRouter, Request, HTTPException, Depends, status
from typing import Dict, Any
import json
import os
import logging
from datetime import datetime

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.services.content_distributor.connectors.manyvids import ManyVidsConnector
from api.databases.databases import db

# Configuration du logger
logger = logging.getLogger(__name__)

# Variables d'environnement
MANYVIDS_WEBHOOK_SECRET = os.getenv("MANYVIDS_WEBHOOK_SECRET")

router = APIRouter(prefix="/webhook/manyvids", tags=["ManyVids Webhook"])

@router.post("/callback")
async def manyvids_webhook_callback(request: Request):
    """
    Endpoint pour recevoir les webhooks de ManyVids.
    Traite les événements de vidéos, ventes, fans, messages, etc.
    """
    try:
        # Récupération du payload
        payload_bytes = await request.body()
        payload = payload_bytes.decode('utf-8')
        
        # Vérification de la signature
        signature = request.headers.get("X-ManyVids-Signature")
        
        if not MANYVIDS_WEBHOOK_SECRET:
            logger.warning("MANYVIDS_WEBHOOK_SECRET non configuré. Impossible de vérifier la signature du webhook ManyVids.")
        elif not signature:
            logger.warning("Signature ManyVids manquante dans les headers du webhook.")
            raise HTTPException(status_code=400, detail="Signature manquante")
        else:
            if not ManyVidsConnector.verify_webhook_signature(payload, signature, MANYVIDS_WEBHOOK_SECRET):
                logger.error("Signature ManyVids invalide.")
                raise HTTPException(status_code=403, detail="Signature invalide")

        # Parsing du payload JSON
        event_data = json.loads(payload)
        logger.info(f"Webhook ManyVids reçu: {event_data}")

        # Traitement selon le type d'événement
        event_type = event_data.get("event_type")
        
        if event_type == "video.uploaded":
            await handle_video_uploaded(event_data)
        elif event_type == "video.purchased":
            await handle_video_purchased(event_data)
        elif event_type == "custom_video.requested":
            await handle_custom_video_requested(event_data)
        elif event_type == "custom_video.completed":
            await handle_custom_video_completed(event_data)
        elif event_type == "fan.subscribed":
            await handle_fan_subscribed(event_data)
        elif event_type == "fan.unsubscribed":
            await handle_fan_unsubscribed(event_data)
        elif event_type == "message.sent":
            await handle_message_sent(event_data)
        elif event_type == "payment.completed":
            await handle_payment_completed(event_data)
        elif event_type == "video.analytics_updated":
            await handle_video_analytics_updated(event_data)
        else:
            logger.info(f"Type d'événement ManyVids non géré: {event_type}")

        return {"message": "Webhook ManyVids traité avec succès"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON invalide")
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook ManyVids: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_video_uploaded(event_data: Dict[str, Any]):
    """Traite l'événement d'upload d'une vidéo."""
    try:
        video_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "manyvids",
            "event_type": "video.uploaded",
            "video_id": video_data.get("video_id"),
            "user_id": video_data.get("user_id"),
            "agency_id": video_data.get("agency_id"),
            "muse_id": video_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "title": video_data.get("title"),
                "price": video_data.get("price"),
                "category": video_data.get("category"),
                "duration": video_data.get("duration"),
                "file_size": video_data.get("file_size"),
                "upload_status": video_data.get("upload_status")
            }
        })
        
        logger.info(f"Vidéo ManyVids uploadée: {video_data.get('video_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement video.uploaded ManyVids: {e}")

async def handle_video_purchased(event_data: Dict[str, Any]):
    """Traite l'événement d'achat d'une vidéo."""
    try:
        purchase_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "manyvids",
            "event_type": "video.purchased",
            "video_id": purchase_data.get("video_id"),
            "buyer_id": purchase_data.get("buyer_id"),
            "seller_id": purchase_data.get("seller_id"),
            "agency_id": purchase_data.get("agency_id"),
            "muse_id": purchase_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "amount": purchase_data.get("amount"),
                "currency": purchase_data.get("currency"),
                "payment_method": purchase_data.get("payment_method"),
                "video_title": purchase_data.get("video_title")
            }
        })
        
        logger.info(f"Vidéo ManyVids achetée: {purchase_data.get('video_id')} par {purchase_data.get('buyer_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement video.purchased ManyVids: {e}")

async def handle_custom_video_requested(event_data: Dict[str, Any]):
    """Traite l'événement de demande de vidéo personnalisée."""
    try:
        request_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "manyvids",
            "event_type": "custom_video.requested",
            "request_id": request_data.get("request_id"),
            "requester_id": request_data.get("requester_id"),
            "creator_id": request_data.get("creator_id"),
            "agency_id": request_data.get("agency_id"),
            "muse_id": request_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "title": request_data.get("title"),
                "description": request_data.get("description"),
                "budget": request_data.get("budget"),
                "deadline": request_data.get("deadline"),
                "special_requests": request_data.get("special_requests")
            }
        })
        
        logger.info(f"Demande vidéo personnalisée ManyVids: {request_data.get('request_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement custom_video.requested ManyVids: {e}")

async def handle_custom_video_completed(event_data: Dict[str, Any]):
    """Traite l'événement de vidéo personnalisée complétée."""
    try:
        completion_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "manyvids",
            "event_type": "custom_video.completed",
            "request_id": completion_data.get("request_id"),
            "video_id": completion_data.get("video_id"),
            "creator_id": completion_data.get("creator_id"),
            "requester_id": completion_data.get("requester_id"),
            "agency_id": completion_data.get("agency_id"),
            "muse_id": completion_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "final_amount": completion_data.get("final_amount"),
                "delivery_date": completion_data.get("delivery_date"),
                "satisfaction_rating": completion_data.get("satisfaction_rating")
            }
        })
        
        logger.info(f"Vidéo personnalisée ManyVids complétée: {completion_data.get('video_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement custom_video.completed ManyVids: {e}")

async def handle_fan_subscribed(event_data: Dict[str, Any]):
    """Traite l'événement d'abonnement d'un fan."""
    try:
        subscription_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "manyvids",
            "event_type": "fan.subscribed",
            "fan_id": subscription_data.get("fan_id"),
            "creator_id": subscription_data.get("creator_id"),
            "agency_id": subscription_data.get("agency_id"),
            "muse_id": subscription_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "subscription_type": subscription_data.get("subscription_type"),
                "amount": subscription_data.get("amount"),
                "billing_cycle": subscription_data.get("billing_cycle"),
                "fan_username": subscription_data.get("fan_username")
            }
        })
        
        logger.info(f"Fan ManyVids abonné: {subscription_data.get('fan_id')} -> {subscription_data.get('creator_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement fan.subscribed ManyVids: {e}")

async def handle_fan_unsubscribed(event_data: Dict[str, Any]):
    """Traite l'événement de désabonnement d'un fan."""
    try:
        unsubscription_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "manyvids",
            "event_type": "fan.unsubscribed",
            "fan_id": unsubscription_data.get("fan_id"),
            "creator_id": unsubscription_data.get("creator_id"),
            "agency_id": unsubscription_data.get("agency_id"),
            "muse_id": unsubscription_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "cancellation_reason": unsubscription_data.get("cancellation_reason"),
                "subscription_duration": unsubscription_data.get("subscription_duration"),
                "effective_date": unsubscription_data.get("effective_date")
            }
        })
        
        logger.info(f"Fan ManyVids désabonné: {unsubscription_data.get('fan_id')} -> {unsubscription_data.get('creator_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement fan.unsubscribed ManyVids: {e}")

async def handle_message_sent(event_data: Dict[str, Any]):
    """Traite l'événement d'envoi d'un message."""
    try:
        message_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "manyvids",
            "event_type": "message.sent",
            "message_id": message_data.get("message_id"),
            "sender_id": message_data.get("sender_id"),
            "recipient_id": message_data.get("recipient_id"),
            "agency_id": message_data.get("agency_id"),
            "muse_id": message_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "is_paid": message_data.get("is_paid"),
                "amount": message_data.get("amount"),
                "has_media": message_data.get("has_media"),
                "message_type": message_data.get("message_type")
            }
        })
        
        logger.info(f"Message ManyVids envoyé: {message_data.get('message_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement message.sent ManyVids: {e}")

async def handle_payment_completed(event_data: Dict[str, Any]):
    """Traite l'événement de paiement complété."""
    try:
        payment_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "manyvids",
            "event_type": "payment.completed",
            "payment_id": payment_data.get("payment_id"),
            "user_id": payment_data.get("user_id"),
            "agency_id": payment_data.get("agency_id"),
            "muse_id": payment_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "amount": payment_data.get("amount"),
                "currency": payment_data.get("currency"),
                "payment_method": payment_data.get("payment_method"),
                "transaction_type": payment_data.get("transaction_type"),
                "fee": payment_data.get("fee"),
                "net_amount": payment_data.get("net_amount")
            }
        })
        
        logger.info(f"Paiement ManyVids complété: {payment_data.get('payment_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement payment.completed ManyVids: {e}")

async def handle_video_analytics_updated(event_data: Dict[str, Any]):
    """Traite l'événement de mise à jour des analytics vidéo."""
    try:
        analytics_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "manyvids",
            "event_type": "video.analytics_updated",
            "video_id": analytics_data.get("video_id"),
            "user_id": analytics_data.get("user_id"),
            "agency_id": analytics_data.get("agency_id"),
            "muse_id": analytics_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "views": analytics_data.get("views"),
                "likes": analytics_data.get("likes"),
                "purchases": analytics_data.get("purchases"),
                "earnings": analytics_data.get("earnings"),
                "period": analytics_data.get("period")
            }
        })
        
        logger.info(f"Analytics vidéo ManyVids mises à jour: {analytics_data.get('video_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement video.analytics_updated ManyVids: {e}")

@router.get("/verify")
async def verify_manyvids_webhook(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
):
    """
    Endpoint de vérification des webhooks ManyVids.
    Utilisé lors de la configuration initiale du webhook.
    """
    verify_token = os.getenv("MANYVIDS_VERIFY_TOKEN")
    
    if not verify_token:
        logger.warning("MANYVIDS_VERIFY_TOKEN non configuré.")
        raise HTTPException(status_code=400, detail="Token de vérification non configuré")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook ManyVids vérifié avec succès")
        return int(hub_challenge)
    else:
        logger.error("Échec de la vérification du webhook ManyVids")
        raise HTTPException(status_code=403, detail="Token de vérification invalide")

@router.get("/analytics/{video_id}")
async def get_manyvids_video_analytics(
    video_id: str,
    start_date: str = None,
    end_date: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère les analytics d'une vidéo ManyVids.
    """
    try:
        # Récupérer les credentials ManyVids de l'utilisateur
        credentials = await db["platform_credentials"].find_one({
            "user_id": current_user.id,
            "platform": "manyvids"
        })
        
        if not credentials:
            raise HTTPException(status_code=404, detail="Credentials ManyVids non trouvés")
        
        # Initialiser le connecteur
        connector = ManyVidsConnector(
            credentials["credentials"]["api_key"],
            credentials["credentials"]["api_secret"]
        )
        
        # Définir les dates par défaut si non fournies
        if not start_date:
            start_date = (utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = utcnow().strftime("%Y-%m-%d")
        
        # Récupérer les analytics
        analytics = await connector.get_video_analytics(video_id, start_date, end_date)
        
        return {
            "video_id": video_id,
            "start_date": start_date,
            "end_date": end_date,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération analytics ManyVids: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_manyvids_categories(current_user: UserResponse = Depends(get_current_user)):
    """
    Récupère les catégories disponibles sur ManyVids.
    """
    try:
        # Récupérer les credentials ManyVids de l'utilisateur
        credentials = await db["platform_credentials"].find_one({
            "user_id": current_user.id,
            "platform": "manyvids"
        })
        
        if not credentials:
            raise HTTPException(status_code=404, detail="Credentials ManyVids non trouvés")
        
        # Initialiser le connecteur
        connector = ManyVidsConnector(
            credentials["credentials"]["api_key"],
            credentials["credentials"]["api_secret"]
        )
        
        # Récupérer les catégories
        categories = await connector.get_categories()
        
        return categories
        
    except Exception as e:
        logger.error(f"Erreur récupération catégories ManyVids: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending/tags")
async def get_manyvids_trending_tags(current_user: UserResponse = Depends(get_current_user)):
    """
    Récupère les tags tendance sur ManyVids.
    """
    try:
        # Récupérer les credentials ManyVids de l'utilisateur
        credentials = await db["platform_credentials"].find_one({
            "user_id": current_user.id,
            "platform": "manyvids"
        })
        
        if not credentials:
            raise HTTPException(status_code=404, detail="Credentials ManyVids non trouvés")
        
        # Initialiser le connecteur
        connector = ManyVidsConnector(
            credentials["credentials"]["api_key"],
            credentials["credentials"]["api_secret"]
        )
        
        # Récupérer les tags tendance
        trending_tags = await connector.get_trending_tags()
        
        return trending_tags
        
    except Exception as e:
        logger.error(f"Erreur récupération tags tendance ManyVids: {e}")
        raise HTTPException(status_code=500, detail=str(e))



