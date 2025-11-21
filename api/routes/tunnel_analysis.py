from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict
from datetime import datetime, timedelta

from api.schemas.tunnel_analysis import TunnelStageStats, Recommendation, TunnelAnalysisResponse
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.routes.stats_tunnels import get_tunnel_overview

router = APIRouter(prefix="/analysis/tunnel", tags=["analysis"])

async def analyze_tunnel(
    agency_id: str,
    days: int,
    granularity: str
) -> List[TunnelAnalysisResponse]:
    end_date = utcnow()
    start_date = end_date - timedelta(days=days)

    # Récupère les stats agrégées du tunnel
    stats = await get_tunnel_overview(
        agency_id=agency_id,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity
    )

    # Regroupe par muse
    grouped: Dict[str, List[TunnelStageStats]] = {}
    for entry in stats:
        muse = entry.get("muse_id")
        stage_stats = TunnelStageStats(
            stage=entry.get("platform"),
            posts=entry.get("total", 0),
            conversions=entry.get("success", 0),
            conversion_rate=entry.get("success_rate", 0.0)
        )
        grouped.setdefault(muse, []).append(stage_stats)

    # Génère des recommandations simples
    responses: List[TunnelAnalysisResponse] = []
    for muse_id, funnel in grouped.items():
        recs: List[Recommendation] = []
        for stat in funnel:
            if stat.conversion_rate < 1.0:
                recs.append(Recommendation(message=f"Augmenter la fréquence des publications sur {stat.stage}"))
        responses.append(
            TunnelAnalysisResponse(
                muse_id=muse_id,
                funnel=funnel,
                recommendations=recs
            )
        )
    return responses

@router.post("/recommendations", response_model=List[TunnelAnalysisResponse])
async def get_tunnel_recommendations(
    days: int = Query(..., gt=0, description="Nombre de jours à analyser"),
    granularity: str = Query("daily", description="Granularité: daily, weekly ou monthly"),
    user: UserResponse = Depends(get_current_user)
):
    """
    Point d'API pour obtenir l'analyse du tunnel et des recommandations.
    Requiert d'être authentifié et retourne un tableau par muse.
    """
    try:
        return await analyze_tunnel(user.agency_id, days, granularity)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
