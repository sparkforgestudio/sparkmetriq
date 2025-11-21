# tests/unit/test_webhook.py
import pytest
from api.services.payment_gateway.nowpayments import process_webhook_notification
from api.schemas.payments import CryptoWebhookPayload
from api.databases.databases import db

class DummyCollection:
    updated = False
    async def update_one(self, q, u):
        assert q["invoice_id"] == "order-123"
        DummyCollection.updated = True

@pytest.mark.asyncio
async def test_process_webhook(monkeypatch):
    payload = CryptoWebhookPayload(
        payment_id="pay_1",
        order_id="order-123",
        status="confirmed",
        pay_amount=10,
        pay_currency="USDT",
        price_amount=10,
        price_currency="USDT",
    )
    # on simule la collection
    monkeypatch.setattr(db, "__getitem__", lambda self, k: DummyCollection())
    await process_webhook_notification(payload)
    assert DummyCollection.updated
