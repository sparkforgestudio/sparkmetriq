# tests/unit/test_mymfans_integration.py
import pytest
import httpx
import os
from unittest.mock import AsyncMock, patch
from api.services.content_distributor.connectors.mymfans import MYMFansConnector, publish_to_mymfans

# Mock des variables d'environnement pour les tests
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("MYMFANS_API_KEY", "mock_api_key")
    monkeypatch.setenv("MYMFANS_API_SECRET", "mock_api_secret")
    monkeypatch.setenv("MYMFANS_BASE_URL", "https://mock.api.mym.fans/v1")
    monkeypatch.setenv("MYMFANS_WEBHOOK_SECRET", "mock_mymfans_webhook_secret")

@pytest.mark.asyncio
async def test_get_profile_info_success():
    """Test de récupération des informations de profil MYM.fans."""
    connector = MYMFansConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "user_id": "user_123",
        "username": "test_creator",
        "display_name": "Test Creator",
        "email": "test@example.com",
        "is_verified": True,
        "total_earnings": 1500.0,
        "subscriber_count": 250
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        result = await connector.get_profile_info()
        
        assert result == mock_response
        assert result["user_id"] == "user_123"
        assert result["username"] == "test_creator"

@pytest.mark.asyncio
async def test_create_post_success():
    """Test de création d'un post MYM.fans."""
    connector = MYMFansConnector("test_api_key", "test_api_secret")
    
    post_data = {
        "title": "Test Post",
        "description": "Description du test",
        "media_ids": ["media_123", "media_456"],
        "price": 15.0,
        "is_premium": True,
        "tags": ["test", "premium"]
    }
    
    mock_response = {
        "post_id": "post_789",
        "status": "published",
        "created_at": "2024-01-01T12:00:00Z",
        "url": "https://mym.fans/post/post_789"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=httpx.Response(201, json=mock_response)
        )
        
        result = await connector.create_post(post_data)
        
        assert result == mock_response
        assert result["post_id"] == "post_789"
        assert result["status"] == "published"

@pytest.mark.asyncio
async def test_upload_media_success():
    """Test d'upload de média MYM.fans."""
    connector = MYMFansConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "media_id": "media_123",
        "media_url": "https://cdn.mym.fans/media_123.jpg",
        "media_type": "image",
        "file_size": 2048576,
        "upload_status": "completed"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=httpx.Response(201, json=mock_response)
        )
        
        result = await connector.upload_media("https://example.com/image.jpg", "image")
        
        assert result == mock_response
        assert result["media_id"] == "media_123"
        assert result["media_type"] == "image"

@pytest.mark.asyncio
async def test_get_earnings_success():
    """Test de récupération des revenus MYM.fans."""
    connector = MYMFansConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "total_earnings": 2500.0,
        "currency": "EUR",
        "period": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        },
        "breakdown": {
            "subscriptions": 1800.0,
            "posts": 500.0,
            "messages": 200.0
        }
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        result = await connector.get_earnings("2024-01-01", "2024-01-31")
        
        assert result == mock_response
        assert result["total_earnings"] == 2500.0
        assert result["currency"] == "EUR"

@pytest.mark.asyncio
async def test_send_private_message_success():
    """Test d'envoi de message privé MYM.fans."""
    connector = MYMFansConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "message_id": "msg_123",
        "status": "sent",
        "price": 10.0,
        "is_paid": True,
        "created_at": "2024-01-01T12:00:00Z"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=httpx.Response(201, json=mock_response)
        )
        
        result = await connector.send_private_message("user_456", "Message privé", "https://example.com/media.jpg", 10.0)
        
        assert result == mock_response
        assert result["message_id"] == "msg_123"
        assert result["is_paid"] == True

@pytest.mark.asyncio
async def test_publish_to_mymfans_success():
    """Test de publication complète sur MYM.fans."""
    content = {
        "id": "content_123",
        "title": "Test Publication",
        "description": "Description du test",
        "media_urls": ["https://example.com/video.mp4"],
        "price": 20.0,
        "is_premium": True,
        "tags": ["test", "premium", "video"]
    }
    
    model_info = {
        "mymfans_api_key": "test_api_key",
        "mymfans_api_secret": "test_api_secret",
        "agency_id": "agency_123",
        "muse_id": "muse_456"
    }
    
    # Mock des réponses
    upload_response = {"media_id": "media_123"}
    post_response = {"post_id": "post_789", "status": "published"}
    
    with patch("api.services.content_distributor.connectors.mymfans.MYMFansConnector") as mock_connector_class:
        mock_connector = AsyncMock()
        mock_connector_class.return_value = mock_connector
        
        mock_connector.upload_media.return_value = upload_response
        mock_connector.create_post.return_value = post_response
        
        result = await publish_to_mymfans(content, model_info)
        
        assert result["status"] == "success"
        assert result["post_id"] == "post_789"
        assert mock_connector.upload_media.called
        assert mock_connector.create_post.called

@pytest.mark.asyncio
async def test_publish_to_mymfans_missing_credentials():
    """Test de publication MYM.fans avec credentials manquants."""
    content = {
        "id": "content_123",
        "title": "Test Publication"
    }
    
    model_info = {
        "agency_id": "agency_123",
        "muse_id": "muse_456"
        # Pas de credentials MYM.fans
    }
    
    result = await publish_to_mymfans(content, model_info)
    
    assert result["status"] == "error"
    assert "Clés API MYM.fans manquantes" in result["reason"]

def test_verify_webhook_signature_valid():
    """Test de vérification de signature webhook valide."""
    payload = '{"test": "data"}'
    secret = "test_secret"
    
    # Générer une signature valide
    import hmac
    import hashlib
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    result = MYMFansConnector.verify_webhook_signature(payload, expected_signature, secret)
    assert result == True

def test_verify_webhook_signature_invalid():
    """Test de vérification de signature webhook invalide."""
    payload = '{"test": "data"}'
    secret = "test_secret"
    invalid_signature = "invalid_signature"
    
    result = MYMFansConnector.verify_webhook_signature(payload, invalid_signature, secret)
    assert result == False

@pytest.mark.asyncio
async def test_get_analytics_overview_success():
    """Test de récupération des analytics overview MYM.fans."""
    connector = MYMFansConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "total_views": 15000,
        "total_likes": 750,
        "total_comments": 120,
        "total_shares": 45,
        "total_earnings": 3500.0,
        "subscriber_growth": 25,
        "engagement_rate": 8.5,
        "top_posts": [
            {"post_id": "post_1", "views": 5000, "earnings": 500.0},
            {"post_id": "post_2", "views": 3000, "earnings": 300.0}
        ]
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        result = await connector.get_analytics_overview("2024-01-01", "2024-01-31")
        
        assert result == mock_response
        assert result["total_views"] == 15000
        assert result["total_earnings"] == 3500.0
        assert len(result["top_posts"]) == 2

@pytest.mark.asyncio
async def test_create_subscription_plan_success():
    """Test de création d'un plan d'abonnement MYM.fans."""
    connector = MYMFansConnector("test_api_key", "test_api_secret")
    
    plan_data = {
        "name": "Premium Plan",
        "description": "Accès premium au contenu",
        "price": 25.0,
        "currency": "EUR",
        "billing_cycle": "monthly",
        "benefits": ["Accès exclusif", "Messages privés", "Contenu premium"]
    }
    
    mock_response = {
        "plan_id": "plan_123",
        "name": "Premium Plan",
        "price": 25.0,
        "status": "active",
        "created_at": "2024-01-01T12:00:00Z"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=httpx.Response(201, json=mock_response)
        )
        
        result = await connector.create_subscription_plan(plan_data)
        
        assert result == mock_response
        assert result["plan_id"] == "plan_123"
        assert result["price"] == 25.0




