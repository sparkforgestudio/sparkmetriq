# api/schemas/scheduler.py
"""
Schémas Pydantic pour le Scheduler Multicanal Intelligent.
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

Platform = Literal["instagram","tiktok","reddit","twitter","telegram","onlyfans","threads"]

class MediaItem(BaseModel):
    url: str
    kind: Literal["image","video","carousel","story","reel","text"] = "image"
    meta: Dict[str, Any] = {}

class DraftIn(BaseModel):
    platform: Platform
    muse_id: str
    title: Optional[str] = None
    caption: Optional[str] = None
    hashtags: List[str] = []
    emojis: List[str] = []
    media: List[MediaItem] = []
    link_out: Optional[str] = None             # ex: lien OF/PPV
    scheduled_at: datetime
    timezone: str = "UTC"
    tone: Optional[str] = "flirty"             # style IA
    objective: Optional[str] = "teasing"       # teasing | conversion | growth
    nsfw_filter: Optional[bool] = False
    story: Optional[bool] = False
    reel: Optional[bool] = False
    ab_test_campaign_id: Optional[str] = None  # rattachement éventuel à un test A/B
    variant: Optional[Literal["A","B"]] = None # draft A ou B
    meta: Dict[str, Any] = {}

class Draft(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    status: Literal["scheduled","queued","published","failed","canceled"] = "scheduled"
    job_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # contenu
    platform: Platform
    muse_id: str
    title: Optional[str] = None
    caption: Optional[str] = None
    hashtags: List[str] = []
    emojis: List[str] = []
    media: List[MediaItem] = []
    link_out: Optional[str] = None
    scheduled_at: datetime
    timezone: str
    tone: Optional[str] = None
    objective: Optional[str] = None
    nsfw_filter: Optional[bool] = None
    story: Optional[bool] = None
    reel: Optional[bool] = None
    ab_test_campaign_id: Optional[str] = None
    variant: Optional[Literal["A","B"]] = None
    meta: Dict[str, Any] = {}

class PreviewRequest(BaseModel):
    platform: Platform
    muse_id: str
    prompt: str
    tone: Optional[str] = "flirty"
    objective: Optional[str] = "teasing"
    language: Optional[str] = "en"

class PreviewOut(BaseModel):
    caption: str
    hashtags: List[str] = []
    emojis: List[str] = []
    warnings: List[str] = []

class ABTestCreate(BaseModel):
    campaign_id: str
    platform: Platform
    muse_id: str
    hypothesis: str
    kpi: Literal["click","view","ppv_paid","engagement"]
    start_at: datetime
    end_at: datetime
    variants: List[DraftIn]  # exactement 2 drafts A/B

class RecyclePolicy(BaseModel):
    name: str
    active: bool = True
    selection: Literal["top_by_ctr","top_by_ppv","top_by_views"] = "top_by_ctr"
    lookback_days: int = 30
    max_per_week: int = 3
    reformat: List[Platform] = ["twitter","reddit","instagram"]
    filters: Dict[str, Any] = {}