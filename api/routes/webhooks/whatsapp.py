# api/routes/webhooks/whatsapp.py

from fastapi import APIRouter, HTTPException, Request
from api.core.configs import WHATSAPP_VERIFY_TOKEN
from api.services.chat_omnichannel.manager import ChatManager

router = APIRouter(
    prefix="/webhook/whatsapp",
    tags=["webhook"],
)

# Instanciation unique du manager
chat_mgr = ChatManager()


@router.get("/")
async def whatsapp_verify(request: Request):
    """
    Vérification du webhook WhatsApp Business API.
    WhatsApp envoie en GET les params 'hub.verify_token' et 'hub.challenge'.
    """
    params = dict(request.query_params)
    if params.get("hub.verify_token") != WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Token de vérification invalide")
    # On retourne simplement le challenge en int
    return int(params.get("hub.challenge"))


@router.post("/")
async def whatsapp_webhook(request: Request):
    """
    Réception des messages entrants depuis WhatsApp.
    On délègue tout le traitement au ChatManager (normalisation, contexte, IA, renvoi).
    """
    payload = await request.json()
    try:
        await chat_mgr.dispatch(platform="whatsapp", data=payload)
        return {"status": "ok"}
    except Exception as e:
        # Le manager loggue déjà les détails de l’erreur
        raise HTTPException(status_code=500, detail=str(e))
