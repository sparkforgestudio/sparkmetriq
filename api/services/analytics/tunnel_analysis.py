# api/services/analytics/tunnel_analysis.py

from typing import List, Dict, Any, Optional
from datetime import datetime
from api.databases.databases import db

def build_filters(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    funnel_stage: Optional[str] = None,
    content_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Construit le dict de filtres à appliquer sur la collection 'platform_logs'.
    """
    filters: Dict[str, Any] = {}
    if agency_id:
        filters["agency_id"] = agency_id
    if muse_id:
        filters["muse_id"] = muse_id
    if platform:
        filters["platform"] = platform
    if funnel_stage:
        filters["funnel_stage"] = funnel_stage
    if content_type:
        filters["content_type"] = content_type
    if start_date or end_date:
        date_filter: Dict[str, Any] = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        filters["created_at"] = date_filter
    return filters

def get_date_format(granularity: str) -> str:
    """
    Retourne un format de date adapté à la granularité souhaitée.
    """
    if granularity == "weekly":
        return "%Y-%U"
    if granularity == "monthly":
        return "%Y-%m"
    return "%Y-%m-%d"

async def analyze_tunnel(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    funnel_stage: Optional[str] = None,
    content_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    granularity: str = "daily",
) -> List[Dict[str, Any]]:
    """
    Analyse et agrège les logs de 'platform_logs' pour donner un aperçu du tunnel de conversion.
    - groupés par plateforme et par date (daily/weekly/monthly)
    - calcul du total, succès, erreurs, taux de réussite, temps moyen de conversion
    """
    filters = build_filters(
        agency_id, muse_id, platform, funnel_stage, content_type, start_date, end_date
    )
    date_fmt = get_date_format(granularity)

    pipeline = [
        {"$match": filters},
        {"$group": {
            "_id": {
                "platform": "$platform",
                "date": {"$dateToString": {"format": date_fmt, "date": "$created_at"}}
            },
            "total": {"$sum": 1},
            "success": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
            "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}},
            "avg_conversion_time": {
                "$avg": {
                    "$cond": [
                        {"$and": [
                            {"$gt": ["$converted_at", None]},
                            {"$gt": ["$created_at", None]}
                        ]},
                        {"$divide": [{"$subtract": ["$converted_at", "$created_at"]}, 1000]},
                        None
                    ]
                }
            }
        }},
        {"$project": {
            "platform": "$_id.platform",
            "date": "$_id.date",
            "total": 1,
            "success": 1,
            "errors": 1,
            "success_rate": {
                "$cond": [
                    {"$ne": ["$total", 0]},
                    {"$multiply": [{"$divide": ["$success", "$total"]}, 100]},
                    0
                ]
            },
            "avg_conversion_time": 1
        }},
        {"$sort": {"date": 1}}
    ]

    return await db["platform_logs"].aggregate(pipeline).to_list(length=100)
