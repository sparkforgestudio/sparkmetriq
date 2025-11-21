from typing import Optional, Dict, Any, List
from datetime import datetime
from pymongo import ASCENDING, DESCENDING

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
    if granularity == "weekly":
        return "%Y-%U"
    if granularity == "monthly":
        return "%Y-%m"
    return "%Y-%m-%d"


async def get_tunnel_overview(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    funnel_stage: Optional[str] = None,
    content_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    granularity: str = "daily",
) -> List[Dict[str, Any]]:
    filters = build_filters(agency_id, muse_id, platform, funnel_stage, content_type, start_date, end_date)
    date_format = get_date_format(granularity)

    pipeline = [
        {"$match": filters},
        {"$group": {
            "_id": {
                "platform": "$platform",
                "date": {"$dateToString": {"format": date_format, "date": "$created_at"}}
            },
            "total": {"$sum": 1},
            "success": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
            "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}},
            "avg_conversion_time": {"$avg": {"$cond": [
                {"$and": [{"$gt": ["$converted_at", None]}, {"$gt": ["$created_at", None]}]},
                {"$divide": [{"$subtract": ["$converted_at", "$created_at"]}, 1000]},
                None
            ]}}
        }},
        {"$project": {
            "platform": "$_id.platform",
            "date": "$_id.date",
            "total": 1,
            "success": 1,
            "errors": 1,
            "success_rate": {"$cond": [{"$ne": ["$total", 0]}, {"$multiply": [{"$divide": ["$success", "$total"]}, 100]}, 0]},
            "avg_conversion_time": 1
        }},
        {"$sort": {"date": ASCENDING}}
    ]

    return await db["platform_logs"].aggregate(pipeline).to_list(length=0)


async def get_tunnel_details(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    funnel_stage: Optional[str] = None,
    content_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    filters = build_filters(agency_id, muse_id, platform, funnel_stage, content_type, start_date, end_date)
    cursor = db["platform_logs"].find(filters).sort("created_at", DESCENDING).limit(100)
    return await cursor.to_list(length=100)


async def fetch_csv_data(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    funnel_stage: Optional[str] = None,
    content_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    records = await get_tunnel_details(agency_id, muse_id, platform, funnel_stage, content_type, start_date, end_date)
    csv_data: List[Dict[str, Any]] = []
    for r in records:
        csv_data.append({
            "agency_id": r.get("agency_id"),
            "muse_id": r.get("muse_id"),
            "platform": r.get("platform"),
            "funnel_stage": r.get("funnel_stage"),
            "content_type": r.get("content_type"),
            "status": r.get("status"),
            "content_id": r.get("content_id"),
            "created_at": r.get("created_at"),
            "converted_at": r.get("converted_at"),
            "message": r.get("message"),
        })
    return csv_data


async def analyze_tunnel(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    granularity: str = "daily",
) -> List[Dict[str, Any]]:
    overview = await get_tunnel_overview(
        agency_id=agency_id,
        muse_id=muse_id,
        platform=None,
        funnel_stage=None,
        content_type=None,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )
    recommendations: List[Dict[str, Any]] = []
    for row in overview:
        rate = row.get("success_rate", 0)
        if rate < 10:
            advice = "Augmentez la fréquence des publications pour améliorer le taux de conversion."
        elif rate < 30:
            advice = "Testez différents types de contenus pour identifier ce qui engage le plus."
        else:
            advice = "La stratégie actuelle est performante, poursuivez sur cette voie."
        recommendations.append({**row, "recommendations": [advice]})

    return recommendations
# expose analyze_tunnel under the name the router expects
get_tunnel_recommendations = analyze_tunnel

from typing import Dict, Any, List

async def analyze_tunnel(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    granularity: str = "daily",
) -> List[Dict[str, Any]]:
    """
    Analyse le tunnel de vente et renvoie pour chaque muse un
    jeu de recommandations simples basées sur les taux de conversion.
    """
    # Récupère l'aperçu du tunnel
    overview = await get_tunnel_overview(
        agency_id=agency_id,
        muse_id=muse_id,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )

    recs_by_muse: Dict[str, List[str]] = {}
    for entry in overview:
        muse = entry.get("muse_id") or entry["_id"].get("muse_id", "unknown")
        rate = entry.get("success_rate", 0)
        recs = recs_by_muse.setdefault(muse, [])

        # Règles de recommandations basiques :
        if rate < 20:
            recs.append(f"Le taux de conversion ({rate:.1f}%) est faible : augmentez la fréquence des posts.")
        elif rate < 50:
            recs.append(f"Taux de conversion moyen ({rate:.1f}%) : testez différents formats de contenu.")
        else:
            recs.append(f"Taux de conversion élevé ({rate:.1f}%) : continuez sur cette lancée et dupliquez les bonnes pratiques.")

    # Structure finale
    return [
        {"muse_id": muse, "recommendations": recs}
        for muse, recs in recs_by_muse.items()
    ]
