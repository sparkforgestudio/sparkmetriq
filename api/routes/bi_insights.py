# api/routes/bi_insights.py
"""
Routes FastAPI pour l'Assistant Stratégique IA (Insights).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, Optional

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.bi_insights import InsightAlertIn
from api.services.bi.insight_engine import InsightEngine
from api.databases.databases import get_bi_db

router = APIRouter(prefix="/bi", tags=["BI Insights"])


@router.post("/insights/alerts", status_code=status.HTTP_201_CREATED)
async def create_alert(
    payload: InsightAlertIn,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """Crée une alerte insight stratégique.
    
    Enregistre une nouvelle alerte dans le système d'insights BI pour notifier
    l'équipe d'opportunités, tendances, problèmes ou suggestions de collaboration.
    
    Args:
        payload: Données de l'alerte (type, sévérité, catégorie, contexte).
        current_user: Utilisateur actuel authentifié (depuis get_current_user).
        
    Returns:
        Dict avec "ok": True et "id" de l'alerte créée.
        
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
        eng = InsightEngine(get_bi_db())
        alert_id = await eng.record_alert(payload.model_dump())
        return {"ok": True, "id": alert_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


@router.get("/insights/alerts", status_code=status.HTTP_200_OK)
async def list_alerts(
    org_id: str = Query(..., description="ID de l'organisation"),
    muse_id: Optional[str] = Query(None, description="ID de la muse (filtre)"),
    types: Optional[str] = Query(None, description="Types séparés par virgule"),
    severity: Optional[str] = Query(None, description="Sévérités séparées par virgule"),
    from_utc: Optional[str] = Query(None, description="Date de début UTC (ISO format)"),
    to_utc: Optional[str] = Query(None, description="Date de fin UTC (ISO format)"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(100, ge=1, le=500, description="Nombre d'éléments par page"),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """Liste les alertes insights selon les filtres.
    
    Retourne une liste paginée d'alertes stratégiques filtrées par organisation,
    muse, type, sévérité et période.
    
    Args:
        org_id: ID de l'organisation (requis, vérifié contre current_user.org_id).
        muse_id: ID de la muse pour filtrer (optionnel).
        types: Types d'alertes séparés par virgule (alert,opportunity,trend,collab).
        severity: Sévérités séparées par virgule (low,medium,high).
        from_utc: Date de début UTC au format ISO (optionnel).
        to_utc: Date de fin UTC au format ISO (optionnel).
        page: Numéro de page (défaut: 1, min: 1).
        limit: Nombre d'éléments par page (défaut: 100, min: 1, max: 500).
        current_user: Utilisateur actuel authentifié.
        
    Returns:
        Dict avec "items" (liste d'alertes), "next_page" (None ou numéro), "count".
        
    Raises:
        HTTPException: 403 si org_id ne correspond pas, 500 en cas d'erreur serveur.
    """
    # Vérification multi-tenant
    if org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: org_id mismatch"
        )
    
    # Parser les paramètres CSV
    q = {
        "org_id": org_id,
        "muse_id": muse_id,
        "types": types.split(",") if types else None,
        "severity": severity.split(",") if severity else None,
        "from_utc": from_utc,
        "to_utc": to_utc,
        "page": page,
        "limit": limit
    }
    
    try:
        eng = InsightEngine(get_bi_db())
        result = await eng.list_alerts(q)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la requête: {str(e)}"
        )


@router.get("/insights/collabs", status_code=status.HTTP_200_OK)
async def list_collabs(
    org_id: str = Query(..., description="ID de l'organisation"),
    muse_id: str = Query(..., description="ID de la muse"),
    min_score: float = Query(0.6, ge=0.0, le=1.0, description="Score minimum requis"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(50, ge=1, le=200, description="Nombre d'éléments par page"),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """Liste les candidats pour collaboration.
    
    Retourne une liste paginée de muses candidates pour collaboration basée
    sur un score de similarité (audience, hashtags, niche, etc.).
    
    Args:
        org_id: ID de l'organisation (requis, vérifié contre current_user.org_id).
        muse_id: ID de la muse pour laquelle chercher des partenaires.
        min_score: Score minimum de similarité requis (défaut: 0.6, range: 0.0-1.0).
        page: Numéro de page (défaut: 1, min: 1).
        limit: Nombre d'éléments par page (défaut: 50, min: 1, max: 200).
        current_user: Utilisateur actuel authentifié.
        
    Returns:
        Dict avec "items" (liste de candidats), "next_page" (None ou numéro), "count".
        
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
        eng = InsightEngine(get_bi_db())
        result = await eng.collab_candidates(org_id, muse_id, min_score, page, limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la requête: {str(e)}"
        )
