# routes/stats_tunnels.py
from fastapi import APIRouter, Query
from services.analytics.tunnels import get_tunnel_overview
from typing import Optional

router = APIRouter()

@router.get("/tunnels/overview")
async def tunnel_overview(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None)
):
    return await get_tunnel_overview(agency_id, muse_id, from_date, to_date)

@router.get("/tunnels/detailed")
async def tunnel_detailed(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    source: Optional[str] = Query(None),  # ex: "instagram"
    destination: Optional[str] = Query(None),  # ex: "telegram"
):
    from services.analytics.tunnels import get_tunnel_details
    return await get_tunnel_details(agency_id, muse_id, from_date, to_date, source, destination)
from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/tunnels/export-csv")
async def export_tunnel_csv(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    from services.analytics.tunnels import fetch_csv_data

    csv_data = await fetch_csv_data(agency_id, muse_id, from_date, to_date)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=csv_data[0].keys())
    writer.writeheader()
    writer.writerows(csv_data)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=tunnel_stats.csv"
    })
