from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from typing import Optional

from api.services.content_distributor.dispatcher import ContentDispatcher, get_dispatcher
from api.core.auth import get_current_user
from api.schemas.users import UserResponse

router = APIRouter(prefix="/dispatcher", tags=["dispatcher"])

class DispatchRequest(BaseModel):
    platform: str  # e.g., "telegram", "instagram", etc.
    text: Optional[str] = None
    media_url: Optional[HttpUrl] = None
    chat_id: Optional[str] = None  # utile pour Telegram, etc.

class DispatchResponse(BaseModel):
    status: str
    message: str

@router.post("/", response_model=DispatchResponse)
async def dispatch_content(
    payload: DispatchRequest,
    dispatcher: ContentDispatcher = Depends(get_dispatcher),
    current_user: UserResponse = Depends(get_current_user)
) -> DispatchResponse:
    """
    Dispatcher de contenu vers des plateformes externes.
    L'utilisateur doit être authentifié.
    """
    try:
        await dispatcher.dispatch(
            platform=payload.platform,
            content={
                "text": payload.text,
                "media_url": str(payload.media_url) if payload.media_url else None,
                "chat_id": payload.chat_id,
                "agency_id": current_user.email,  # ou user.agency_id si dispo
                "muse_id": getattr(current_user, 'muse_id', None)
            }
        )
        return DispatchResponse(
            status="success",
            message=f"Content dispatched to {payload.platform}"
        )
    except Exception as e:
        # TODO: logger.error(f"Error dispatching content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )