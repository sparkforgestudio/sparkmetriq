from fastapi import APIRouter, Query
from typing import List, Optional
from api.databases.databases import db

router = APIRouter(prefix="/analysis/filters", tags=["analysis"])

@router.get("/tunnel", response_model=dict)
async def get_tunnel_filters(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None)
):
    """
    Renvoie les listes de valeurs possibles pour filtrer l'analyse tunnel.
    """
    match = {}
    if agency_id:
        match["agency_id"] = agency_id
    if muse_id:
        match["muse_id"] = muse_id

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": None,
            "agencies": {"$addToSet": "$agency_id"},
            "muses": {"$addToSet": "$muse_id"},
            "platforms": {"$addToSet": "$platform"},
            "stages": {"$addToSet": "$funnel_stage"},
            "types": {"$addToSet": "$content_type"},
        }},
        {"$project": {"_id": 0}}
    ]
    res = await db["platform_logs"].aggregate(pipeline).to_list(1)
    return res[0] if res else {
        "agencies": [], "muses": [], "platforms": [], "stages": [], "types": []
    }
