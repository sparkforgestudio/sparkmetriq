import httpx
import os
from schemas.payments import PaymentRequest
from schemas.users import UserResponse

CRYPTOBOT_API_TOKEN = os.getenv("CRYPTOBOT_API_TOKEN")
CRYPTOBOT_BASE_URL = "https://pay.crypt.bot"

async def generate_payment_link(payment_request: PaymentRequest, user: UserResponse) -> str:
    callback_url = f"https://yourdomain.com/payments/webhook"
    
    payload = {
        "asset": payment_request.currency.upper(),
        "amount": str(payment_request.amount),
        "description": payment_request.description,
        "hidden_message": f"Access granted to content by {payment_request.muse_id}",
        "paid_btn_name": "open_bot",
        "paid_btn_url": f"https://t.me/{payment_request.muse_id}_bot",
        "payload": f"user:{user.email}|muse:{payment_request.muse_id}",
        "allow_comments": False,
        "allow_anonymous": False,
        "expires_in": 900,
        "callback_url": callback_url
    }

    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_API_TOKEN
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CRYPTOBOT_BASE_URL}/api/createInvoice", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["result"]["pay_url"]
