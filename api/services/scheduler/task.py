from services.content_distributor.dispatcher import dispatch_content
from pymongo import MongoClient
from datetime import datetime
import asyncio
from services.scheduler.logger import scheduler_logger

# Configuration MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["musemgmtdb"]

async def dispatch_scheduled_posts():
    now = datetime.utcnow()
    scheduled_posts = db.public_contents.find({"scheduled_at": {"$lte": now}, "status": "pending"})

    async for post in scheduled_posts:
        platforms = post.get("platforms", [])
        model_info = {
            "muse_id": post.get("muse_id"),
            "agency_id": post.get("agency_id"),
            "access_token": post.get("access_token", None)
        }

        try:
            result = await dispatch_content(post, platforms, model_info)

            # Mise à jour dans MongoDB
            db.public_contents.update_one(
                {"_id": post["_id"]},
                {"$set": {
                    "status": "dispatched",
                    "dispatched_result": result,
                    "dispatched_at": datetime.utcnow()
                }}
            )

            scheduler_logger.info(f"✅ Post {post['_id']} dispatched to {platforms} with result: {result}")

        except Exception as e:
            scheduler_logger.error(f"❌ Error dispatching post {post['_id']}: {str(e)}")
