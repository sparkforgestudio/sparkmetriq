# api/routes/webhooks/mymfans.py
from fastapi import APIRouter, Request, HTTPException, Depends, status
from typing import Dict, Any
import json
import os
import logging
from datetime import datetime

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.services.content_distributor.connectors.mymfans import MYMFansConnector
from api.databases.databases import db

# Configuration du logger
logger = logging.getLogger(__name__)

# Variables d'environnement
MYMFANS_WEBHOOK_SECRET = os.getenv("MYMFANS_WEBHOOK_SECRET")

router = APIRouter(prefix="/webhook/mymfans", tags=["MYM.fans Webhook"])

@router.post("/callback")
async def mymfans_webhook_callback(request: Request):
    """
    Endpoint pour recevoir les webhooks de MYM.fans.
    Traite les événements de publication, paiements, abonnements, etc.
    """
    try:
        # Récupération du payload
        payload_bytes = await request.body()
        payload = payload_bytes.decode('utf-8')
        
        # Vérification de la signature
        signature = request.headers.get("X-MYM-Signature")
        
        if not MYMFANS_WEBHOOK_SECRET:
            logger.warning("MYMFANS_WEBHOOK_SECRET non configuré. Impossible de vérifier la signature du webhook MYM.fans.")
        elif not signature:
            logger.warning("Signature MYM.fans manquante dans les headers du webhook.")
            raise HTTPException(status_code=400, detail="Signature manquante")
        else:
            if not MYMFansConnector.verify_webhook_signature(payload, signature, MYMFANS_WEBHOOK_SECRET):
                logger.error("Signature MYM.fans invalide.")
                raise HTTPException(status_code=403, detail="Signature invalide")

        # Parsing du payload JSON
        event_data = json.loads(payload)
        logger.info(f"Webhook MYM.fans reçu: {event_data}")

        # Traitement selon le type d'événement
        event_type = event_data.get("event_type")
        
        if event_type == "post.published":
            await handle_post_published(event_data)
        elif event_type == "post.purchased":
            await handle_post_purchased(event_data)
        elif event_type == "subscription.created":
            await handle_subscription_created(event_data)
        elif event_type == "subscription.cancelled":
            await handle_subscription_cancelled(event_data)
        elif event_type == "message.sent":
            await handle_message_sent(event_data)
        elif event_type == "payment.completed":
            await handle_payment_completed(event_data)
        else:
            logger.info(f"Type d'événement MYM.fans non géré: {event_type}")

        return {"message": "Webhook MYM.fans traité avec succès"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON invalide")
    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook MYM.fans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_post_published(event_data: Dict[str, Any]):
    """Traite l'événement de publication d'un post."""
    try:
        post_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "mymfans",
            "event_type": "post.published",
            "post_id": post_data.get("post_id"),
            "user_id": post_data.get("user_id"),
            "agency_id": post_data.get("agency_id"),
            "muse_id": post_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "title": post_data.get("title"),
                "price": post_data.get("price"),
                "is_premium": post_data.get("is_premium"),
                "media_count": len(post_data.get("media_urls", []))
            }
        })
        
        logger.info(f"Post MYM.fans publié: {post_data.get('post_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement post.published MYM.fans: {e}")

async def handle_post_purchased(event_data: Dict[str, Any]):
    """Traite l'événement d'achat d'un post."""
    try:
        purchase_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "mymfans",
            "event_type": "post.purchased",
            "post_id": purchase_data.get("post_id"),
            "buyer_id": purchase_data.get("buyer_id"),
            "seller_id": purchase_data.get("seller_id"),
            "agency_id": purchase_data.get("agency_id"),
            "muse_id": purchase_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "amount": purchase_data.get("amount"),
                "currency": purchase_data.get("currency"),
                "payment_method": purchase_data.get("payment_method")
            }
        })
        
        logger.info(f"Post MYM.fans acheté: {purchase_data.get('post_id')} par {purchase_data.get('buyer_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement post.purchased MYM.fans: {e}")

async def handle_subscription_created(event_data: Dict[str, Any]):
    """Traite l'événement de création d'un abonnement."""
    try:
        subscription_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "mymfans",
            "event_type": "subscription.created",
            "subscriber_id": subscription_data.get("subscriber_id"),
            "creator_id": subscription_data.get("creator_id"),
            "agency_id": subscription_data.get("agency_id"),
            "muse_id": subscription_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "plan_id": subscription_data.get("plan_id"),
                "plan_name": subscription_data.get("plan_name"),
                "amount": subscription_data.get("amount"),
                "currency": subscription_data.get("currency"),
                "billing_cycle": subscription_data.get("billing_cycle")
            }
        })
        
        logger.info(f"Abonnement MYM.fans créé: {subscription_data.get('subscriber_id')} -> {subscription_data.get('creator_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement subscription.created MYM.fans: {e}")

async def handle_subscription_cancelled(event_data: Dict[str, Any]):
    """Traite l'événement d'annulation d'un abonnement."""
    try:
        subscription_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "mymfans",
            "event_type": "subscription.cancelled",
            "subscriber_id": subscription_data.get("subscriber_id"),
            "creator_id": subscription_data.get("creator_id"),
            "agency_id": subscription_data.get("agency_id"),
            "muse_id": subscription_data.get("muse_id"),
            "timestamp": utcnow(),
            "metadata": {
                "plan_id": subscription_data.get("plan_id"),
                "cancellation_reason": subscription_data.get("cancellation_reason"),
                "effective_date": subscription_data.get("effective_date")
            }
        })
        
        logger.info(f"Abonnement MYM.fans annulé: {subscription_data.get('subscriber_id')} -> {subscription_data.get('creator_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement subscription.cancelled MYM.fans: {e}")

async def handle_message_sent(event_data: Dict[str, Any]):
    """Traite l'événement d'envoi d'un message privé."""
    try:
        message_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "mymfans",
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
                "message_length": len(message_data.get("content", ""))
            }
        })
        
        logger.info(f"Message MYM.fans envoyé: {message_data.get('message_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement message.sent MYM.fans: {e}")

async def handle_payment_completed(event_data: Dict[str, Any]):
    """Traite l'événement de paiement complété."""
    try:
        payment_data = event_data.get("data", {})
        
        # Enregistrer l'événement dans les logs
        await db["platform_logs"].insert_one({
            "platform": "mymfans",
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
                "fee": payment_data.get("fee")
            }
        })
        
        logger.info(f"Paiement MYM.fans complété: {payment_data.get('payment_id')}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement payment.completed MYM.fans: {e}")

@router.get("/verify")
async def verify_mymfans_webhook(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
):
    """
    Endpoint de vérification des webhooks MYM.fans.
    Utilisé lors de la configuration initiale du webhook.
    """
    verify_token = os.getenv("MYMFANS_VERIFY_TOKEN")
    
    if not verify_token:
        logger.warning("MYMFANS_VERIFY_TOKEN non configuré.")
        raise HTTPException(status_code=400, detail="Token de vérification non configuré")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook MYM.fans vérifié avec succès")
        return int(hub_challenge)
    else:
        logger.error("Échec de la vérification du webhook MYM.fans")
        raise HTTPException(status_code=403, detail="Token de vérification invalide")

@router.get("/analytics/{post_id}")
async def get_mymfans_post_analytics(
    post_id: str,
    start_date: str = None,
    end_date: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère les analytics d'un post MYM.fans.
    """
    try:
        # Récupérer les credentials MYM.fans de l'utilisateur
        credentials = await db["platform_credentials"].find_one({
            "user_id": current_user.id,
            "platform": "mymfans"
        })
        
        if not credentials:
            raise HTTPException(status_code=404, detail="Credentials MYM.fans non trouvés")
        
        # Initialiser le connecteur
        connector = MYMFansConnector(
            credentials["credentials"]["api_key"],
            credentials["credentials"]["api_secret"]
        )
        
        # Définir les dates par défaut si non fournies
        if not start_date:
            start_date = (utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = utcnow().strftime("%Y-%m-%d")
        
        # Récupérer les analytics
        analytics = await connector.get_post_analytics(post_id, start_date, end_date)
        
        return {
            "post_id": post_id,
            "start_date": start_date,
            "end_date": end_date,
            "analytics": analytics
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération analytics MYM.fans: {e}")
        raise HTTPException(status_code=500, detail=str(e))




