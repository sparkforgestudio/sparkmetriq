from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

class SchedulePayload(BaseModel):
    agency_id: str
    muse_id: str
    platform: Literal["instagram", "tiktok", "telegram", "threads", "snapchat", "reddit", "twitter", "facebook", "onlyfans"]
    content: dict
    scheduled_at: datetime
    tags: Optional[List[str]] = None
    status: Optional[str] = "pending"
