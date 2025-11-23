# api/routes/translator.py
"""
Routes REST pour le système de traduction IA.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from api.schemas.users import UserResponse
from api.core.auth import get_current_user
from api.schemas.translator import (
    TranslateIn, TranslateOut, BatchTranslateIn, BatchTranslateOut
)
from api.services.ai.translate_service import translate_once
from api.services.analytics.events import emit_translation_event
from api.services.observability.activity import log_translation_action
from api.core.settings import settings

router = APIRouter(prefix="/translator", tags=["Translator"])


@router.post("/translate", response_model=TranslateOut, status_code=status.HTTP_200_OK)
async def translate(
    payload: TranslateIn,
    current_user: UserResponse = Depends(get_current_user)
) -> TranslateOut:
    """
    Traduit et réécrit un texte avec contrôle du ton, emojis et formalité.
    
    Args:
        payload: Requête de traduction
        current_user: Utilisateur actuel (depuis auth)
        
    Returns:
        Résultat de traduction
        
    Raises:
        HTTPException: 403 si feature désactivé, 400 si erreur
    """
    if not settings.feature_translator_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Translator feature disabled"
        )
    
    try:
        # Utiliser org_id de l'utilisateur si non fourni
        if not payload.org_id:
            payload.org_id = current_user.org_id
        
        # Effectuer la traduction
        result = await translate_once(payload)
        
        # Émettre événement analytics
        await emit_translation_event(
            org_id=payload.org_id or current_user.org_id or "default",
            conversation_id=payload.conversation_id,
            direction="inbound" if payload.user_role == "fan" else "outbound",
            source=result.source_lang,
            target=result.target_lang
        )
        
        # Logger l'action
        await log_translation_action(
            org_id=payload.org_id or current_user.org_id or "default",
            conversation_id=payload.conversation_id,
            actor=getattr(current_user, "email", "system"),
            length=len(payload.text)
        )
        
        return result
        
    except RuntimeError as e:
        # Rate limit ou feature disabled
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN if "rate limit" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/translate:batch", response_model=BatchTranslateOut, status_code=status.HTTP_200_OK)
async def translate_batch(
    batch: BatchTranslateIn,
    current_user: UserResponse = Depends(get_current_user)
) -> BatchTranslateOut:
    """
    Traduit plusieurs textes en lot.
    
    Args:
        batch: Requête de traduction par lot
        current_user: Utilisateur actuel
        
    Returns:
        Résultats de traduction par lot
    """
    if not settings.feature_translator_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Translator feature disabled"
        )
    
    out_items: List[TranslateOut] = []
    
    for item in batch.items:
        try:
            # Utiliser org_id de l'utilisateur si non fourni
            if not item.org_id:
                item.org_id = current_user.org_id
            
            res = await translate_once(item)
            out_items.append(res)
            
            # Émettre événement analytics pour chaque traduction
            await emit_translation_event(
                org_id=item.org_id or current_user.org_id or "default",
                conversation_id=item.conversation_id,
                direction="inbound" if item.user_role == "fan" else "outbound",
                source=res.source_lang,
                target=res.target_lang
            )
            
        except Exception as e:
            # Ajouter un marqueur d'échec minimal
            out_items.append(TranslateOut(
                source_lang=item.source_lang or "und",
                target_lang=item.target_lang,
                original=item.text,
                translated="",
                rewritten=f"[error] {str(e)}",
                quality="needs_review"
            ))
    
    return BatchTranslateOut(items=out_items)




