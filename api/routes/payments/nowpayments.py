from fastapi import APIRouter, Depends, HTTPException, Request
from api.schemas.payments import (
    CryptoOnrampRequest,
    CryptoOnrampResponse,
    CryptoWebhookPayload
)
from api.services.payments.nowpayments import NowPaymentsService
from api.core.auth import get_current_user  # ou le dépendance que vous utilisez
from api.models import Payment  # modèle Mongo/Pydantic de votre DB

router = APIRouter(
    prefix="/payments/crypto",
    tags=["payments"],
    dependencies=[Depends(get_current_user)]
)

service = NowPaymentsService()

@router.post("/onramp", response_model=CryptoOnrampResponse)
async def initiate_onramp(req: CryptoOnrampRequest):
    try:
        data = service.create_payment(
            price_amount=req.price_amount,
            price_currency=req.price_currency,
            pay_currency=req.pay_currency,
            order_id=req.order_id,
            callback_url=req.callback_url,
        )
        # Enregistrez en base l’invoice (Payment DB) si besoin :
        # await Payment.create({...})
        return {
            "id": data["id"],
            "payment_id": data["payment_id"],
            "pay_address": data["wallet_address"],
            "pay_amount": data["pay_amount"],
            "pay_currency": data["pay_currency"],
            "invoice_url": data["invoice_url"],
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/webhook/nowpayments")
async def nowpayments_webhook(payload: CryptoWebhookPayload):
    """
    NOWPayments POSTe ici les notifications de statut.
    """
    # 1) Vérifier éventuellement un header HMAC si vous l’avez configuré
    # 2) Mettre à jour votre DB (payment.status = payload.status)
    # 3) Si status == "finished": débloquer le contenu / activer l’abonnement
    payment = await Payment.find_one({"payment_id": payload.payment_id})
    if not payment:
        raise HTTPException(404, "Payment not found")

    payment.status = payload.status
    await payment.save()

    if payload.status == "finished":
        # e.g. call your business logic pour débloquer la Muse
        # await unlock_content_for_order(payment.order_id)
        pass

    return {"status": "ok"}
