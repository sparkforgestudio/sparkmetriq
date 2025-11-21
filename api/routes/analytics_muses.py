# api/routes/analytics_muses.py
"""
Routes REST pour les analytics des muses par catégorie.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.analytics import CategoryAggFilters, CategoryAggItem, CategoryAggResponse
from api.databases.databases import get_core_db, get_bi_db

router = APIRouter(prefix="/analytics/muses", tags=["Analytics"])


def _match_date(field: str, date_from: str, date_to: str) -> Dict[str, Any]:
    """
    Construit un filtre de date MongoDB.
    
    Args:
        field: Nom du champ
        date_from: Date de début (ISO string)
        date_to: Date de fin (ISO string)
        
    Returns:
        Filtre MongoDB
    """
    return {
        field: {
            "$gte": datetime.fromisoformat(date_from.replace("Z", "+00:00")),
            "$lte": datetime.fromisoformat(date_to.replace("Z", "+00:00"))
        }
    }


async def _agg_sum(
    bi_db,
    coll_name: str,
    org_id: str,
    date_from: str,
    date_to: str,
    amount_field: str = None,
    message_dir: str = None,
    event: str = None,
    channels: List[str] = None
) -> Dict[str, float]:
    """
    Agrége les données d'une collection BI et les répartit par catégorie de muse.
    
    Args:
        bi_db: Base de données BI
        coll_name: Nom de la collection
        org_id: ID de l'organisation
        date_from: Date de début
        date_to: Date de fin
        amount_field: Champ contenant le montant (si None, compte les documents)
        message_dir: Direction des messages (in/out) si coll_name == "messages"
        event: Type d'événement si coll_name == "funnel_events"
        channels: Liste des canaux à filtrer
        
    Returns:
        Dictionnaire {catégorie: valeur}
    """
    match = {"org_id": org_id}
    match.update(_match_date("ts", date_from, date_to))
    
    # Filtres spécifiques
    if coll_name == "messages" and message_dir:
        match["direction"] = message_dir
    
    if coll_name == "funnel_events" and event:
        match["event"] = event
    
    # Filtre par canaux
    if channels:
        if coll_name == "messages":
            match["channel"] = {"$in": channels}
        elif coll_name in ("payments", "ppv_sales"):
            match["source"] = {"$in": channels}
    
    # Agrégation
    if amount_field:
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$muse_id", "val": {"$sum": f"${amount_field}"}}}
        ]
    else:
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$muse_id", "val": {"$sum": 1}}}
        ]
    
    try:
        rows = await bi_db[coll_name].aggregate(pipeline).to_list(length=None)
    except Exception:
        # Collection n'existe peut-être pas encore (MVP)
        rows = []
    
    return rows


@router.post("/by-category", response_model=CategoryAggResponse)
async def by_category(
    filters: CategoryAggFilters,
    current_user: UserResponse = Depends(get_current_user)
) -> CategoryAggResponse:
    """
    Agrège les KPIs par catégorie de muse.
    
    Args:
        filters: Filtres (dates, catégories, canaux)
        current_user: Utilisateur actuel
        
    Returns:
        Agrégations par catégorie
    """
    db_core = get_core_db()
    db_bi = get_bi_db()
    org_id = current_user.org_id
    
    # 1) Récupérer le mapping muse -> catégories
    cursor = db_core["muses"].find(
        {"org_id": org_id},
        {"_id": 1, "categories": 1}
    )
    muses = await cursor.to_list(length=None)
    
    if not muses:
        return CategoryAggResponse(
            items=[],
            total_revenue=0.0,
            total_ppv=0.0,
            total_messages_in=0,
            total_messages_out=0,
            total_new_subs=0,
            total_churns=0
        )
    
    # Construire le mapping
    muse_cat: Dict[str, List[str]] = {}
    for m in muses:
        muse_id = str(m["_id"])
        muse_cat[muse_id] = m.get("categories", [])
    
    # 2) Filtres optionnels
    allowed_categories = set(filters.categories or [])
    apply_cat_filter = len(allowed_categories) > 0
    channels = set(filters.channels or []) if filters.channels else None
    
    # 3) Fonction helper pour agréger et répartir par catégorie
    async def agg_sum(
        coll_name: str,
        amount_field: str = None,
        message_dir: str = None,
        event: str = None
    ) -> Dict[str, float]:
        """
        Agrége une collection et répartit équitablement par catégorie.
        """
        rows = await _agg_sum(
            db_bi,
            coll_name,
            org_id,
            filters.date_from,
            filters.date_to,
            amount_field,
            message_dir,
            event,
            list(channels) if channels else None
        )
        
        # Répartir par catégorie (équitablement si plusieurs catégories)
        cat_totals: Dict[str, float] = {}
        
        for r in rows:
            muse_id = str(r["_id"])
            val = float(r["val"])
            cats = muse_cat.get(muse_id, [])
            
            # Appliquer le filtre de catégorie si nécessaire
            if apply_cat_filter:
                cats = [c for c in cats if c in allowed_categories]
            
            if not cats:
                continue
            
            # Répartition équitable
            share = val / len(cats)
            for c in cats:
                cat_totals[c] = cat_totals.get(c, 0.0) + share
        
        return cat_totals
    
    # 4) Agrégations pour chaque métrique
    revenue = await agg_sum("payments", "amount")
    ppv = await agg_sum("ppv_sales", "ppv_amount")
    min_ = await agg_sum("messages", message_dir="in")
    mout = await agg_sum("messages", message_dir="out")
    subs = await agg_sum("funnel_events", event="subscribe")
    churns = await agg_sum("funnel_events", event="churn")
    
    # 5) Construire la liste des catégories
    categories = set(revenue.keys()) | set(ppv.keys()) | set(min_.keys()) | \
                 set(mout.keys()) | set(subs.keys()) | set(churns.keys())
    
    if apply_cat_filter:
        categories = categories & allowed_categories
    
    # 6) Compter les muses par catégorie (respecter le filtre)
    muses_per_cat: Dict[str, int] = {}
    for muse_id, cats in muse_cat.items():
        for c in cats:
            if apply_cat_filter and c not in allowed_categories:
                continue
            muses_per_cat[c] = muses_per_cat.get(c, 0) + 1
    
    # 7) Construire les items de réponse
    items = []
    totals = {
        "revenue_total": 0.0,
        "total_ppv": 0.0,
        "total_messages_in": 0,
        "total_messages_out": 0,
        "total_new_subs": 0,
        "total_churns": 0
    }
    
    for c in sorted(categories):
        item = CategoryAggItem(
            category=c,
            muses=muses_per_cat.get(c, 0),
            revenue_total=round(revenue.get(c, 0.0), 2),
            ppv_total=round(ppv.get(c, 0.0), 2),
            messages_in=int(min_.get(c, 0.0)),
            messages_out=int(mout.get(c, 0.0)),
            new_subs=int(subs.get(c, 0.0)),
            churns=int(churns.get(c, 0.0))
        )
        items.append(item)
        
        totals["revenue_total"] += item.revenue_total
        totals["total_ppv"] += item.ppv_total
        totals["total_messages_in"] += item.messages_in
        totals["total_messages_out"] += item.messages_out
        totals["total_new_subs"] += item.new_subs
        totals["total_churns"] += item.churns
    
    return CategoryAggResponse(
        items=items,
        total_revenue=round(totals["revenue_total"], 2),
        total_ppv=round(totals["total_ppv"], 2),
        total_messages_in=totals["total_messages_in"],
        total_messages_out=totals["total_messages_out"],
        total_new_subs=totals["total_new_subs"],
        total_churns=totals["total_churns"]
    )
