from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PPVContentCreate(BaseModel):
    agency_id: str
    title: str
    description: Optional[str] = None
    media_url: Optional[str] = None
    price_usdt: float

class PPVContentPublic(PPVContentCreate):
    id: str
    created_at: datetime
