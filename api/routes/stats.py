from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pydantic import BaseModel
from api.core.auths import get_current_user
from api.schemas.users import UserResponse
from api.database import db

router = APIRouter()

# --------------------------------------------------------------------
# Endpoints existants déjà présents dans le fichier (/overview, /timeline, etc.)
# --------------------------------------------------------------------

@router.get("/overview")
async def get_platform_overview(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    days: int = 30,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Statistiques globales des publications pour les plateformes.
    """
    date_from = datetime.utcnow() - timedelta(days=days)
    match_stage = {
        "scheduled_at": {"$gte": date_from},
    }
    if agency_id:
        match_stage["agency_id"] = agency_id
    if muse_id:
        match_stage["muse_id"] = muse_id

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": "$platform",
            "total_posts": {"$sum": 1},
            "total_errors": {
                "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
            }
        }}
    ]

    results = await db["platform_logs"].aggregate(pipeline).to_list(None)

    # Calcul du taux de succès
    for item in results:
        total = item["total_posts"]
        errors = item["total_errors"]
        item["platform"] = item["_id"]
        item["success_rate"] = round((total - errors) / total * 100, 1) if total else 0
        del item["_id"]

    return {"stats": results}


@router.get("/timeline")
async def get_timeline_data(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    days: int = 30,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Courbe d'évolution quotidienne des publications.
    """
    date_from = datetime.utcnow() - timedelta(days=days)
    match_stage = {
        "scheduled_at": {"$gte": date_from}
    }
    if agency_id:
        match_stage["agency_id"] = agency_id
    if muse_id:
        match_stage["muse_id"] = muse_id

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$scheduled_at"}},
            "posts": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    results = await db["platform_logs"].aggregate(pipeline).to_list(None)

    return {
        "timeline": [{"date": r["_id"], "posts": r["posts"]} for r in results]
    }


@router.get("/agencies", response_model=List[str])
async def list_agencies(current_user: UserResponse = Depends(get_current_user)):
    """
    Liste des agences existantes.
    """
    return await db["platform_logs"].distinct("agency_id")


@router.get("/muses", response_model=List[str])
async def list_muses(current_user: UserResponse = Depends(get_current_user)):
    """
    Liste des muses existantes.
    """
    return await db["platform_logs"].distinct("muse_id")


# --------------------------------------------------------------------
# Nouveau endpoint : Timeline par type de contenu
# --------------------------------------------------------------------

class TimelineEntry(BaseModel):
    date: str  # Date formatée en 'YYYY-MM-DD'
    posts: int

class ContentTimeline(BaseModel):
    content_type: str
    timeline: List[TimelineEntry]

@router.get("/timeline/content", response_model=Dict[str, List[ContentTimeline]])
async def get_timeline_by_content(
    agency_id: Optional[str] = None,
    muse_id: Optional[str] = None,
    days: int = 30,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Retourne l’évolution quotidienne des publications regroupées par type de contenu.
    L’agrégation s’appuie sur la collection 'platform_logs' et regroupe les posts par
    date (format YYYY-MM-DD) et par le champ 'content_type'.
    """
    date_from = datetime.utcnow() - timedelta(days=days)
    match_stage = {
        "scheduled_at": {"$gte": date_from}
    }
    if agency_id:
        match_stage["agency_id"] = agency_id
    if muse_id:
        match_stage["muse_id"] = muse_id

    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {
                "content_type": "$content_type",
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$scheduled_at"}}
            },
            "posts": {"$sum": 1}
        }},
        {"$sort": {"_id.date": 1}}
    ]

    results = await db["platform_logs"].aggregate(pipeline).to_list(None)

    # Organisation des résultats dans un dictionnaire regroupé par 'content_type'
    timelines: Dict[str, List[TimelineEntry]] = {}
    for r in results:
        # En cas d'absence de champ content_type, on regroupe sous une catégorie par défaut
        ctype = r["_id"].get("content_type") or "non_specifié"
        entry = TimelineEntry(date=r["_id"]["date"], posts=r["posts"])
        if ctype in timelines:
            timelines[ctype].append(entry)
        else:
            timelines[ctype] = [entry]

    # Transformation du dictionnaire en liste d'objets ContentTimeline
    content_timelines = [ContentTimeline(content_type=k, timeline=v) for k, v in timelines.items()]
    return {"timeline": content_timelines}
