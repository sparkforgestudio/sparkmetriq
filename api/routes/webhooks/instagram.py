# api/routes/webhooks/instagram.py
from fastapi import APIRouter, Request, HTTPException
import os

# Récupération du token de vérification depuis les configurations ou l'environnement
try:
    from api.core.configs import INSTAGRAM_VERIFY_TOKEN
except ImportError:
    INSTAGRAM_VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN")

# Import du gestionnaire de chat omnicanal
from api.services.chat_omnichannel.manager import ChatManager

router = APIRouter(prefix="/webhook/instagram", tags=["webhook"])

# Instanciation du ChatManager pour traiter les messages entrants
chat_mgr = ChatManager()

@router.get("/")
async def instagram_verify(request: Request):
    # Vérification du webhook par Instagram (GET)
    params = request.query_params
    verify_token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if verify_token != INSTAGRAM_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Token de vérification invalide")
    # Instagram attend que l'on renvoie le challenge en entier
    return int(challenge) if challenge is not None else HTTPException(status_code=400, detail="hub.challenge manquant")

@router.post("/")
async def instagram_webhook(request: Request):
    # Réception des événements Instagram (POST)
    payload = await request.json()
    # On traite chaque entrée et chaque message direct
    for entry in payload.get("entry", []):
        for dm in entry.get("messaging", []):
            # Dispatch du message via le manager
            await chat_mgr.dispatch(platform="instagram", data=dm)
    return {"status": "received"}
