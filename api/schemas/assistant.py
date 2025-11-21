# api/schemas/assistant.py
"""
Schémas Pydantic pour l'Assistant IA Stratégique.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class KPIWindow(BaseModel):
    date_from: datetime
    date_to: datetime

class Goal(BaseModel):
    name: str
    target_value: float
    unit: str
    rationale: Optional[str] = None

class ActionItem(BaseModel):
    title: str
    description: str
    channel: Literal["onlyfans","instagram","tiktok","reddit","twitter","telegram"]
    cta: str
    kpi: Optional[str] = None
    owner: Optional[str] = "creator"
    due_day: Optional[int] = None   # jour du mois recommandé
    effort: Optional[Literal["low","medium","high"]] = "low"

class ActionPlanIn(BaseModel):
    muse_id: str
    month: str                 # "YYYY-MM"
    goals: List[Goal] = []
    preferences: Dict[str, Any] = {}  # ton, niches, contraintes
    kpi_window: Optional[KPIWindow] = None

class ActionPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    muse_id: str
    month: str
    goals: List[Goal]
    actions: List[ActionItem]
    insights: List[str] = []
    created_at: datetime
    version: int = 1

class Alert(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    muse_id: str
    kind: Literal["growth_drop","over_perform","churn_high","trend_opportunity","pricing_issue"]
    message: str
    severity: Literal["low","medium","high"] = "medium"
    status: Literal["open","ack","closed"] = "open"
    ts: datetime

class CollabProfile(BaseModel):
    handle: str
    platform: Literal["instagram","tiktok","twitter","reddit","onlyfans"]
    audience_size: Optional[int] = None
    niche: Optional[str] = None
    similarity: float = 0.0
    sample_overlap: Optional[int] = None

class CollabSuggestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    muse_id: str
    profiles: List[CollabProfile]
    outreach_template: str
    ts: datetime

class TrendInsight(BaseModel):
    source: Literal["reddit","tiktok","twitter"]
    topic: str
    summary: str
    activation_idea: str
    score: float
    ts: datetime

class RecoRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tenant_id: str
    muse_id: str
    plan_month: Optional[str] = None
    recommendation: str
    applied: bool = False
    feedback: Optional[Literal["useful","not_useful","neutral"]] = None
    kpi_after: Optional[Dict[str, float]] = None
    ts: datetime



