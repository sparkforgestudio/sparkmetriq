from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional
from services.analytics.timeline import generate_timeline_stats

router = APIRouter()

@router.get("/timeline")
async def get_timeline_stats(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """
    Renvoie l’évolution quotidienne des KPI pour une agence ou muse.
    """
    results = await generate_timeline_stats(
        agency_id=agency_id,
        muse_id=muse_id,
        start_date=start_date,
        end_date=end_date
    )
    return {"timeline": results}
