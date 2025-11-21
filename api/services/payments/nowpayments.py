import os, requests
from typing import Dict, Any
from api.core.configs import NOWPAYMENTS_API_KEY, NOWPAYMENTS_BASE_URL

class NowPaymentsService:
    def __init__(self):
        if not NOWPAYMENTS_API_KEY:
            raise ValueError("NOWPAYMENTS_API_KEY non configuré")
        self.base = NOWPAYMENTS_BASE_URL
        self.headers = {
            "x-api-key": NOWPAYMENTS_API_KEY,
            "Content-Type": "application/json"
        }

    def create_payment(self,
                       price_amount: float,
                       price_currency: str = "EUR",
                       pay_currency: str = "USDT",
                       order_id: str = None,
                       callback_url: str = None
                       ) -> Dict[str, Any]:
        """
        Crée une facture NOWPayments pour un paiement carte → USDT.
        """
        payload = {
            "price_amount": price_amount,
            "price_currency": price_currency,
            "pay_currency": pay_currency,
        }
        if order_id:
            payload["order_id"] = order_id
        if callback_url:
            payload["callback_url"] = callback_url

        resp = requests.post(f"{self.base}/v1/payment", json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        resp = requests.get(f"{self.base}/v1/payment/{payment_id}", headers=self.headers)
        resp.raise_for_status()
        return resp.json()
