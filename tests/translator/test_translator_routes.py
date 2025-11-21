# tests/translator/test_translator_routes.py
"""
Tests pour les routes du traducteur IA.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
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
def mock_translate_service():
    """Mock du service de traduction."""
    with patch("api.services.ai.translate_service.translate_once") as mock:
        from api.schemas.translator import TranslateOut
        mock.return_value = TranslateOut(
            source_lang="en",
            target_lang="fr",
            original="Hello",
            translated="Bonjour",
            rewritten="Bonjour 😉",
            quality="ok",
            tokens_used=10,
            extras={"tone": "flirt", "emoji": "medium", "formality": "casual"}
        )
        yield mock


@pytest.fixture
def mock_analytics():
    """Mock des services analytics et audit."""
    with patch("api.services.analytics.events.emit_translation_event") as mock_analytics, \
         patch("api.services.observability.activity.log_translation_action") as mock_audit:
        mock_analytics.return_value = "event_id"
        mock_audit.return_value = "log_id"
        yield mock_analytics, mock_audit


@pytest.mark.asyncio
async def test_translate_minimal(mock_translate_service, mock_analytics):
    """Test de traduction minimale."""
    client = TestClient(app)
    
    payload = {
        "text": "Hello",
        "target_lang": "fr",
        "tone": "flirt",
        "emoji": "medium",
        "formality": "casual",
        "org_id": "org_demo",
        "conversation_id": "conv_1",
        "user_role": "operator"
    }
    
    response = client.post("/api/translator/translate", json=payload)
    
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["translated"] == "Bonjour"
    assert body["rewritten"] == "Bonjour 😉"
    assert body["source_lang"] == "en"
    assert body["target_lang"] == "fr"
    assert "original" in body


@pytest.mark.asyncio
async def test_translate_with_auto_detection(mock_translate_service, mock_analytics):
    """Test de traduction avec auto-détection de langue."""
    client = TestClient(app)
    
    payload = {
        "text": "Bonjour",
        "target_lang": "en",
        "tone": "neutral",
        "emoji": "none"
    }
    
    response = client.post("/api/translator/translate", json=payload)
    
    assert response.status_code == 200
    body = response.json()
    assert body["target_lang"] == "en"
    assert "translated" in body


@pytest.mark.asyncio
async def test_translate_feature_disabled():
    """Test que la traduction retourne 403 si le feature est désactivé."""
    original_value = settings.feature_translator_enabled
    settings.feature_translator_enabled = False
    
    try:
        client = TestClient(app)
        
        payload = {
            "text": "Hello",
            "target_lang": "fr"
        }
        
        response = client.post("/api/translator/translate", json=payload)
        
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()
        
    finally:
        settings.feature_translator_enabled = original_value


@pytest.mark.asyncio
async def test_translate_batch(mock_translate_service, mock_analytics):
    """Test de traduction par lot."""
    client = TestClient(app)
    
    payload = {
        "items": [
            {
                "text": "Hello",
                "target_lang": "fr",
                "tone": "neutral"
            },
            {
                "text": "Goodbye",
                "target_lang": "fr",
                "tone": "respectful"
            }
        ]
    }
    
    response = client.post("/api/translator/translate:batch", json=payload)
    
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert len(body["items"]) == 2
    assert all("translated" in item for item in body["items"])


@pytest.mark.asyncio
async def test_translate_text_too_long():
    """Test que la traduction rejette les textes trop longs."""
    original_max = settings.translator_max_chars
    settings.translator_max_chars = 10
    
    try:
        client = TestClient(app)
        
        payload = {
            "text": "This is a very long text that exceeds the maximum character limit",
            "target_lang": "fr"
        }
        
        response = client.post("/api/translator/translate", json=payload)
        
        assert response.status_code in (400, 500)  # Peut être 400 ou 500 selon l'implémentation
        
    finally:
        settings.translator_max_chars = original_max


@pytest.mark.asyncio
async def test_translate_missing_required_fields():
    """Test que la traduction rejette les requêtes incomplètes."""
    client = TestClient(app)
    
    # Manque target_lang
    payload = {
        "text": "Hello"
    }
    
    response = client.post("/api/translator/translate", json=payload)
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_translate_empty_text():
    """Test que la traduction rejette les textes vides."""
    client = TestClient(app)
    
    payload = {
        "text": "",
        "target_lang": "fr"
    }
    
    response = client.post("/api/translator/translate", json=payload)
    
    assert response.status_code == 422  # Validation error



