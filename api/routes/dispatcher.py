from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
from services.content_distributor.dispatcher import ContentDispatcher

router = APIRouter()

# Modèle pour recevoir la requête de publication
class DispatchRequest(BaseModel):
    platform: str  # ex: "telegram"
    text: Optional[str] = None
    media_url: Optional[HttpUrl] = None
    chat_id: Optional[str] = None  # utile pour Telegram, etc.

@router.post("/dispatch")
async def dispatch_content(payload: DispatchRequest):
    try:
        dispatcher = ContentDispatcher()
        await dispatcher.dispatch(
            platform=payload.platform,
            content={
                "text": payload.text,
                "media_url": payload.media_url,
                "chat_id": payload.chat_id
            }
        )
        return {"status": "success", "message": f"Content dispatched to {payload.platform}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
