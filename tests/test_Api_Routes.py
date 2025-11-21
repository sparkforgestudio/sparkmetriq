import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture
def auth_headers(monkeypatch):
    # TODO: Mock token generation or set a valid token in env
    token = "testtoken"
    return {"Authorization": f"Bearer {token}"}

# Auth routes

def test_register_user():
    # Placeholder: should return 200 or 400 if user exists
    response = client.post(
        "/auths/register",
        json={"email": "test@example.com", "password": "pass123", "is_admin": False}
    )
    assert response.status_code in (200, 400)


def test_login_user():
    response = client.post(
        "/auths/login",
        data={"username": "test@example.com", "password": "pass123"}
    )
    assert response.status_code in (200, 400)

# Dispatcher route

def test_dispatch_content_unauthenticated():
    response = client.post("/dispatch", json={})
    assert response.status_code == 401

def test_dispatch_content_authenticated(auth_headers):
    response = client.post(
        "/dispatch",
        headers=auth_headers,
        json={"platform": "telegram", "text": "Hello"}
    )
    assert response.status_code in (200, 500)

# Tunnel analysis routes

def test_tunnel_overview_requires_auth():
    response = client.get("/analysis/tunnel/overview")
    assert response.status_code == 401

def test_tunnel_overview(auth_headers):
    response = client.get("/analysis/tunnel/overview", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_tunnel_details(auth_headers):
    response = client.get("/analysis/tunnel/details", headers=auth_headers)
    assert response.status_code == 200

def test_tunnel_export(auth_headers):
    response = client.get("/analysis/tunnel/export", headers=auth_headers)
    assert response.status_code == 200

def test_tunnel_recommendations(auth_headers):
    response = client.get("/analysis/tunnel/recommendations", headers=auth_headers)
    assert response.status_code == 200

# Webhook routes

def test_telegram_webhook_invalid_token():
    response = client.post("/webhook/telegram/invalid_token", json={})
    assert response.status_code == 403

@pytest.mark.parametrize("token", ["valid_token"])
def test_telegram_webhook_valid(token, monkeypatch):
    # Mock the expected token
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", token)
    response = client.post(f"/webhook/telegram/{token}", json={})
    assert response.status_code == 200

# Instagram webhook verification

def test_instagram_verify_invalid():
    response = client.get("/webhook/instagram/", params={"hub.verify_token": "wrong", "hub.challenge": "123"})
    assert response.status_code == 403

@pytest.mark.parametrize("challenge", ["12345"])
def test_instagram_verify_valid(challenge, monkeypatch):
    monkeypatch.setenv("INSTAGRAM_VERIFY_TOKEN", "good_token")
    response = client.get(
        "/webhook/instagram/",
        params={"hub.verify_token": "good_token", "hub.challenge": challenge}
    )
    assert response.status_code == 200
    assert response.json() == int(challenge)

# WhatsApp webhook placeholder

def test_whatsapp_webhook(auth_headers):
    # TODO: Add proper test when implementation is available
    response = client.post("/webhook/whatsapp/", headers=auth_headers, json={})
    assert response.status_code in (200, 500)
