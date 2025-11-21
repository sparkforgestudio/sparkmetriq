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


# api/routes/tunnel_analysis.py
from fastapi import APIRouter, Depends, HTTPException
from api.core.auth import get_current_user
from api.schemas.tunnel_analysis import (
    TunnelAnalysisRequest,
    TunnelAnalysisResponse
)
from api.services.analytics.tunnels import analyze_tunnel  # à implémenter

router = APIRouter(prefix="/analysis/tunnel", tags=["analysis"])

@router.post("/recommendations", response_model=List[TunnelAnalysisResponse])
async def tunnel_recommendations(
    payload: TunnelAnalysisRequest,
    current_user = Depends(get_current_user)
):
    """
    Génère pour chaque muse un diagnostic du tunnel de vente
    et des recommandations actionnables.
    """
    try:
        results = await analyze_tunnel(
            agency_id=payload.agency_id,
            muse_id=payload.muse_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            granularity=payload.granularity
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
