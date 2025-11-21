# api/routes/chats.py

from typing import Any, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.chat import ChatMessageIn, ChatMessageOut, ChatHistory
from api.services.chat_omnichannel.manager import (
    handle_message,
    get_history,
    dispatch_message,
)

router = APIRouter(prefix="/chat", tags=["chat"])


# --- 1) Envoyer un message à l'IA ---
@router.post(
    "/send",
    name="chat_send",  # utile pour test_client.app.url_path_for("chat_send")
    response_model=ChatMessageOut,
    status_code=status.HTTP_200_OK,
)
async def send_chat_message(
    payload: ChatMessageIn,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Envoie un message utilisateur à l’IA et renvoie la réponse.
    Utilise le manager (DeepSeek/RAG peuvent être branchés en interne).
    """
    try:
        return await handle_message(
            user_email=current_user.email,
            conversation_id=payload.conversation_id,
            message=payload.message,
            platform=payload.platform,  # Utiliser les champs du payload
            user_id=payload.user_id,
            metadata=payload.metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 2) Récupérer l’historique paginé ---
@router.get(
    "/history/{conversation_id}",
    response_model=ChatHistory,
    status_code=status.HTTP_200_OK,
)
async def chat_history(
    conversation_id: str,
    skip: int = Query(0, ge=0, description="Offset de pagination"),
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    role: Optional[str] = Query(
        None,
        pattern="^(user|bot)$",  # Pydantic v2 : pattern (remplace regex)
        description="Filtrer par rôle : user|bot",
    ),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Retourne l’historique d’une conversation sous forme paginée.
    """
    try:
        total, raw_items = await get_history(
            conversation_id=conversation_id,
            skip=skip,
            limit=limit,
            role=role,
        )
        if raw_items is None:
            raise KeyError

        messages = [
            ChatMessageOut(
                conversation_id=conversation_id,
                message=item.get("text", ""),
                attachments=item.get("attachments"),
                timestamp=item["timestamp"],
            )
            for item in raw_items
        ]

        return ChatHistory(
            conversation_id=conversation_id,
            skip=skip,
            limit=limit,
            total=total,
            messages=messages,
        )

    except KeyError:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 3) Webhook omnicanal ---
class ChatWebhookPayload(BaseModel):
    muse_id: str = Field(..., description="ID de la muse destinataire")
    user_id: str = Field(..., description="Identifiant utilisateur sur la plateforme source")
    message: str = Field(..., description="Contenu du message entrant")
    metadata: Optional[dict[str, Any]] = None


@router.post(
    "/webhook/{platform}",
    status_code=status.HTTP_200_OK,
)
async def receive_chat_webhook(
    platform: Literal["telegram", "instagram", "whatsapp", "snapchat", "threads"],
    payload: ChatWebhookPayload,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Point d'entrée unique pour les messages entrants depuis les canaux supportés.
    """
    try:
        reply = await dispatch_message(
            platform=platform,
            muse_id=payload.muse_id,
            user_id=payload.user_id,
            message=payload.message,
            metadata=payload.metadata,
        )
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
