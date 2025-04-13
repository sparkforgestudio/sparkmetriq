from services.databases import db
from datetime import datetime
from typing import List, Optional, Dict, Any

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
    Construit un dictionnaire de filtres pour interroger la collection 'platform_logs'
    en fonction des critères facultatifs.
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
    Possibilités : "daily" (par défaut), "weekly", "monthly".
    """
    if granularity == "weekly":
        return "%Y-%U"  # Année + numéro de semaine (semaine commençant dimanche)
    elif granularity == "monthly":
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
    """
    Récupère un aperçu des statistiques du tunnel depuis la collection 'platform_logs'.
    Les données sont agrégées par plateforme et selon une échelle temporelle (daily, weekly ou monthly).
    Calcule le nombre total d'événements, le nombre de succès, d'erreurs, le taux de succès
    et, si possible, la durée moyenne de conversion (en secondes) lorsque le champ 'converted_at' est renseigné.
    """
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

async def get_tunnel_details(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    funnel_stage: Optional[str] = None,
    content_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Récupère les détails des logs du tunnel depuis 'platform_logs', triés par 'created_at' décroissant.
    """
    filters = build_filters(agency_id, muse_id, platform, funnel_stage, content_type, start_date, end_date)
    return await db["platform_logs"].find(filters).sort("created_at", -1).limit(100).to_list(None)

async def fetch_csv_data(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    funnel_stage: Optional[str] = None,
    content_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Formate les données détaillées du tunnel pour l'export CSV.
    Les champs sélectionnés incluent des informations liées à l'agence, la muse, la plateforme, l'étape du tunnel et d'autres métadonnées.
    """
    records = await get_tunnel_details(agency_id, muse_id, platform, funnel_stage, content_type, start_date, end_date)
    csv_data = [
        {
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
        }
        for r in records
    ]
    return csv_data
