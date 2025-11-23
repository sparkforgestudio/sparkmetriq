# tests/message_builder/test_preview_and_send.py
"""
Tests pour le système Message Builder (preview, création de campagne, materialization, queue).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone
from bson import ObjectId

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


@pytest.fixture
def mock_segmentation():
    """Mock du service de segmentation."""
    with patch("api.services.messaging.message_builder.build_targets") as mock:
        now = datetime.now(timezone.utc)
        mock.return_value = ([
            {
                "user_ref": "u1",
                "platform": "telegram",
                "muse_id": "m1",
                "last_active_at": now - timedelta(days=5),
                "total_spent": 29.9,
                "avg_spend": 29.9,
                "last_purchase_at": now - timedelta(days=2),
                "first_name": "John",
                "lang": "fr"
            },
            {
                "user_ref": "u2",
                "platform": "telegram",
                "muse_id": "m1",
                "last_active_at": now - timedelta(days=10),
                "total_spent": 0.0,
                "avg_spend": 0.0,
                "last_purchase_at": None,
                "first_name": None,
                "lang": "en"
            }
        ], 2)
        yield mock


@pytest.fixture
def mock_template_engine():
    """Mock du moteur de template."""
    with patch("api.services.messaging.message_builder.render_template") as mock:
        def render_side_effect(body, variables):
            # Simulation simple du rendu
            result = body
            for key, value in variables.items():
                if value:
                    result = result.replace(f"{{{{ {key} }}}}", str(value))
                    result = result.replace(f"{{{{ {key}|default('') }}}}", str(value) or "")
            return result
        
        mock.side_effect = render_side_effect
        yield mock


@pytest.mark.asyncio
async def test_create_template(mock_template_engine):
    """Test de création de template."""
    client = TestClient(app)
    
    payload = {
        "org_id": "org_demo",
        "name": "promo_ppv_fr",
        "body": "Salut {{ first_name|default('chéri') }}, offre PPV pour toi : {{ avg_spend|round(0) }}€ ❤️"
    }
    
    response = client.post("/api/message-builder/templates", json=payload)
    
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "promo_ppv_fr"
    assert "id" in body


@pytest.mark.asyncio
async def test_preview_campaign(mock_segmentation, mock_template_engine):
    """Test de preview de campagne."""
    client = TestClient(app)
    
    # Créer un template d'abord
    template_payload = {
        "org_id": "org_demo",
        "name": "test_template",
        "body": "Hello {{ first_name|default('there') }}, you spent {{ total_spent }}€"
    }
    template_resp = client.post("/api/message-builder/templates", json=template_payload)
    assert template_resp.status_code == 201
    template_id = template_resp.json()["id"]
    
    # Preview
    preview_payload = {
        "org_id": "org_demo",
        "name": "Campagne Test",
        "template_id": template_id,
        "segmentation": {
            "platforms": ["telegram"],
            "inactive_days_gte": 3,
            "limit": 10
        },
        "platform": "telegram",
        "dry_run": True
    }
    
    response = client.post("/api/message-builder/preview", json=preview_payload)
    
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert body["count_total"] >= len(body["items"])
    assert len(body["items"]) > 0
    assert "rendered" in body["items"][0]
    assert "variables" in body["items"][0]


@pytest.mark.asyncio
async def test_create_and_materialize_campaign(mock_segmentation, mock_template_engine):
    """Test de création et materialization de campagne."""
    client = TestClient(app)
    
    # Créer un template
    template_payload = {
        "org_id": "org_demo",
        "name": "test_template",
        "body": "Hello {{ first_name }}"
    }
    template_resp = client.post("/api/message-builder/templates", json=template_payload)
    template_id = template_resp.json()["id"]
    
    # Créer une campagne
    campaign_payload = {
        "org_id": "org_demo",
        "name": "Campagne Test",
        "template_id": template_id,
        "segmentation": {
            "platforms": ["telegram"],
            "inactive_days_gte": 3
        },
        "platform": "telegram"
    }
    
    create_resp = client.post("/api/message-builder/campaigns", json=campaign_payload)
    assert create_resp.status_code == 201
    campaign_id = create_resp.json()["id"]
    
    # Materialize targets
    materialize_resp = client.post(f"/api/message-builder/campaigns/{campaign_id}/materialize")
    assert materialize_resp.status_code == 200
    totals = materialize_resp.json()["totals"]
    assert totals["targets"] >= 1


@pytest.mark.asyncio
async def test_queue_messages(mock_segmentation, mock_template_engine):
    """Test de mise en queue des messages."""
    client = TestClient(app)
    
    # Créer template et campagne
    template_payload = {
        "org_id": "org_demo",
        "name": "test_template",
        "body": "Hello {{ first_name }}"
    }
    template_resp = client.post("/api/message-builder/templates", json=template_payload)
    template_id = template_resp.json()["id"]
    
    campaign_payload = {
        "org_id": "org_demo",
        "name": "Campagne Test",
        "template_id": template_id,
        "segmentation": {"platforms": ["telegram"]},
        "platform": "telegram"
    }
    create_resp = client.post("/api/message-builder/campaigns", json=campaign_payload)
    campaign_id = create_resp.json()["id"]
    
    # Materialize
    client.post(f"/api/message-builder/campaigns/{campaign_id}/materialize")
    
    # Queue (avec confirm)
    queue_payload = {
        "campaign_id": campaign_id,
        "confirm": True
    }
    queue_resp = client.post(f"/api/message-builder/campaigns/{campaign_id}/queue", json=queue_payload)
    assert queue_resp.status_code == 200
    totals = queue_resp.json()["totals"]
    assert totals["queued"] >= 1


@pytest.mark.asyncio
async def test_queue_requires_confirm():
    """Test que la queue nécessite confirm=true."""
    client = TestClient(app)
    
    queue_payload = {
        "campaign_id": "fake_id",
        "confirm": False
    }
    response = client.post("/api/message-builder/campaigns/fake_id/queue", json=queue_payload)
    assert response.status_code == 400
    assert "confirm" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_template_too_long():
    """Test que les templates trop longs sont rejetés."""
    client = TestClient(app)
    
    original_max = settings.mb_template_max_chars
    settings.mb_template_max_chars = 10
    
    try:
        payload = {
            "org_id": "org_demo",
            "name": "too_long",
            "body": "This is a very long template that exceeds the maximum character limit"
        }
        
        response = client.post("/api/message-builder/templates", json=payload)
        assert response.status_code == 400
        assert "too long" in response.json()["detail"].lower()
        
    finally:
        settings.mb_template_max_chars = original_max


@pytest.mark.asyncio
async def test_feature_disabled():
    """Test que le message builder retourne 403 si désactivé."""
    original_value = settings.feature_message_builder_enabled
    settings.feature_message_builder_enabled = False
    
    try:
        client = TestClient(app)
        
        payload = {
            "org_id": "org_demo",
            "name": "test",
            "body": "Hello"
        }
        
        response = client.post("/api/message-builder/templates", json=payload)
        assert response.status_code == 403
        
    finally:
        settings.feature_message_builder_enabled = original_value




