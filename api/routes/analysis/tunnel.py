from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from datetime import datetime

from api.schemas.tunnels import (
    TunnelOverviewItem,
    TunnelDetailItem,
    TunnelCSVRecord,
    TunnelRecommendationsResponse,
)
from api.core.auth import get_current_user
from api.services.analytics.tunnels import (
    get_tunnel_overview,
    get_tunnel_details,
    fetch_csv_data,
    analyze_tunnel,
)

router = APIRouter(
    prefix="/analysis/tunnel",
    tags=["analysis"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/overview",
    response_model=List[TunnelOverviewItem],
    summary="Aperçu des statistiques du tunnel",
)
async def tunnel_overview(
    agency_id: Optional[str] = Query(None, description="Filtrer par agence"),
    muse_id: Optional[str] = Query(None, description="Filtrer par muse"),
    platform: Optional[str] = Query(None, description="Filtrer par plateforme"),
    funnel_stage: Optional[str] = Query(None, description="Filtrer par étape du tunnel"),
    content_type: Optional[str] = Query(None, description="Filtrer par type de contenu"),
    start_date: Optional[datetime] = Query(None, description="Date de début (ISO)"),
    end_date: Optional[datetime] = Query(None, description="Date de fin (ISO)"),
    granularity: str = Query("daily", description="daily | weekly | monthly"),
):
    try:
        return await get_tunnel_overview(
            agency_id=agency_id,
            muse_id=muse_id,
            platform=platform,
            funnel_stage=funnel_stage,
            content_type=content_type,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/details",
    response_model=List[TunnelDetailItem],
    summary="Détails des logs du tunnel",
)
async def tunnel_details(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    try:
        return await get_tunnel_details(
            agency_id=agency_id,
            muse_id=muse_id,
            platform=platform,
            funnel_stage=funnel_stage,
            content_type=content_type,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/export",
    response_model=List[TunnelCSVRecord],
    summary="Export CSV des données du tunnel",
)
async def tunnel_export(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    try:
        return await fetch_csv_data(
            agency_id=agency_id,
            muse_id=muse_id,
            platform=platform,
            funnel_stage=funnel_stage,
            content_type=content_type,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommendations",
    response_model=List[TunnelRecommendationsResponse],
    summary="Recommandations d'optimisation du tunnel",
)
async def tunnel_recommendations(
    agency_id: Optional[str] = Query(None, description="Filtrer par agence"),
    muse_id: Optional[str] = Query(None, description="Filtrer par muse"),
    start_date: Optional[datetime] = Query(None, description="Date de début (ISO)"),
    end_date: Optional[datetime] = Query(None, description="Date de fin (ISO)"),
    granularity: str = Query("daily", description="daily | weekly | monthly"),
):
    try:
        return await analyze_tunnel(
            agency_id=agency_id,
            muse_id=muse_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
