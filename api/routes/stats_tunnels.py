from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.services.analytics.tunnels import (
    get_tunnel_overview,
    get_tunnel_details,
    fetch_csv_data,
    get_tunnel_recommendations,
)

router = APIRouter(prefix="/stats/tunnels", tags=["stats"])

@router.get("/overview", response_model=List[Dict[str, Any]])
async def tunnels_overview(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Aperçu agrégé des tunnels de vente par plateforme et par période.
    """
    try:
        data = await get_tunnel_overview(
            agency_id=agency_id,
            muse_id=muse_id,
            platform=platform,
            funnel_stage=funnel_stage,
            content_type=content_type,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/details", response_model=List[Dict[str, Any]])
async def tunnels_details(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Liste détaillée des logs de tunnels, triés par date de création.
    """
    try:
        data = await get_tunnel_details(
            agency_id=agency_id,
            muse_id=muse_id,
            platform=platform,
            funnel_stage=funnel_stage,
            content_type=content_type,
            start_date=start_date,
            end_date=end_date
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export", response_model=List[Dict[str, Any]])
async def tunnels_export(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Prépare les données pour export CSV des logs de tunnels.
    """
    try:
        csv_data = await fetch_csv_data(
            agency_id=agency_id,
            muse_id=muse_id,
            platform=platform,
            funnel_stage=funnel_stage,
            content_type=content_type,
            start_date=start_date,
            end_date=end_date
        )
        return csv_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
