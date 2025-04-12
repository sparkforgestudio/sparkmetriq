from fastapi import APIRouter, Depends
from api.services.databases import db
from core.auths import get_current_user, is_operator_or_admin
from schemas.users import UserResponse
from datetime import datetime
from fastapi import Query

router = APIRouter()

@router.get("/stats")
async def get_platform_stats(current_user: UserResponse = Depends(is_operator_or_admin)):
    """
    Regroupe les statistiques des publications par plateforme.
    """
    pipeline = [
        {
            "$group": {
                "_id": {
                    "platform": "$platform",
                    "status": "$status"
                },
                "count": {"$sum": 1}
            }
        }
    ]

    raw_stats = await db["platform_logs"].aggregate(pipeline).to_list(length=None)

    aggregated = {}
    for stat in raw_stats:
        platform = stat["_id"]["platform"]
        status = stat["_id"]["status"]
        count = stat["count"]

        if platform not in aggregated:
            aggregated[platform] = {"platform": platform, "count": 0, "success": 0, "failed": 0}

        aggregated[platform]["count"] += count
        if status == "success":
            aggregated[platform]["success"] += count
        elif status == "error":
            aggregated[platform]["failed"] += count

    return {"stats": list(aggregated.values())}

@router.get("/muse-stats")
async def get_stats_by_muse(
    current_user: UserResponse = Depends(is_operator_or_admin),
    agency_id: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...)
):
    """
    Statistiques par muse, entre deux dates (UTC).
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utiliser ISO 8601 (ex: 2024-05-01T00:00:00)")

    pipeline = [
        {
            "$match": {
                "agency_id": agency_id,
                "timestamp": {"$gte": start, "$lte": end}
            }
        },
        {
            "$group": {
                "_id": {"muse_id": "$muse_id", "status": "$status"},
                "count": {"$sum": 1}
            }
        }
    ]

    results = await db["platform_logs"].aggregate(pipeline).to_list(None)

    aggregated = {}
    for r in results:
        muse_id = r["_id"]["muse_id"]
        status = r["_id"]["status"]
        count = r["count"]

        if muse_id not in aggregated:
            aggregated[muse_id] = {"muse_id": muse_id, "total": 0, "success": 0, "failed": 0}

        aggregated[muse_id]["total"] += count
        if status == "success":
            aggregated[muse_id]["success"] += count
        elif status == "error":
            aggregated[muse_id]["failed"] += count

    return {"muses": list(aggregated.values())}