from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PlatformConfig(BaseModel):
    name: str
    content_format: str
    posting_time: str  # HH:MM format
    cta: Optional[str]

class TunnelCreate(BaseModel):
    agency_id: str
    muse_id: str
    name: str
    platforms: List[PlatformConfig]
    is_active: Optional[bool] = True

class TunnelResponse(TunnelCreate):
    id: str
    created_at: datetime
