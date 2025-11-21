# api/services/messaging/outbox_worker.py
"""
Worker pour l'envoi automatique des messages depuis l'outbox.
Intègre avec le dispatcher existant pour envoyer les messages aux plateformes.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId

from api.core.settings import settings
from api.databases.databases import get_core_db

logger = logging.getLogger(__name__)


async def process_outbox(batch_size: Optional[int] = None) -> dict:
    """
    Traite les messages en queue dans l'outbox et les envoie via le dispatcher.
    
    Args:
        batch_size: Taille du batch (défaut: MB_RATE_PER_MINUTE)
        
    Returns:
        Statistiques de traitement
    """
    if not settings.feature_message_builder_enabled:
        logger.debug("Message builder disabled, skipping outbox processing")
        return {"processed": 0, "sent": 0, "failed": 0}
    
    if not settings.mb_enable_scheduler:
        logger.debug("Outbox scheduler disabled, skipping processing")
        return {"processed": 0, "sent": 0, "failed": 0}
    
    db = get_core_db()
    limit = batch_size or settings.mb_rate_per_minute
    now = datetime.now(timezone.utc)
    
    # Récupérer les messages en queue et prêts à être envoyés
    query = {
        "status": "queued",
        "scheduled_at": {"$lte": now}
    }
    
    cursor = (
        db["outbox_messages"]
        .find(query)
        .sort("scheduled_at", 1)
        .limit(limit)
    )
    
    messages = await cursor.to_list(length=limit)
    
    stats = {
        "processed": len(messages),
        "sent": 0,
        "failed": 0
    }
    
    for msg_doc in messages:
        try:
            # Extraire les informations nécessaires
            platform = msg_doc["platform"]
            user_ref = msg_doc["user_ref"]
            message_text = msg_doc["message"]
            org_id = msg_doc["org_id"]
            campaign_id = msg_doc.get("campaign_id")
            muse_id = msg_doc.get("muse_id")
            
            # Envoyer via les connectors selon la plateforme
            # Note: adapter selon votre implémentation réelle des connectors
            from api.services.content_distributor.dispatcher import PLATFORM_DISPATCHERS
            
            if platform not in PLATFORM_DISPATCHERS:
                raise ValueError(f"Platform {platform} not supported")
            
            # Préparer le contenu pour le dispatcher
            content = {
                "text": message_text,
                "chat_id": user_ref,  # user_ref est généralement le chat_id/user_id
                "message_type": "dm"  # Message direct
            }
            
            model_info = {
                "agency_id": org_id,
                "muse_id": muse_id or ""
            }
            
            # Appeler la fonction de publication de la plateforme
            dispatch_func = PLATFORM_DISPATCHERS[platform]
            result = await dispatch_func(content, model_info)
            
            # Vérifier le résultat
            if result.get("status") != "success":
                raise Exception(f"Platform returned error: {result.get('reason', 'Unknown error')}")
            
            # Marquer comme envoyé
            await db["outbox_messages"].update_one(
                {"_id": msg_doc["_id"]},
                {
                    "$set": {
                        "status": "sent",
                        "sent_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            stats["sent"] += 1
            
            # Mettre à jour les totaux de la campagne
            if campaign_id:
                try:
                    await db["campaigns"].update_one(
                        {"_id": ObjectId(campaign_id)},
                        {
                            "$inc": {"totals.sent": 1},
                            "$set": {"updated_at": datetime.now(timezone.utc)}
                        }
                    )
                    
                    # Émettre événement analytics
                    from api.services.analytics.events import emit_campaign_event
                    try:
                        await emit_campaign_event(org_id, campaign_id, "sent", 1)
                    except Exception as e:
                        logger.warning(f"Error emitting campaign event: {e}")
                except Exception as e:
                    logger.warning(f"Error updating campaign {campaign_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error sending message {msg_doc.get('_id')}: {e}")
            
            # Marquer comme échoué
            await db["outbox_messages"].update_one(
                {"_id": msg_doc["_id"]},
                {
                    "$set": {
                        "status": "failed",
                        "fail_reason": str(e)[:500],  # Limiter la longueur
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            stats["failed"] += 1
            
            # Mettre à jour les totaux de la campagne
            if campaign_id:
                try:
                    await db["campaigns"].update_one(
                        {"_id": ObjectId(campaign_id)},
                        {
                            "$inc": {"totals.failed": 1},
                            "$set": {"updated_at": datetime.now(timezone.utc)}
                        }
                    )
                    
                    # Émettre événement analytics
                    from api.services.analytics.events import emit_campaign_event
                    try:
                        await emit_campaign_event(org_id, campaign_id, "failed", 1)
                    except Exception as e2:
                        logger.warning(f"Error emitting campaign event: {e2}")
                except Exception as e2:
                    logger.warning(f"Error updating campaign {campaign_id}: {e2}")
    
    return stats


# Fonction helper pour intégration avec APScheduler
def register_outbox_worker(scheduler):
    """
    Enregistre le job de traitement de l'outbox dans APScheduler.
    
    Args:
        scheduler: Instance APScheduler
        
    Note: Appeler cette fonction depuis api/main.py ou votre point d'entrée scheduler.
    """
    if not settings.mb_enable_scheduler:
        logger.info("Outbox scheduler disabled, not registering worker job")
        return
    
    # Exécuter toutes les minutes
    scheduler.add_job(
        process_outbox,
        trigger="interval",
        minutes=1,
        id="outbox_worker",
        replace_existing=True,
        max_instances=1
    )
    
    logger.info("Outbox worker job registered (every 1 minute)")
