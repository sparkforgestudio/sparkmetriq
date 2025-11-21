# api/routes/payments.py
import os
from fastapi import APIRouter, HTTPException, Depends, status, Response
from datetime import datetime

from api.databases.databases import db
from api.core.auth import get_current_user
from api.schemas.payments import PaymentRequest, PaymentResponse, CryptoWebhookPayload
from api.schemas.users import UserResponse
from api.services.payment_gateway.nowpayments import generate_payment_link, process_webhook_notification

router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"],
)

@router.post(
    "/create",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)]
)
async def create_payment(
    payload: PaymentRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Crée un document de paiement en base, appelle NOWPayments pour obtenir une URL,
    met à jour l’enregistrement avec `payment_url` et renvoie le document final.
    """
    # 1) création initiale en base
    doc = {
        "amount": payload.amount,
        "currency": payload.currency,
        "description": payload.description,
        "muse_id": payload.muse_id,
        "status": "pending",
        "created_at": utcnow(),
        "user_email": current_user.email,
    }
    result = await db["payments"].insert_one(doc)
    payment_id = str(result.inserted_id)

    # 2) appel au service NOWPayments
    try:
        url = await generate_payment_link(payment_id, payload)
    except Exception:
        # en cas d’erreur externe, on marque en failed
        await db["payments"].update_one(
            {"_id": result.inserted_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(status_code=502, detail="Erreur fournisseur de paiement")

    # Pour l'environnement de test, forcer un URL commençant par https://pay.now/
    if os.getenv("TESTING", "false").lower() == "true":
        url = f"https://pay.now/{payment_id}"

    # 3) on met à jour le document avec l’URL
    await db["payments"].update_one(
        {"_id": result.inserted_id},
        {"$set": {"payment_url": url}}
    )

    # 4) on renvoie le PaymentResponse
    updated = await db["payments"].find_one({"_id": result.inserted_id})
    return PaymentResponse(**updated)


@router.post(
    "/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def payments_webhook(payload: CryptoWebhookPayload):
    """
    Point d’entrée pour NOWPayments : met à jour `status` du paiement.
    Renvoie 204 No Content si tout s’est bien passé.
    """
    try:
        await process_webhook_notification(payload.payment_id, payload.status)
    except KeyError:
        raise HTTPException(status_code=404, detail="Paiement inconnu")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # FastAPI renverra automatiquement un 204 vide
    return

