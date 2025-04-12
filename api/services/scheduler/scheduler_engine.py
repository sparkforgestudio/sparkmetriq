import asyncio
from datetime import datetime
from services.databases import db
from services.content_distributor.dispatcher import dispatch_content
from services.content_distributor.logger import logger

async def scheduler_loop():
    while True:
        now = datetime.utcnow()
        tasks = await db["scheduled_tasks"].find({
            "scheduled_at": {"$lte": now},
            "status": "pending"
        }).to_list(length=10)

        for task in tasks:
            try:
                result = await dispatch_content(
                    task["content"],
                    [task["platform"]],
                    {"agency_id": task["agency_id"], "muse_id": task["muse_id"]}
                )
                await db["scheduled_tasks"].update_one(
                    {"_id": task["_id"]},
                    {"$set": {"status": "done", "result": result}}
                )
                logger.success(f"Tâche exécutée pour {task['platform']}")
            except Exception as e:
                await db["scheduled_tasks"].update_one(
                    {"_id": task["_id"]},
                    {"$set": {"status": "failed", "error": str(e)}}
                )
                logger.error(f"Erreur lors de la tâche planifiée : {str(e)}")
        
        await asyncio.sleep(30)  # Intervalle de vérification
