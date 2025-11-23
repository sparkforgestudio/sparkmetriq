# api/schemas/tunnel_analysis.py
from datetime import date
from typing import List, Optional, Literal
from pydantic import BaseModel

class TunnelStageStats(BaseModel):
    stage: str
    posts: int
    conversions: int
    conversion_rate: float

class Recommendation(BaseModel):
    stage: str
    insight: str
    suggested_action: str

class TunnelAnalysisRequest(BaseModel):
    agency_id: str
    muse_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    granularity: Literal["daily", "weekly", "monthly"] = "daily"

class TunnelAnalysisResponse(BaseModel):
    muse_id: str
    funnel: List[TunnelStageStats]
    recommendations: List[Recommendation]

