# api/routes/calendar.py
"""
Routes FastAPI pour la Vue Calendaire Unifiée.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, Optional

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.calendar import (
    ScheduledPostIn, ScheduledPostOut, CalendarQuery,
    RescheduleIn, DuplicateIn
)
from api.services.calendar.service import CalendarService

router = APIRouter(prefix="/calendar", tags=["Calendar"])

# Instance globale du service
svc = CalendarService()


@router.get("/items", response_model=Dict[str, Any])
async def list_items(
    org_id: str = Query(..., description="ID de l'organisation"),
    from_utc: str = Query(..., description="Date de début UTC (ISO format)"),
    to_utc: str = Query(..., description="Date de fin UTC (ISO format)"),
    muse_ids: Optional[str] = Query(
        None,
        description="IDs des muses (séparés par virgule)"
    ),
    platforms: Optional[str] = Query(
        None,
        description="Plateformes (séparées par virgule)"
    ),
    statuses: Optional[str] = Query(
        None,
        description="Statuts (séparés par virgule)"
    ),
    labels: Optional[str] = Query(
        None,
        description="Labels (séparés par virgule)"
    ),
    category_id: Optional[str] = Query(
        None,
        description="ID de catégorie"
    ),
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(200, ge=1, le=500, description="Nombre d'éléments par page"),
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Liste les posts du calendrier selon les filtres.
    
    Args:
        org_id: ID de l'organisation
        from_utc: Date de début UTC
        to_utc: Date de fin UTC
        muse_ids: IDs des muses (optionnel)
        platforms: Plateformes (optionnel)
        statuses: Statuts (optionnel)
        labels: Labels (optionnel)
        category_id: ID de catégorie (optionnel)
        page: Numéro de page
        limit: Nombre d'éléments par page
        current_user: Utilisateur actuel
        
    Returns:
        Liste des posts avec pagination
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
        "from_utc": from_utc,
        "to_utc": to_utc,
        "muse_ids": muse_ids.split(",") if muse_ids else None,
        "platforms": platforms.split(",") if platforms else None,
        "statuses": statuses.split(",") if statuses else None,
        "labels": labels.split(",") if labels else None,
        "category_id": category_id,
        "page": page,
        "limit": limit
    }
    
    try:
        result = await svc.query_calendar(q)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la requête: {str(e)}"
        )


@router.post("/schedule", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    payload: ScheduledPostIn,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Crée un nouveau post programmé.
    
    Args:
        payload: Données du post
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation de création avec ID
    """
    # Vérification multi-tenant
    if payload.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: org_id mismatch"
        )
    
    try:
        post_id = await svc.create(payload)
        # La notification WS est déjà faite dans le service
        return {"ok": True, "id": post_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


@router.patch("/schedule/{post_id}", status_code=status.HTTP_200_OK)
async def update_schedule(
    post_id: str,
    payload: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Met à jour un post programmé.
    
    Args:
        post_id: ID du post
        payload: Champs à mettre à jour
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation de mise à jour
    """
    org_id = current_user.org_id
    
    try:
        await svc.update(post_id, org_id, payload)
        # La notification WS est déjà faite dans le service
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


@router.post("/reschedule", status_code=status.HTTP_200_OK)
async def reschedule(
    body: RescheduleIn,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Reprogramme un post.
    
    Args:
        body: Données de reprogrammation
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation de reprogrammation
    """
    org_id = current_user.org_id
    
    try:
        await svc.reschedule(body, org_id)
        
        # Notifier via WS (déjà fait dans service, mais on peut rebroadcast ici si besoin)
        
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la reprogrammation: {str(e)}"
        )


@router.post("/duplicate", status_code=status.HTTP_201_CREATED)
async def duplicate(
    body: DuplicateIn,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Duplique un post sur une ou plusieurs plateformes.
    
    Args:
        body: Données de duplication
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation avec IDs des nouveaux posts
    """
    # Pour obtenir org_id, on doit d'abord charger le post source
    # Pour simplifier, on l'ajoute dans le body ou on le récupère du post
    
    # On va le récupérer via le service qui vérifie l'org_id
    # Pour MVP, on suppose que le service gère ça
    
    # On aura besoin d'org_id, donc on va le passer via un query param
    # ou le récupérer du post source dans le service
    
    # Simplification: on ajoute org_id dans le schéma DuplicateIn ou on le passe en query
    # Pour l'instant, on va le récupérer du post source dans le service
    
    try:
        # Le service récupère org_id depuis le post source
        # On devrait ajouter org_id dans DuplicateIn, mais pour MVP on passe par le service
        
        # Workaround: on va charger le post pour obtenir org_id
        from api.databases.databases import get_core_db
        from bson import ObjectId
        
        db = get_core_db()
        post = await db["scheduled_posts"].find_one({"_id": ObjectId(body.id)})
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        org_id = post["org_id"]
        
        # Vérification multi-tenant
        if org_id != current_user.org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: org_id mismatch"
            )
        
        new_ids = await svc.duplicate(body, org_id)
        
        return {"ok": True, "ids": new_ids}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la duplication: {str(e)}"
        )
