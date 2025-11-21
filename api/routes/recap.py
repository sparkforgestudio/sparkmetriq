# api/routes/recap.py
"""
Routes REST pour le système de résumé IA des conversations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from api.schemas.users import UserResponse
from api.core.auth import get_current_user
from api.schemas.recap import (
    RecapGenerateIn, RecapOut, RecapListOut, RecapItem
)
from api.services.ai.recap_service import generate_recap
from api.services.analytics.events import emit_recap_event
from api.services.observability.activity import log_recap
from api.core.settings import settings
from api.databases.databases import get_core_db

router = APIRouter(prefix="/recap", tags=["Recap"])


@router.post("/generate", response_model=RecapOut, status_code=status.HTTP_200_OK)
async def recap_generate(
    payload: RecapGenerateIn,
    current_user: UserResponse = Depends(get_current_user)
) -> RecapOut:
    """
    Génère ou actualise un recap structuré pour une conversation.
    
    Args:
        payload: Requête de génération de recap
        current_user: Utilisateur actuel
        
    Returns:
        Recap généré
        
    Raises:
        HTTPException: 403 si feature désactivé, 400 si erreur
    """
    if not settings.feature_convo_recap_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conversation recap feature disabled"
        )
    
    try:
        out = await generate_recap(payload)
        
        # Émettre événement analytics
        await emit_recap_event(
            org_id=payload.org_id,
            conversation_id=payload.conversation_id,
            kind=payload.kind,
            count=out.window.get("count", 0)
        )
        
        # Logger l'action
        await log_recap(
            org_id=payload.org_id,
            conversation_id=payload.conversation_id,
            actor=getattr(current_user, "email", "system"),
            status="success"
        )
        
        return out
        
    except RuntimeError as e:
        await log_recap(
            org_id=payload.org_id,
            conversation_id=payload.conversation_id,
            actor=getattr(current_user, "email", "system"),
            status="failed",
            note=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        await log_recap(
            org_id=payload.org_id,
            conversation_id=payload.conversation_id,
            actor=getattr(current_user, "email", "system"),
            status="failed",
            note=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await log_recap(
            org_id=payload.org_id,
            conversation_id=payload.conversation_id,
            actor=getattr(current_user, "email", "system"),
            status="failed",
            note=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recap generation failed: {str(e)}"
        )


@router.get("/get", response_model=RecapOut, status_code=status.HTTP_200_OK)
async def recap_get(
    org_id: str = Query(..., description="ID de l'organisation"),
    conversation_id: str = Query(..., description="ID de la conversation"),
    current_user: UserResponse = Depends(get_current_user)
) -> RecapOut:
    """
    Récupère le dernier recap d'une conversation.
    
    Args:
        org_id: ID de l'organisation
        conversation_id: ID de la conversation
        current_user: Utilisateur actuel
        
    Returns:
        Recap trouvé
        
    Raises:
        HTTPException: 404 si non trouvé
    """
    db = get_core_db()
    
    doc = await db["conversation_recaps"].find_one({
        "org_id": org_id,
        "conversation_id": conversation_id
    })
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recap not found"
        )
    
    # S'assurer que structured existe
    if "structured" not in doc:
        doc["structured"] = {}
    
    # Convertir _id en string si présent
    if "_id" in doc:
        del doc["_id"]
    
    return RecapOut(**doc)


@router.get("/list", response_model=RecapListOut, status_code=status.HTTP_200_OK)
async def recap_list(
    org_id: str = Query(..., description="ID de l'organisation"),
    muse_id: Optional[str] = Query(None, description="ID de la muse (filtre optionnel)"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(20, ge=1, le=100, description="Taille de page"),
    current_user: UserResponse = Depends(get_current_user)
) -> RecapListOut:
    """
    Liste les recaps récents pour une organisation/muse.
    
    Args:
        org_id: ID de l'organisation
        muse_id: ID de la muse (optionnel)
        page: Numéro de page
        page_size: Taille de page
        current_user: Utilisateur actuel
        
    Returns:
        Liste de recaps
    """
    db = get_core_db()
    
    query = {"org_id": org_id}
    if muse_id:
        query["muse_id"] = muse_id
    
    skip = max(0, (page - 1) * page_size)
    
    cursor = (
        db["conversation_recaps"]
        .find(query)
        .sort("updated_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    
    docs = await cursor.to_list(length=page_size)
    
    items = []
    for d in docs:
        window = d.get("window", {}) or {}
        items.append(RecapItem(
            id=str(d.get("_id", "")),
            conversation_id=d.get("conversation_id", ""),
            updated_at=d.get("updated_at"),
            last_message_ts=d.get("last_message_ts"),
            kind=window.get("kind", "full")
        ))
    
    return RecapListOut(items=items)



