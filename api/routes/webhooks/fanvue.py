# api/routes/webhooks/fanvue.py
from fastapi import APIRouter, Request, HTTPException, Depends, status
from typing import Dict, Any
import json
import os
import logging
from datetime import datetime

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.services.content_distributor.connectors.fanvue import FanvueConnector
from api.databases.databases import db

# Configuration du logger
logger = logging.getLogger(__name__)

# Variables d'environnement
FANVUE_WEBHOOK_SECRET = os.getenv("FANVUE_WEBHOOK_SECRET")

router = APIRouter(prefix="/webhook/fanvue", tags=["Fanvue Webhook"])

@router.post("/callback")
async def fanvue_webhook_callback(request: Request):
    """
    Webhook Fanvue pour recevoir les notifications de publication, paiements et analytics.
    """
    try:
        # Récupération du payload
        body = await request.body()
        payload = json.loads(body.decode('utf-8'))
        
        # Vérification de la signature
        signature = request.headers.get("X-Fanvue-Signature")
        if signature and FANVUE_WEBHOOK_SECRET:
            if not FanvueConnector.verify_webhook_signature(
                body.decode('utf-8'), 
                signature, 
                FANVUE_WEBHOOK_SECRET
            ):
                raise HTTPException(status_code=401, detail="Signature invalide")
        
        # Traitement selon le type d'événement
        event_type = payload.get("event")
        
        if event_type == "post.created":
            await handle_post_created_event(payload)
        elif event_type == "post.purchased":
            await handle_post_purchased_event(payload)
        elif event_type == "subscription.created":
            await handle_subscription_created_event(payload)
        elif event_type == "payment.completed":
            await handle_payment_completed_event(payload)
        elif event_type == "analytics.updated":
            await handle_analytics_updated_event(payload)
        else:
            logger.info(f"Événement Fanvue non géré: {event_type}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Erreur webhook Fanvue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_post_created_event(payload: Dict[str, Any]):
    """Gère les événements de création de post."""
    try:
        post_data = payload.get("data", {})
        post_id = post_data.get("post_id")
        title = post_data.get("title")
        price = post_data.get("price", 0)
        is_premium = post_data.get("is_premium", False)
        
        # Sauvegarde en base de données
        await db["fanvue_posts"].insert_one({
            "post_id": post_id,
            "title": title,
            "price": price,
            "is_premium": is_premium,
            "created_at": utcnow(),
            "webhook_data": payload
        })
        
        logger.info(f"Post Fanvue créé: {post_id} - {title}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement création post: {e}")

async def handle_post_purchased_event(payload: Dict[str, Any]):
    """Gère les événements d'achat de post."""
    try:
        purchase_data = payload.get("data", {})
        post_id = purchase_data.get("post_id")
        buyer_id = purchase_data.get("buyer_id")
        amount = purchase_data.get("amount", 0)
        commission = purchase_data.get("commission", 0)
        
        # Sauvegarde de l'achat
        await db["fanvue_purchases"].insert_one({
            "post_id": post_id,
            "buyer_id": buyer_id,
            "amount": amount,
            "commission": commission,
            "purchased_at": utcnow(),
            "webhook_data": payload
        })
        
        # Mise à jour des statistiques du post
        await db["fanvue_posts"].update_one(
            {"post_id": post_id},
            {
                "$inc": {
                    "purchase_count": 1,
                    "total_earnings": amount - commission
                },
                "$set": {
                    "last_purchase_at": utcnow()
                }
            }
        )
        
        logger.info(f"Post Fanvue acheté: {post_id} par {buyer_id} pour {amount}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement achat post: {e}")

async def handle_subscription_created_event(payload: Dict[str, Any]):
    """Gère les événements de création d'abonnement."""
    try:
        subscription_data = payload.get("data", {})
        subscriber_id = subscription_data.get("subscriber_id")
        plan_id = subscription_data.get("plan_id")
        amount = subscription_data.get("amount", 0)
        billing_cycle = subscription_data.get("billing_cycle", "monthly")
        
        # Sauvegarde de l'abonnement
        await db["fanvue_subscriptions"].insert_one({
            "subscriber_id": subscriber_id,
            "plan_id": plan_id,
            "amount": amount,
            "billing_cycle": billing_cycle,
            "created_at": utcnow(),
            "webhook_data": payload
        })
        
        logger.info(f"Abonnement Fanvue créé: {subscriber_id} - Plan {plan_id}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement abonnement: {e}")

async def handle_payment_completed_event(payload: Dict[str, Any]):
    """Gère les événements de paiement complété."""
    try:
        payment_data = payload.get("data", {})
        payment_id = payment_data.get("payment_id")
        amount = payment_data.get("amount", 0)
        currency = payment_data.get("currency", "USD")
        payment_method = payment_data.get("payment_method")
        
        # Sauvegarde du paiement
        await db["fanvue_payments"].insert_one({
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "completed_at": utcnow(),
            "webhook_data": payload
        })
        
        logger.info(f"Paiement Fanvue complété: {payment_id} - {amount} {currency}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement paiement: {e}")

async def handle_analytics_updated_event(payload: Dict[str, Any]):
    """Gère les événements de mise à jour d'analytics."""
    try:
        analytics_data = payload.get("data", {})
        post_id = analytics_data.get("post_id")
        metrics = analytics_data.get("metrics", {})
        
        # Sauvegarde des analytics
        await db["fanvue_analytics"].insert_one({
            "post_id": post_id,
            "metrics": metrics,
            "timestamp": utcnow(),
            "webhook_data": payload
        })
        
        logger.info(f"Analytics Fanvue mis à jour pour post: {post_id}")
        
    except Exception as e:
        logger.error(f"Erreur traitement événement analytics: {e}")

@router.get("/verify")
async def fanvue_webhook_verify(request: Request):
    """
    Endpoint de vérification pour Fanvue (challenge-response).
    """
    try:
        # Récupération des paramètres de vérification
        challenge = request.query_params.get("hub.challenge")
        verify_token = request.query_params.get("hub.verify_token")
        
        # Vérification du token
        expected_token = os.getenv("FANVUE_VERIFY_TOKEN")
        if verify_token != expected_token:
            raise HTTPException(status_code=403, detail="Token de vérification invalide")
        
        # Retour du challenge
        return int(challenge) if challenge else HTTPException(status_code=400, detail="Challenge manquant")
        
    except Exception as e:
        logger.error(f"Erreur vérification webhook Fanvue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{post_id}")
async def get_fanvue_post_analytics(
    post_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère les analytics d'un post Fanvue.
    """
    try:
        # Récupération des analytics depuis la base
        analytics = await db["fanvue_analytics"].find(
            {"post_id": post_id}
        ).sort("timestamp", -1).limit(30).to_list(length=30)
        
        return {
            "post_id": post_id,
            "analytics": analytics,
            "total_records": len(analytics)
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération analytics Fanvue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/earnings")
async def get_fanvue_earnings(
    start_date: str = None,
    end_date: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère les revenus Fanvue pour une période.
    """
    try:
        query = {}
        if start_date and end_date:
            query["completed_at"] = {
                "$gte": datetime.fromisoformat(start_date),
                "$lte": datetime.fromisoformat(end_date)
            }
        
        payments = await db["fanvue_payments"].find(query).sort("completed_at", -1).to_list(length=1000)
        
        total_earnings = sum(payment.get("amount", 0) for payment in payments)
        
        return {
            "payments": payments,
            "total_earnings": total_earnings,
            "total_payments": len(payments)
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération revenus Fanvue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts")
async def get_fanvue_posts(
    limit: int = 20,
    is_premium: bool = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère la liste des posts Fanvue.
    """
    try:
        query = {}
        if is_premium is not None:
            query["is_premium"] = is_premium
        
        posts = await db["fanvue_posts"].find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        return {
            "posts": posts,
            "total": len(posts)
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération posts Fanvue: {e}")
        raise HTTPException(status_code=500, detail=str(e))
