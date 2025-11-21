# tests/toggles/test_feature_toggles.py
"""
Tests de bascule des feature flags et entitlements pour CloudPhone et OTP.
"""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from api.main import app
from api.core.settings import settings
from api.services.orgs import set_entitlements, get_entitlements
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.databases.databases import db


# Mock pour l'authentification
def mock_get_current_user():
    """Mock de l'utilisateur courant pour les tests."""
    return UserResponse(
        id="test_user_id",
        email="test@org.io",
        org_id="org_test",
        is_admin=True,
        roles=[]
    )


@pytest.fixture(autouse=True)
def override_user():
    """Override l'authentification pour tous les tests."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def cleanup_entitlements():
    """Nettoyer les entitlements après chaque test."""
    yield
    await db["org_entitlements"].delete_many({"org_id": "org_test"})


@pytest.mark.asyncio
async def test_cloudphone_flag_on_but_entitlement_off():
    """Test que CloudPhone retourne 403 si l'entitlement est off."""
    # Définir l'entitlement à off
    await set_entitlements("org_test", {
        "cloudphone": {"active": False},
        "otp": {"active": True}
    })
    
    client = TestClient(app)
    
    # Tenter de créer un device (exemple)
    resp = client.post("/api/mobile-cloud/devices", json={})
    
    # Devrait retourner 403 car entitlement off
    assert resp.status_code == 403
    assert "not enabled" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cloudphone_flag_on_and_entitlement_on():
    """Test que CloudPhone fonctionne si flag et entitlement sont on."""
    # Définir l'entitlement à on
    await set_entitlements("org_test", {
        "cloudphone": {"active": True},
        "otp": {"active": False}
    })
    
    client = TestClient(app)
    
    # Tenter d'accéder à une route GET (qui devrait fonctionner)
    resp = client.get("/api/mobile-cloud/profiles")
    
    # Devrait retourner 200 (liste vide) ou 422 si validation échoue
    # Mais pas 403 car entitlement est activé
    assert resp.status_code != 403
    assert resp.status_code in (200, 422, 400)


@pytest.mark.asyncio
async def test_otp_flag_on_but_entitlement_off():
    """Test que OTP retourne 403 si l'entitlement est off."""
    await set_entitlements("org_test", {
        "cloudphone": {"active": True},
        "otp": {"active": False}
    })
    
    client = TestClient(app)
    
    resp = client.post("/api/otp/reserve", json={
        "org_id": "org_test",
        "app": "instagram",
        "country": "US",
        "slot_id": "test_slot"
    })
    
    assert resp.status_code == 403
    assert "not enabled" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_otp_flag_on_and_entitlement_on():
    """Test que OTP fonctionne si flag et entitlement sont on."""
    await set_entitlements("org_test", {
        "cloudphone": {"active": False},
        "otp": {"active": True}
    })
    
    client = TestClient(app)
    
    # Tenter de réserver une session OTP
    resp = client.post("/api/otp/reserve", json={
        "org_id": "org_test",
        "app": "instagram",
        "country": "US",
        "slot_id": "test_slot"
    })
    
    # Ne devrait pas être 403 (entitlement activé)
    assert resp.status_code != 403
    # Peut être 400/404/422 pour d'autres raisons de validation
    assert resp.status_code in (200, 400, 404, 422, 500)


@pytest.mark.asyncio
async def test_get_entitlements_endpoint():
    """Test l'endpoint GET /api/org/entitlements."""
    # Définir des entitlements
    await set_entitlements("org_test", {
        "cloudphone": {"active": True},
        "otp": {"active": False}
    })
    
    client = TestClient(app)
    
    resp = client.get("/api/org/entitlements")
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["org_id"] == "org_test"
    assert "features" in data
    assert data["features"]["cloudphone"]["active"] is True
    assert data["features"]["otp"]["active"] is False


@pytest.mark.asyncio
async def test_update_entitlements_endpoint():
    """Test l'endpoint PUT /api/org/entitlements (admin uniquement)."""
    client = TestClient(app)
    
    # Mettre à jour les entitlements
    resp = client.put("/api/org/entitlements", json={
        "features": {
            "cloudphone": {"active": True},
            "otp": {"active": True}
        }
    })
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["org_id"] == "org_test"
    assert data["features"]["cloudphone"]["active"] is True
    assert data["features"]["otp"]["active"] is True
    
    # Vérifier que c'est bien sauvegardé
    entitlements = await get_entitlements("org_test")
    assert entitlements["features"]["cloudphone"]["active"] is True
    assert entitlements["features"]["otp"]["active"] is True


@pytest.mark.asyncio
async def test_update_entitlements_non_admin():
    """Test que seuls les admins peuvent mettre à jour les entitlements."""
    # Créer un mock pour un utilisateur non-admin
    def mock_non_admin_user():
        return UserResponse(
            id="test_user_id",
            email="test@org.io",
            org_id="org_test",
            is_admin=False,
            roles=[]
        )
    
    app.dependency_overrides[get_current_user] = mock_non_admin_user
    
    try:
        client = TestClient(app)
        
        resp = client.put("/api/org/entitlements", json={
            "features": {
                "cloudphone": {"active": True}
            }
        })
        
        assert resp.status_code == 403
        assert "admin" in resp.json()["detail"].lower()
        
    finally:
        app.dependency_overrides[get_current_user] = mock_get_current_user



