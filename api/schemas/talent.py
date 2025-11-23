# api/schemas/talent.py
"""
Schémas Pydantic pour la Gestion Centralisée des Talents.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

Platform = Literal["instagram","tiktok","reddit","twitter","telegram","onlyfans","threads"]

class Thread(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    muse_id: str
    user_hash: str               # hash pseudo-anonyme du fan
    platform: Platform
    last_message: Optional[str] = None
    last_ts: datetime
    unseen_count: int = 0
    priority: int = 0
    tags: List[str] = []

class ThreadFilter(BaseModel):
    muse_id: Optional[str] = None
    platform: Optional[Platform] = None
    status: Optional[Literal["new","replied","vip","ppv_sent","escalated"]] = None
    q: Optional[str] = None
    page: int = 1
    page_size: int = 25

class TagRequest(BaseModel):
    muse_id: str
    user_hash: str
    tag: str

class NoteIn(BaseModel):
    muse_id: str
    user_hash: str
    text: str

class Note(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    muse_id: str
    user_hash: str
    text: str
    author_id: str
    ts: datetime

class RoleGrant(BaseModel):
    user_id: str
    role: Literal["operator","strategist","supervisor","lead_agent","admin"]

class AssignmentIn(BaseModel):
    muse_id: str
    platform: Platform
    operator_id: str

class Assignment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    muse_id: str
    platform: Platform
    operator_id: str

class AuditEventIn(BaseModel):
    muse_id: Optional[str] = None
    user_hash: Optional[str] = None
    action: str                 # e.g. "reply_sent", "tag_added", "escalated", "role_granted"
    meta: Dict[str, Any] = {}

class AuditEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    actor_id: str
    muse_id: Optional[str]
    user_hash: Optional[str]
    action: str
    meta: Dict[str, Any]
    ts: datetime

class HookIn(BaseModel):
    provider: Literal["clickup","notion","sheets","zapier"]
    config: Dict[str, Any]     # tokens/ids stockés chiffrés côté keystore si dispo

class Hook(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    provider: str
    config: Dict[str, Any]
    created_at: datetime

class MuseDashboardRow(BaseModel):
    muse_id: str
    revenue_7d: float = 0.0
    replies_rate_7d: float = 0.0
    ppv_conv_rate_7d: float = 0.0
    growth_msgs_7d: float = 0.0
    status: Literal["ok","at_risk","inactive"] = "ok"

class SegmentQuery(BaseModel):
    segment: Optional[str] = None  # ex "cosplay","fitness","fetish"
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class ThreadMessage(BaseModel):
    """Message dans un thread de conversation."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    thread_id: str
    role: Literal["user", "bot", "operator"]
    text: str
    platform: Platform
    timestamp: datetime
    attachments: Optional[List[str]] = None
    metadata: Dict[str, Any] = {}

class ThreadSummary(BaseModel):
    """Résumé d'un thread avec métriques."""
    model_config = ConfigDict(from_attributes=True)
    thread: Thread
    message_count: int = 0
    last_activity: Optional[datetime] = None
    assigned_operator: Optional[str] = None
    notes_count: int = 0
    tags_count: int = 0

class OperatorStats(BaseModel):
    """Statistiques d'un opérateur."""
    model_config = ConfigDict(from_attributes=True)
    operator_id: str
    assigned_muses: List[str] = []
    total_threads: int = 0
    active_threads: int = 0
    replies_today: int = 0
    avg_response_time: Optional[float] = None  # en minutes
    performance_score: float = 0.0

class AgencyMetrics(BaseModel):
    """Métriques consolidées de l'agence."""
    model_config = ConfigDict(from_attributes=True)
    total_muses: int = 0
    active_operators: int = 0
    total_revenue_7d: float = 0.0
    avg_response_rate: float = 0.0
    total_threads: int = 0
    escalated_threads: int = 0
    top_performing_muse: Optional[str] = None
    at_risk_muses: List[str] = []




