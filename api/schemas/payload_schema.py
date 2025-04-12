# payload_schema.py
from typing import List, Literal, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class MediaItem(BaseModel):
    type: Literal["image", "video", "audio"]
    url: HttpUrl

class PublicContentPayload(BaseModel):
    agency_id: str
    muse_id: str
    platform: Literal["telegram", "instagram", "tiktok", "threads", "snapchat", "reddit", "twitter"]
    type: Literal["image", "video", "carousel", "story", "reel", "short"]
    media: List[MediaItem]
    caption: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    language: Optional[str] = "fr"
    is_sensitive: Optional[bool] = False
