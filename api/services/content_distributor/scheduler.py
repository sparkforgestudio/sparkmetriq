# services/content_distributor/scheduler.py

import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from services.content_distributor.dispatcher import dispatch_content
from services.content_distributor.logger import logger

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "musemgmtdb"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def process_pending_tasks():
    now = datetime.now(timezone.utc)
    tasks_cursor = db.scheduled_tasks.find({
        "scheduled_at": {"$lte": now},
        "status": "pending"
    })

    tasks = await tasks_cursor.to_list(length=100)

    for task in tasks:
        try:
            content = {
                "media": task["media"],
                "caption": task.get("caption", ""),
                "tags": task.get("tags", []),
                "language": task.get("language", "fr"),
                "is_sensitive": task.get("is_sensitive", False)
            }
            platforms = [task["platform"]]
            model_info = {
                "agency_id": task["agency_id"],
                "muse_id": task["muse_id"]
            }

            result = await dispatch_content(content, platforms, model_info)

            await db.scheduled_tasks.update_one(
                {"_id": task["_id"]},
                {"$set": {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc),
                    "result": result
                }}
            )

            logger.info(f"Tâche planifiée exécutée avec succès : {task['_id']}")

        except Exception as e:
            await db.scheduled_tasks.update_one(
                {"_id": task["_id"]},
                {"$set": {
                    "status": "error",
                    "error_message": str(e),
                    "attempted_at": datetime.now(timezone.utc)
                }}
            )

            logger.error(f"Échec de la tâche planifiée : {task['_id']} - {str(e)}")

async def scheduler_loop(interval_seconds: int = 60):
    while True:
        await process_pending_tasks()
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    asyncio.run(scheduler_loop())
