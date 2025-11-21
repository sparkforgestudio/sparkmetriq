# tests/integration/test_payments_endpoints.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture(autouse=True)
def stub_nowpayments(monkeypatch):
    """
    Stub NOWPayments calls to return a fixed payment URL.
    """
    async def fake_generate_payment_link(payment_id, payload):
        return "https://pay.now/12345"
    # Ensure the service uses our fake key
    monkeypatch.setenv("NOWPAYMENTS_API_KEY", "FAKE_KEY")
    import api.services.payment_gateway.nowpayments as np
    monkeypatch.setattr(np, "generate_payment_link", fake_generate_payment_link)

@pytest.fixture(scope="session")
def client():
    """
    TestClient fixture for HTTP requests against the FastAPI app.
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers(client):
    """
    Registers a test user and returns the Authorization header.
    """
    payload = {"email": "test@example.com", "password": "password123"}
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200, f"Registration failed: {resp.status_code} {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_payment_requires_auth(client):
    """
    Ensure creating a payment without auth returns 401.
    """
    r = client.post(
        "/api/payments/create", json={
            "amount": 1.23,
            "currency": "USDT",
            "description": "Test",
            "muse_id": "muse1"
        }
    )
    assert r.status_code == 401


@pytest.mark.skip(reason="Webhook E2E en cours, skip temporaire")
def test_create_and_webhook_flow(client, auth_headers):
    """
    End-to-end flow: create a payment and process its webhook.
    (temporarily skipped)
    """
    # Create payment
    payload = {
        "amount": 5.0,
        "currency": "USDT",
        "description": "Test",
        "muse_id": "muse1"
    }
    r = client.post(
        "/api/payments/create",
        headers=auth_headers,
        json=payload
    )
    assert r.status_code == 201
    data = r.json()
    assert data.get("payment_url", "").startswith("https://pay.now/")

    # Simulate webhook notification
    webhook = {
        "payment_id": data.get("payment_id"),
        "status": "finished",
        "pay_amount": 5.0,
        "pay_currency": "USDT",
        "price_amount": 5.0,
        "price_currency": "USDT",
    }
    r2 = client.post("/api/payments/webhook", json=webhook)
    assert r2.status_code == 204
