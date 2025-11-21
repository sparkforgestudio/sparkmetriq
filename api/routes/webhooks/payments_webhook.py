# api/routes/payments_webhook.py
from fastapi import APIRouter, Request
from api.databases.databases import db
from datetime import datetime

router = APIRouter()

@router.post("/webhook")
async def cryptobot_webhook(request: Request):
    data = await request.json()

    # On vérifie que le paiement est validé
    if data.get("status") != "paid":
        return {"message": "Payment not successful"}

    # Extraire les informations du payload (ex: "user:email@example.com|muse:muse123")
    payload = data.get("payload", "")
    try:
        user_email = payload.split("|")[0].split(":")[1]
        muse_id = payload.split("|")[1].split(":")[1]
    except (IndexError, ValueError):
        return {"message": "Invalid payload format"}

    # Enregistrer la transaction dans la collection 'payments'
    await db["payments"].insert_one({
        "email": user_email,
        "muse_id": muse_id,
        "amount": data.get("amount"),
        "currency": data.get("asset"),
        "invoice_id": data.get("invoice_id"),
        "status": "paid",
        "created_at": utcnow()
    })

    # Optionnel : Notifier l'utilisateur via Telegram via un autre service
    # await some_function_to_notify(user_email)

    return {"message": "Payment received"}
