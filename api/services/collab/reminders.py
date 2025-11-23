# api/services/collab/reminders.py
"""
Service de rappels pour les tâches de collaboration.
Scheduler pour vérifier les tâches en retard et envoyer des notifications.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from api.core.settings import settings
from api.databases.databases import get_core_db
from api.services.collab.ws import hub

logger = logging.getLogger(__name__)


async def check_overdue_tasks() -> int:
    """
    Vérifie les tâches en retard et envoie des notifications.
    
    Returns:
        Nombre de tâches en retard trouvées
    """
    if not settings.feature_collab_enabled:
        return 0
    
    db = get_core_db()
    now = datetime.now(timezone.utc)
    
    # Chercher les tâches en retard (due_at < now et status todo/in_progress)
    overdue_tasks = await db["collab_tasks"].find({
        "status": {"$in": ["todo", "in_progress"]},
        "due_at": {"$lt": now, "$ne": None}
    }).to_list(length=None)
    
    count = 0
    orgs_notified = set()
    
    for task in overdue_tasks:
        org_id = task.get("org_id")
        if not org_id:
            continue
        
        try:
            # Broadcast via WebSocket
            await hub.broadcast(
                org_id,
                {
                    "type": "collab.task.overdue",
                    "task": {
                        "id": str(task.get("_id")),
                        "title": task.get("title"),
                        "due_at": task.get("due_at").isoformat() if task.get("due_at") else None,
                        "assignees": task.get("assignees", [])
                    }
                }
            )
            
            orgs_notified.add(org_id)
            count += 1
            
            # Optionnel: Logger l'activité
            await db["collab_activity"].insert_one({
                "org_id": org_id,
                "type": "task_overdue_reminder",
                "task_id": str(task.get("_id")),
                "ts": now,
                "created_at": now
            })
            
        except Exception as e:
            logger.error(f"Error processing overdue task {task.get('_id')}: {e}")
    
    if count > 0:
        logger.info(f"Sent {count} overdue task reminders to {len(orgs_notified)} organizations")
    
    return count


# Fonction helper pour intégration avec APScheduler
def register_reminders_scheduler(scheduler):
    """
    Enregistre le job de vérification des rappels dans APScheduler.
    
    Args:
        scheduler: Instance APScheduler
        
    Note: Appeler cette fonction depuis api/main.py ou votre point d'entrée scheduler.
    """
    if not settings.feature_collab_enabled:
        logger.info("Collaboration disabled, not registering reminders scheduler")
        return
    
    interval_sec = settings.collab_reminder_interval_sec
    
    scheduler.add_job(
        check_overdue_tasks,
        trigger="interval",
        seconds=interval_sec,
        id="collab_reminders",
        replace_existing=True,
        max_instances=1
    )
    
    logger.info(f"Collaboration reminders scheduler registered (every {interval_sec} seconds)")




