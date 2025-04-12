# services/logs/activity_logger.py
from datetime import datetime
from typing import Optional, Dict
from services.databases import db
from services.content_distributor.logger import logger


async def log_activity(
    action: str,
    status: str,
    platform: Optional[str] = None,
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    details: Optional[Dict] = None
):
    log_doc = {
        "timestamp": datetime.utcnow(),
        "type": action,            # e.g., "post", "schedule", "error", etc.
        "status": status,          # "success", "failed", "skipped"
        "platform": platform,      # "instagram", "tiktok", etc.
        "agency_id": agency_id,
        "muse_id": muse_id,
        "details": details or {}   # payload, error message, metadata...
    }
    await db["activity_logs"].insert_one(log_doc)
