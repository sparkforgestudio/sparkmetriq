# services/analytics/tunnels.py

from services.databases import db
from datetime import datetime, timedelta
from typing import List, Optional, Dict


def build_filters(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict:
    filters = {}
    if agency_id:
        filters["agency_id"] = agency_id
    if muse_id:
        filters["muse_id"] = muse_id
    if platform:
        filters["platform"] = platform
    if start_date or end_date:
        filters["created_at"] = {}
        if start_date:
            filters["created_at"]["$gte"] = start_date
        if end_date:
            filters["created_at"]["$lte"] = end_date
    return filters


async def get_tunnel_overview(agency_id=None, muse_id=None, platform=None, start_date=None, end_date=None):
    filters = build_filters(agency_id, muse_id, platform, start_date, end_date)

    pipeline = [
        {"$match": filters},
        {"$group": {
            "_id": "$platform",
            "total": {"$sum": 1},
            "success": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
            "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}},
        }},
        {"$project": {
            "platform": "$_id",
            "total": 1,
            "success": 1,
            "errors": 1,
            "success_rate": {
                "$cond": [
                    {"$ne": ["$total", 0]},
                    {"$multiply": [{"$divide": ["$success", "$total"]}, 100]},
                    0
                ]
            }
        }}
    ]

    return await db["platform_logs"].aggregate(pipeline).to_list(length=20)


async def get_tunnel_details(agency_id=None, muse_id=None, platform=None, start_date=None, end_date=None):
    filters = build_filters(agency_id, muse_id, platform, start_date, end_date)
    return await db["platform_logs"].find(filters).sort("created_at", -1).limit(100).to_list(None)


async def fetch_csv_data(agency_id=None, muse_id=None, platform=None, start_date=None, end_date=None):
    records = await get_tunnel_details(agency_id, muse_id, platform, start_date, end_date)
    csv_data = [
        {
            "agency_id": r.get("agency_id"),
            "muse_id": r.get("muse_id"),
            "platform": r.get("platform"),
            "status": r.get("status"),
            "content_id": r.get("content_id"),
            "created_at": r.get("created_at"),
            "message": r.get("message")
        }
        for r in records
    ]
    return csv_data
