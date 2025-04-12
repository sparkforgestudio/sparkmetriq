from fastapi import APIRouter, Query, Depends
from typing import Optional, List
from api.stats.tunnels import get_tunnel_overview, get_tunnel_details, fetch_csv_data
from fastapi.responses import StreamingResponse
from io import StringIO
from core.auths import get_current_user

router = APIRouter()

# GET /api/stats/tunnels/overview
@router.get("/overview")
async def tunnel_overview(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    period: Optional[str] = Query("30d"),
    current_user=Depends(get_current_user)
):
    return await get_tunnel_overview(agency_id, muse_id, period)


# GET /api/stats/tunnels/details
@router.get("/details")
async def tunnel_details(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user=Depends(get_current_user)
):
    return await get_tunnel_details(agency_id, muse_id, platform, status, start_date, end_date)


# GET /api/stats/tunnels/export
@router.get("/export")
async def export_tunnel_data(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user=Depends(get_current_user)
):
    csv_content = await fetch_csv_data(agency_id, muse_id, platform, status, start_date, end_date)
    response = StreamingResponse(StringIO(csv_content), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=tunnel_export.csv"
    return response
