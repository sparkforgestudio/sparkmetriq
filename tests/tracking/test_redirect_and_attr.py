# tests/tracking/test_redirect_and_attr.py
"""
Tests pour le système de suivi des liens & attribution des revenus.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone

from api.main import app
from api.core.settings import settings
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.databases.databases import get_core_db, get_bi_db


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


@pytest.mark.asyncio
async def test_create_tracking_link():
    """Test de création d'un lien traqué."""
    client = TestClient(app)
    
    payload = {
        "org_id": "org_demo",
        "destination_url": "https://example.com/offer",
        "utm_source": "tiktok",
        "utm_medium": "bio",
        "utm_campaign": "launch",
        "utm_content": "teaser1",
        "promo_code": "PROMO10"
    }
    
    response = client.post("/api/tracking/links", json=payload)
    
    assert response.status_code == 201
    body = response.json()
    assert body["code"]
    assert body["short_url"]
    assert body["utm"]["utm_source"] == "tiktok"
    assert body["promo_code"] == "PROMO10"


@pytest.mark.asyncio
async def test_redirect_and_log_click():
    """Test de redirection et log d'un clic."""
    client = TestClient(app)
    
    # Créer un lien d'abord
    payload = {
        "org_id": "org_demo",
        "destination_url": "https://example.com/offer",
        "utm_source": "tiktok",
        "utm_medium": "bio"
    }
    create_resp = client.post("/api/tracking/links", json=payload)
    assert create_resp.status_code == 201
    link = create_resp.json()
    code = link["code"]
    
    # Simuler un clic via redirection
    redirect_resp = client.get(
        f"/r/{code}?u=u123",
        headers={
            "user-agent": "pytest",
            "referer": "https://t.co/xyz"
        },
        follow_redirects=False
    )
    
    assert redirect_resp.status_code in (302, 307)
    
    # Vérifier que la destination contient les UTM
    location = redirect_resp.headers.get("location", "")
    assert "utm_source=tiktok" in location or "utm_source=tiktok" in location.lower()


@pytest.mark.asyncio
async def test_attribution_payment(mongo_client):
    """Test d'attribution d'un paiement à une source."""
    # Créer un lien et un clic d'abord
    from api.databases.databases import get_core_db, get_bi_db
    
    db_core = get_core_db()
    db_bi = get_bi_db()
    
    org_id = "org_demo"
    user_ref = "u123"
    now = datetime.now(timezone.utc)
    
    # Créer un lien
    link_doc = {
        "org_id": org_id,
        "code": "testcode",
        "destination_url": "https://example.com",
        "utm": {"utm_source": "tiktok", "utm_medium": "bio"},
        "created_at": now,
        "clicks_total": 0
    }
    await db_core["tracking_links"].insert_one(link_doc)
    
    # Créer un clic
    click_doc = {
        "org_id": org_id,
        "code": "testcode",
        "user_ref": user_ref,
        "ts": now - timedelta(hours=1),
        "utm": {"utm_source": "tiktok", "utm_medium": "bio"},
        "ip_hash": "test_hash",
        "ua": "test",
        "ref": "test"
    }
    await db_core["tracking_clicks"].insert_one(click_doc)
    
    # Appeler l'attribution
    from api.services.tracking.attribution_service import attribute_payment
    
    attrib = await attribute_payment(org_id, user_ref, 19.9, now)
    
    assert attrib["source"] == "tiktok"
    assert attrib["amount"] == 19.9
    
    # Vérifier l'insertion en base BI
    found = await db_bi["revenue_attribution_daily"].find_one({
        "org_id": org_id,
        "user_ref": user_ref
    })
    
    assert found is not None
    assert found["source"] == "tiktok"
    assert float(found["amount"]) == 19.9


@pytest.mark.asyncio
async def test_stats_sources(mongo_client):
    """Test des statistiques par source."""
    client = TestClient(app)
    
    from api.databases.databases import get_bi_db
    
    db_bi = get_bi_db()
    org_id = "org_demo"
    now = datetime.now(timezone.utc)
    
    # Créer des attributions de test
    await db_bi["revenue_attribution_daily"].insert_many([
        {
            "org_id": org_id,
            "day": now.date().isoformat(),
            "ts": now,
            "amount": 50.0,
            "source": "tiktok",
            "medium": "bio",
            "campaign": "launch",
            "content": "teaser1",
            "user_ref": "u1",
            "model": "last_touch"
        },
        {
            "org_id": org_id,
            "day": now.date().isoformat(),
            "ts": now,
            "amount": 30.0,
            "source": "instagram",
            "medium": "story",
            "campaign": "launch",
            "content": None,
            "user_ref": "u2",
            "model": "last_touch"
        }
    ])
    
    # Récupérer les stats
    response = client.get(
        "/api/tracking/stats/sources",
        params={
            "org_id": org_id,
            "date_from": (now - timedelta(days=1)).isoformat(),
            "date_to": (now + timedelta(days=1)).isoformat()
        }
    )
    
    assert response.status_code == 200
    body = response.json()
    assert body["revenue_total"] == 80.0
    assert len(body["by_source"]) >= 2


@pytest.mark.asyncio
async def test_link_expired():
    """Test qu'un lien expiré retourne 410."""
    client = TestClient(app)
    
    # Créer un lien expiré
    from api.databases.databases import get_core_db
    
    db_core = get_core_db()
    
    expired_link = {
        "org_id": "org_demo",
        "code": "expired",
        "destination_url": "https://example.com",
        "expires_at": datetime.now(timezone.utc) - timedelta(days=1),
        "created_at": datetime.now(timezone.utc) - timedelta(days=2),
        "clicks_total": 0,
        "utm": {}
    }
    await db_core["tracking_links"].insert_one(expired_link)
    
    # Essayer de rediriger
    response = client.get("/r/expired", follow_redirects=False)
    
    assert response.status_code == 410
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_link_not_found():
    """Test qu'un lien inexistant retourne 404."""
    client = TestClient(app)
    
    response = client.get("/r/nonexistent", follow_redirects=False)
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_feature_disabled():
    """Test que le tracking retourne 403 si désactivé."""
    original_value = settings.feature_link_tracking_enabled
    settings.feature_link_tracking_enabled = False
    
    try:
        client = TestClient(app)
        
        payload = {
            "org_id": "org_demo",
            "destination_url": "https://example.com"
        }
        
        response = client.post("/api/tracking/links", json=payload)
        assert response.status_code == 403
        
    finally:
        settings.feature_link_tracking_enabled = original_value




