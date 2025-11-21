# api/routes/stats/tunnels.py

from fastapi import APIRouter, Query
from datetime import datetime
from typing import Optional, List
from api.services.analytics.tunnels import (
    get_tunnel_overview,
    get_tunnel_details,
    fetch_csv_data,
    # ou analyse_tunnel aliasé selon votre module
)

router = APIRouter(prefix="/stats/tunnel", tags=["stats"])


@router.get("/overview")
async def tunnel_overview(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: str = Query("daily"),
) -> List[dict]:
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


@router.get("/details")
async def tunnel_details(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
) -> List[dict]:
    return await get_tunnel_details(
        agency_id=agency_id,
        muse_id=muse_id,
        platform=platform,
        funnel_stage=funnel_stage,
        content_type=content_type,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/export")
async def export_tunnel_csv(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    records = await fetch_csv_data(
        agency_id=agency_id,
        muse_id=muse_id,
        platform=platform,
        funnel_stage=funnel_stage,
        content_type=content_type,
        start_date=start_date,
        end_date=end_date,
    )
    # Ici vous pouvez transformer `records` en CSV ou renvoyer directement la liste
    return records
