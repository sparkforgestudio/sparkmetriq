from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
from services.content_distributor.dispatcher import ContentDispatcher, get_dispatcher
from api.core.auths import get_current_user
from api.schemas.users import UserResponse

router = APIRouter()

# Modèle pour recevoir la requête de publication
class DispatchRequest(BaseModel):
    platform: str  # ex: "telegram", "instagram", etc.
    text: Optional[str] = None
    media_url: Optional[HttpUrl] = None
    chat_id: Optional[str] = None  # utile pour Telegram, etc.

# Modèle de réponse pour homogénéiser l’output
class DispatchResponse(BaseModel):
    status: str
    message: str
# services/content_distributor/dispatcher.py

class ContentDispatcher:
    async def dispatch(self, platform: str, content: dict):
        # Logique de dispatch selon la plateforme
        # Par exemple, envoi à un service externe ou mise en file d'attente
        ...

def get_dispatcher() -> ContentDispatcher:
    return ContentDispatcher()

@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_content(
    payload: DispatchRequest,
    dispatcher: ContentDispatcher = Depends(get_dispatcher),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Point d'API pour dispatcher le contenu vers la plateforme ciblée.
    L'utilisateur doit être authentifié pour accéder à ce service.
    """
    try:
        await dispatcher.dispatch(
            platform=payload.platform,
            content={
                "text": payload.text,
                "media_url": payload.media_url,
                "chat_id": payload.chat_id
            }
        )
        return DispatchResponse(status="success", message=f"Content dispatched to {payload.platform}")
    except Exception as e:
        # On peut ajouter ici une journalisation des erreurs selon les normes du projet
        raise HTTPException(status_code=500, detail=str(e))
