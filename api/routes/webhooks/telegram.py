from fastapi import APIRouter, HTTPException, Request
from api.core.configs import TELEGRAM_BOT_TOKEN
from api.services.chat_omnichannel.manager import ChatManager

router = APIRouter(
    prefix="/webhook/telegram",
    tags=["webhook"]
)

# Instanciation du manager de chat omnicanal
chat_manager = ChatManager()

@router.post("/{bot_token}")
async def telegram_webhook(bot_token: str, request: Request):
    """
    Point d'entrée pour Telegram.
    Telegram envoie les updates en POST sur /webhook/telegram/<BOT_TOKEN>.
    """
    # Vérification de l'authenticité du webhook
    if bot_token != TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalide")

    update = await request.json()
    try:
        # Dispatch du message vers le manager de chat omnicanal
        await chat_manager.dispatch(platform="telegram", data=update)
        return {"ok": True}
    except Exception as e:
        # En cas d'erreur interne, on renvoie un 500
        raise HTTPException(status_code=500, detail=str(e))
