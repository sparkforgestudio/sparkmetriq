# api/routes/bi_pricing.py
"""
Routes FastAPI pour l'Assistant Pricing IA.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, Optional

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.bi_pricing import PricingRecommendationIn
from api.services.bi.pricing_optimizer import PricingOptimizerService
from api.databases.databases import get_bi_db

router = APIRouter(prefix="/bi", tags=["BI Pricing"])


@router.post("/pricing/recommend", status_code=status.HTTP_200_OK)
async def recommend_price(
    payload: PricingRecommendationIn,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """Génère une recommandation de pricing optimisé.
    
    Analyse le prix actuel d'un item (PPV, subscription, bundle) et propose
    un prix optimisé basé sur des heuristiques (MVP) ou des modèles ML.
    
    Args:
        payload: Données de l'item (org_id, muse_id, item_type, item_ref, current_price_usd, features).
        current_user: Utilisateur actuel authentifié (depuis get_current_user).
        
    Returns:
        Dict avec "ok": True et "data" contenant la recommandation complète
        (prix recommandé, confiance, gain prédit, base du calcul).
        
    Raises:
        HTTPException: 403 si org_id ne correspond pas, 500 en cas d'erreur serveur.
    """
    # Vérification multi-tenant
    if payload.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: org_id mismatch"
        )
    
    try:
        svc = PricingOptimizerService(get_bi_db())
        out = await svc.recommend_price(payload.model_dump())
        return {"ok": True, "data": out}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération: {str(e)}"
        )


@router.get("/pricing/recommendations", status_code=status.HTTP_200_OK)
async def list_recommendations(
    org_id: str = Query(..., description="ID de l'organisation"),
    muse_id: Optional[str] = Query(None, description="ID de la muse (filtre)"),
    item_type: Optional[str] = Query(None, description="Type d'item (filtre)"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(100, ge=1, le=500, description="Nombre d'éléments par page"),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """Liste les recommandations de pricing historiques.
    
    Retourne une liste paginée des recommandations de pricing générées précédemment,
    filtrées par organisation, muse et type d'item.
    
    Args:
        org_id: ID de l'organisation (requis, vérifié contre current_user.org_id).
        muse_id: ID de la muse pour filtrer (optionnel).
        item_type: Type d'item pour filtrer (ppv, subscription, bundle, optionnel).
        page: Numéro de page (défaut: 1, min: 1).
        limit: Nombre d'éléments par page (défaut: 100, min: 1, max: 500).
        current_user: Utilisateur actuel authentifié.
        
    Returns:
        Dict avec "items" (liste de recommandations), "next_page" (None ou numéro), "count".
        
    Raises:
        HTTPException: 403 si org_id ne correspond pas, 500 en cas d'erreur serveur.
    """
    # Vérification multi-tenant
    if org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: org_id mismatch"
        )
    
    try:
        # Construire le filtre
        filt = {"org_id": org_id}
        
        if muse_id:
            filt["muse_id"] = muse_id
        
        if item_type:
            filt["item_type"] = item_type
        
        # Pagination
        skip = (page - 1) * limit
        
        bi_db = get_bi_db()
        cursor = (
            bi_db["pricing_recommendations"]
            .find(filt)
            .sort("generated_at", -1)
            .skip(skip)
            .limit(limit + 1)  # +1 pour détecter page suivante
        )
        
        rows = await cursor.to_list(length=limit + 1)
        
        # Détecter s'il y a une page suivante
        has_next = len(rows) > limit
        if has_next:
            rows = rows[:limit]
        
        # Convertir _id en string
        for r in rows:
            r["id"] = str(r.pop("_id"))
        
        return {
            "items": rows,
            "next_page": page + 1 if has_next else None,
            "count": len(rows)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la requête: {str(e)}"
        )
