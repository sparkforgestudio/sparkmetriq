# api/services/ai/recap_scheduler.py
"""
Squelette pour le déclenchement automatique des recaps.
Non activé par défaut - nécessite RECAP_AUTO_ENABLED=true.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from api.core.settings import settings
from api.databases.databases import get_core_db
from api.schemas.recap import RecapGenerateIn
from api.services.ai.recap_service import generate_recap

logger = logging.getLogger(__name__)


async def scan_and_recap():
    """
    Scanne les conversations et génère des recaps automatiquement.
    
    Conditions:
    - RECAP_AUTO_ENABLED doit être True
    - Conversations inactives depuis RECAP_IDLE_MINUTES
    - Ou conversations avec >= RECAP_MIN_NEW_MSG nouveaux messages depuis dernier recap
    
    Note: Cette fonction doit être appelée périodiquement par APScheduler.
    """
    if not settings.recap_auto_enabled:
        logger.debug("Auto recap disabled, skipping scan")
        return
    
    if not settings.feature_convo_recap_enabled:
        logger.warning("Recap feature disabled, skipping auto recap")
        return
    
    db = get_core_db()
    idle_cut = datetime.now(timezone.utc) - timedelta(minutes=settings.recap_idle_minutes)
    
    try:
        # Agrégation pour trouver les conversations candidates
        # (inactives depuis idle_cut)
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$lt": idle_cut}
                }
            },
            {
                "$group": {
                    "_id": {
                        "org_id": "$org_id",
                        "conversation_id": "$conversation_id"
                    },
                    "last_ts": {"$max": "$timestamp"},
                    "message_count": {"$sum": 1},
                    "muse_id": {"$first": "$muse_id"},
                    "user_id": {"$first": "$user_id"}
                }
            },
            {
                "$match": {
                    "last_ts": {"$lt": idle_cut}
                }
            },
            {
                "$limit": 50  # Limiter le nombre de recaps par scan
            }
        ]
        
        candidates = await db["chat_messages"].aggregate(pipeline).to_list(length=None)
        
        logger.info(f"Found {len(candidates)} conversation candidates for auto recap")
        
        for candidate in candidates:
            org_id = candidate["_id"]["org_id"]
            conversation_id = candidate["_id"]["conversation_id"]
            muse_id = candidate.get("muse_id")
            user_id = candidate.get("user_id")
            
            try:
                # Vérifier s'il existe déjà un recap récent
                existing_recap = await db["conversation_recaps"].find_one({
                    "org_id": org_id,
                    "conversation_id": conversation_id
                })
                
                # Si recap existe et est récent, vérifier si assez de nouveaux messages
                if existing_recap:
                    last_recap_ts = existing_recap.get("updated_at")
                    if last_recap_ts:
                        # Compter les nouveaux messages depuis le dernier recap
                        new_msg_count = await db["chat_messages"].count_documents({
                            "org_id": org_id,
                            "conversation_id": conversation_id,
                            "timestamp": {"$gt": last_recap_ts}
                        })
                        
                        if new_msg_count < settings.recap_min_new_msg:
                            logger.debug(
                                f"Skipping {conversation_id}: only {new_msg_count} new messages "
                                f"(need {settings.recap_min_new_msg})"
                            )
                            continue
                
                # Générer le recap
                payload = RecapGenerateIn(
                    org_id=org_id,
                    conversation_id=conversation_id,
                    muse_id=muse_id,
                    user_id=user_id,
                    kind="full",
                    max_messages=settings.recap_max_messages_per_call
                )
                
                await generate_recap(payload)
                logger.info(f"Auto recap generated for conversation {conversation_id}")
                
            except Exception as e:
                logger.error(f"Error generating auto recap for {conversation_id}: {e}")
                # Continue avec les autres conversations
                continue
                
    except Exception as e:
        logger.error(f"Error in scan_and_recap: {e}", exc_info=True)


# Fonction helper pour intégration avec APScheduler
def register_recap_scheduler(scheduler):
    """
    Enregistre le job de recap automatique dans APScheduler.
    
    Args:
        scheduler: Instance APScheduler
        
    Note: Appeler cette fonction depuis api/main.py ou votre point d'entrée scheduler.
    """
    if not settings.recap_auto_enabled:
        logger.info("Auto recap disabled, not registering scheduler job")
        return
    
    # Exécuter toutes les 15 minutes (ajustable)
    scheduler.add_job(
        scan_and_recap,
        trigger="interval",
        minutes=15,
        id="recap_auto_scan",
        replace_existing=True,
        max_instances=1
    )
    
    logger.info("Auto recap scheduler job registered (every 15 minutes)")




