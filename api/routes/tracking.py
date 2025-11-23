# api/routes/tracking.py
"""
Routes REST pour le système de suivi des liens marketing & attribution.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime, timezone
from bson import ObjectId

from api.core.settings import settings
from api.schemas.users import UserResponse
from api.core.auth import get_current_user
from api.schemas.tracking import (
    LinkCreate, LinkOut, LinkListOut, TrackRenderIn, TrackRenderOut, SourceStatsOut
)
from api.databases.databases import get_core_db, get_bi_db
from api.services.tracking.link_service import create_link, ensure_tracked_url

router = APIRouter(prefix="/tracking", tags=["Tracking"])


def _ensure_enabled():
    """Vérifie que le feature flag est activé."""
    if not settings.feature_link_tracking_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Link tracking disabled"
        )


@router.post("/links", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
async def create_tracking_link(
    payload: LinkCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> LinkOut:
    """
    Crée un lien traqué.
    
    Args:
        payload: Requête de création
        current_user: Utilisateur actuel
        
    Returns:
        Lien créé
    """
    _ensure_enabled()
    
    try:
        doc = await create_link(payload)
        return LinkOut(
            id=doc["id"],
            code=doc["code"],
            org_id=doc["org_id"],
            short_url=doc["short_url"],
            destination_url=doc["destination_url"],
            utm=doc.get("utm", {}),
            campaign_id=doc.get("campaign_id"),
            promo_code=doc.get("promo_code"),
            created_at=doc["created_at"],
            expires_at=doc.get("expires_at"),
            max_clicks=doc.get("max_clicks"),
            clicks_total=doc.get("clicks_total", 0),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/links", response_model=LinkListOut)
async def list_links(
    org_id: str = Query(..., description="ID de l'organisation"),
    current_user: UserResponse = Depends(get_current_user)
) -> LinkListOut:
    """
    Liste les liens traqués d'une organisation.
    
    Args:
        org_id: ID de l'organisation
        current_user: Utilisateur actuel
        
    Returns:
        Liste des liens
    """
    _ensure_enabled()
    
    db = get_core_db()
    cursor = (
        db["tracking_links"]
        .find({"org_id": org_id})
        .sort("created_at", -1)
        .limit(200)
    )
    
    docs = await cursor.to_list(length=200)
    
    items = []
    for d in docs:
        items.append(LinkOut(
            id=str(d["_id"]),
            code=d["code"],
            org_id=d["org_id"],
            short_url=f"{settings.tracking_domain_base}/r/{d['code']}",
            destination_url=d["destination_url"],
            utm=d.get("utm", {}),
            campaign_id=d.get("campaign_id"),
            promo_code=d.get("promo_code"),
            created_at=d["created_at"],
            expires_at=d.get("expires_at"),
            max_clicks=d.get("max_clicks"),
            clicks_total=d.get("clicks_total", 0),
        ))
    
    return LinkListOut(items=items)


@router.post("/render", response_model=TrackRenderOut)
async def render_tracked_url(
    payload: TrackRenderIn,
    current_user: UserResponse = Depends(get_current_user)
) -> TrackRenderOut:
    """
    Génère un lien traqué rapidement (pour Message Builder).
    
    Args:
        payload: Requête de rendu
        current_user: Utilisateur actuel
        
    Returns:
        Lien traqué généré
    """
    _ensure_enabled()
    
    try:
        doc = await ensure_tracked_url(
            payload.org_id,
            str(payload.destination_url),
            payload.context or {}
        )
        return TrackRenderOut(
            short_url=doc["short_url"],
            code=doc["code"]
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stats/sources", response_model=SourceStatsOut)
async def stats_sources(
    org_id: str = Query(..., description="ID de l'organisation"),
    date_from: datetime = Query(..., description="Date de début"),
    date_to: datetime = Query(..., description="Date de fin"),
    current_user: UserResponse = Depends(get_current_user),
) -> SourceStatsOut:
    """
    Statistiques par source de trafic (revenus attribués).
    
    Args:
        org_id: ID de l'organisation
        date_from: Date de début
        date_to: Date de fin
        current_user: Utilisateur actuel
        
    Returns:
        Statistiques par source
    """
    _ensure_enabled()
    
    db_bi = get_bi_db()
    
    # Agrégation des revenus par source/medium/campaign/content
    pipeline = [
        {
            "$match": {
                "org_id": org_id,
                "ts": {"$gte": date_from, "$lte": date_to}
            }
        },
        {
            "$group": {
                "_id": {
                    "source": "$source",
                    "medium": "$medium",
                    "campaign": "$campaign",
                    "content": "$content"
                },
                "revenue": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"revenue": -1}
        },
        {
            "$limit": 200
        }
    ]
    
    items = await db_bi["revenue_attribution_daily"].aggregate(pipeline).to_list(length=None)
    
    by_source = []
    for it in items:
        by_source.append({
            "source": it["_id"].get("source"),
            "medium": it["_id"].get("medium"),
            "campaign": it["_id"].get("campaign"),
            "content": it["_id"].get("content"),
            "revenue": float(it["revenue"]),
            "clicks": None  # Option: joindre tracking_clicks si nécessaire
        })
    
    total = sum(x["revenue"] for x in by_source) if by_source else 0.0
    
    return SourceStatsOut(
        org_id=org_id,
        range_from=date_from,
        range_to=date_to,
        model=settings.attribution_model,
        clicks=None,  # À calculer si besoin de CTR global
        revenue_total=total,
        by_source=by_source
    )




