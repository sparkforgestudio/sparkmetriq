# tests/recap/test_recap_routes.py
"""
Tests pour les routes du système de résumé IA des conversations.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone
from api.main import app
from api.core.settings import settings
from api.core.auth import get_current_user
from api.schemas.users import UserResponse


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
def mock_recap_service():
    """Mock du service de recap."""
    with patch("api.services.ai.recap_service.generate_recap") as mock:
        from api.schemas.recap import RecapOut, RecapStructured
        
        mock.return_value = RecapOut(
            org_id="org_demo",
            conversation_id="conv_42",
            muse_id="muse_1",
            user_id="user_1",
            last_message_ts=datetime.now(timezone.utc),
            window={"kind": "full", "count": 2},
            structured=RecapStructured(
                summary="Fan likes cosplay elves",
                preferences=["cosplay elf"],
                objections=[],
                purchases=[],
                sensitive_topics=[],
                next_actions=["Offer teaser"],
                recommended_tone="playful"
            ),
            tokens_used=100,
            version="v1",
            updated_at=datetime.now(timezone.utc)
        )
        yield mock


@pytest.fixture
def mock_analytics_audit():
    """Mock des services analytics et audit."""
    with patch("api.services.analytics.events.emit_recap_event") as mock_analytics, \
         patch("api.services.observability.activity.log_recap") as mock_audit:
        mock_analytics.return_value = "event_id"
        mock_audit.return_value = "log_id"
        yield mock_analytics, mock_audit


@pytest.mark.asyncio
async def test_recap_generate_and_get(mock_recap_service, mock_analytics_audit):
    """Test de génération et récupération de recap."""
    client = TestClient(app)
    
    # 1. Générer un recap
    payload = {
        "org_id": "org_demo",
        "conversation_id": "conv_42",
        "kind": "full",
        "max_messages": 50
    }
    
    response = client.post("/api/recap/generate", json=payload)
    
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["structured"]["summary"]
    assert "preferences" in body["structured"]
    assert body["conversation_id"] == "conv_42"
    
    # 2. Récupérer le recap (nécessite de mocker la DB aussi)
    with patch("api.routes.recap.get_core_db") as mock_db:
        from unittest.mock import MagicMock
        mock_db_instance = MagicMock()
        
        # Mock du find_one
        mock_collection = MagicMock()
        mock_db_instance.__getitem__.return_value = mock_collection
        
        recap_doc = {
            "org_id": "org_demo",
            "conversation_id": "conv_42",
            "muse_id": "muse_1",
            "user_id": "user_1",
            "last_message_ts": datetime.now(timezone.utc),
            "window": {"kind": "full", "count": 2},
            "structured": {
                "summary": "Fan likes cosplay elves",
                "preferences": ["cosplay elf"],
                "objections": [],
                "purchases": [],
                "sensitive_topics": [],
                "next_actions": ["Offer teaser"],
                "recommended_tone": "playful"
            },
            "tokens_used": 100,
            "version": "v1",
            "updated_at": datetime.now(timezone.utc)
        }
        
        async def async_find_one(query):
            return recap_doc
        
        mock_collection.find_one = AsyncMock(side_effect=async_find_one)
        mock_db.return_value = mock_db_instance
        
        response2 = client.get("/api/recap/get", params={
            "org_id": "org_demo",
            "conversation_id": "conv_42"
        })
        
        assert response2.status_code == 200
        assert response2.json()["conversation_id"] == "conv_42"


@pytest.mark.asyncio
async def test_recap_list(mock_recap_service):
    """Test de liste des recaps."""
    client = TestClient(app)
    
    with patch("api.routes.recap.get_core_db") as mock_db:
        from unittest.mock import MagicMock
        mock_db_instance = MagicMock()
        mock_collection = MagicMock()
        mock_db_instance.__getitem__.return_value = mock_collection
        
        recap_items = [
            {
                "_id": "id1",
                "org_id": "org_demo",
                "conversation_id": "conv_1",
                "muse_id": "muse_1",
                "updated_at": datetime.now(timezone.utc),
                "last_message_ts": datetime.now(timezone.utc),
                "window": {"kind": "full"}
            },
            {
                "_id": "id2",
                "org_id": "org_demo",
                "conversation_id": "conv_2",
                "muse_id": "muse_1",
                "updated_at": datetime.now(timezone.utc),
                "last_message_ts": datetime.now(timezone.utc),
                "window": {"kind": "delta"}
            }
        ]
        
        async def async_find(query):
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = mock_cursor
            mock_cursor.skip.return_value = mock_cursor
            mock_cursor.limit.return_value = mock_cursor
            
            async def async_to_list(length):
                return recap_items
            
            mock_cursor.to_list = async_to_list
            return mock_cursor
        
        mock_collection.find = AsyncMock(side_effect=async_find)
        mock_db.return_value = mock_db_instance
        
        response = client.get("/api/recap/list", params={
            "org_id": "org_demo",
            "muse_id": "muse_1",
            "page": 1,
            "page_size": 20
        })
        
        assert response.status_code == 200
        body = response.json()
        assert "items" in body
        assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_recap_feature_disabled():
    """Test que le recap retourne 403 si le feature est désactivé."""
    original_value = settings.feature_convo_recap_enabled
    settings.feature_convo_recap_enabled = False
    
    try:
        client = TestClient(app)
        
        payload = {
            "org_id": "org_demo",
            "conversation_id": "conv_42",
            "kind": "full"
        }
        
        response = client.post("/api/recap/generate", json=payload)
        
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()
        
    finally:
        settings.feature_convo_recap_enabled = original_value


@pytest.mark.asyncio
async def test_recap_get_not_found():
    """Test que la récupération retourne 404 si le recap n'existe pas."""
    client = TestClient(app)
    
    with patch("api.routes.recap.get_core_db") as mock_db:
        from unittest.mock import MagicMock
        mock_db_instance = MagicMock()
        mock_collection = MagicMock()
        mock_db_instance.__getitem__.return_value = mock_collection
        
        async def async_find_one(query):
            return None
        
        mock_collection.find_one = AsyncMock(side_effect=async_find_one)
        mock_db.return_value = mock_db_instance
        
        response = client.get("/api/recap/get", params={
            "org_id": "org_demo",
            "conversation_id": "nonexistent"
        })
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_recap_missing_required_fields():
    """Test que la génération rejette les requêtes incomplètes."""
    client = TestClient(app)
    
    # Manque conversation_id
    payload = {
        "org_id": "org_demo"
    }
    
    response = client.post("/api/recap/generate", json=payload)
    
    assert response.status_code == 422  # Validation error




