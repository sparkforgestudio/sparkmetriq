# api/services/payment_gateway/nowpayments.py
import httpx
from api.schemas.payments import PaymentRequest, CryptoWebhookPayload
from api.schemas.payments import CryptoOnrampResponse
from api.core.configs import NOWPAYMENTS_API_KEY, NOWPAYMENTS_URL

async def generate_payment_link(request: PaymentRequest, user) -> str:
    """
    Appelle l’API NOWPayments pour créer une charge on-ramp.
    Retourne l’URL d’invoice à renvoyer au front.
    """
    body = {
        "price_amount": request.amount,
        "price_currency": request.currency,
        "pay_currency": request.currency,
        "order_id": f"{user.email}-{request.muse_id}-{int(request.amount*100)}",
        "callback_url": f"{NOWPAYMENTS_URL}/api/payments/webhook",
        "success_url": request.description,  # ou un champ dédié
    }
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{NOWPAYMENTS_URL}/v1/invoice", json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    return data["invoice_url"]

async def process_webhook_notification(payload: CryptoWebhookPayload) -> None:
    """
    Traite la notification envoyée par NOWPayments :
    - Vérifie le statut
    - Met à jour la collection `payments` dans MongoDB
    """
    from api.databases.databases import db

    # Exemple de mapping de statut NOWPayments vers notre modèle
    status_map = {
        "waiting": "pending",
        "confirmed": "paid",
        "finished": "paid",
        "expired": "failed",
    }
    new_status = status_map.get(payload.status, "pending")

    await db["payments"].update_one(
        {"invoice_id": payload.payment_id},
        {"$set": {
            "status": new_status,
            "pay_amount": payload.pay_amount,
            "pay_currency": payload.pay_currency,
            "price_amount": payload.price_amount,
            "price_currency": payload.price_currency,
        }}
    )
