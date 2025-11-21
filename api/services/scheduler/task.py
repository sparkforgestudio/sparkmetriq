# api/services/scheduler/task.py

from datetime         import datetime
from api.databases.databases import db
from api.services.scheduler.logger import scheduler_logger
from api.services.content_distributor.dispatcher import get_dispatcher

async def dispatch_scheduled_posts():
    now = utcnow()
    cursor = db["scheduled_tasks"].find({
        "scheduled_at": {"$lte": now},
        "status":       "pending"
    })
    # Ici on récupère **tous** les documents dans une liste asynchrone
    scheduled_posts = await cursor.to_list(length=None)

    dispatcher = get_dispatcher()
    for post in scheduled_posts:
        try:
            await dispatcher.dispatch(
                platform= post["platform"],
                content=  post["content"],
                agency_id=post["agency_id"],
                muse_id=post.get("muse_id")
            )
            await db["scheduled_tasks"].update_one(
                {"_id": post["_id"]},
                {"$set": {
                    "status":       "dispatched",
                    "dispatched_at": utcnow()
                }}
            )
            scheduler_logger.info(f"Tâche {post['_id']} dispatchée.")
        except Exception as e:
            scheduler_logger.error(f"Échec dispatch {post['_id']}: {e}")
            await db["scheduled_tasks"].update_one(
                {"_id": post["_id"]},
                {"$set": {
                    "status":        "error",
                    "error_message": str(e)
                }}
            )
