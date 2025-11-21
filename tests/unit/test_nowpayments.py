# tests/unit/test_nowpayments.py
import pytest
import httpx
from httpx import Response
from api.services.payment_gateway.nowpayments import generate_payment_link
from api.schemas.payments import PaymentRequest
from uuid import UUID

class DummyUser:
    email = "user@example.com"

@pytest.mark.asyncio
async def test_generate_payment_link(monkeypatch):
    # on simule la réponse de NowPayments
    async def fake_post(url, json, headers):
        assert headers["x-api-key"] == "FAKE_KEY"
        return Response(200, json={"invoice_url": "https://pay.now/123"})
    monkeypatch.setenv("NOWPAYMENTS_API_KEY", "FAKE_KEY")
    monkeypatch.setattr(httpx, "post", fake_post)

    req = PaymentRequest(amount=10.5, currency="USDT", description="Test", muse_id="m1")
    url = await generate_payment_link(req, DummyUser())
    assert url == "https://pay.now/123"
