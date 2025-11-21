# tests/unit/test_manyvids_integration.py
import pytest
import httpx
import os
from unittest.mock import AsyncMock, patch
from api.services.content_distributor.connectors.manyvids import ManyVidsConnector, publish_to_manyvids

# Mock des variables d'environnement pour les tests
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("MANYVIDS_API_KEY", "mock_api_key")
    monkeypatch.setenv("MANYVIDS_API_SECRET", "mock_api_secret")
    monkeypatch.setenv("MANYVIDS_BASE_URL", "https://mock.api.manyvids.com/v1")
    monkeypatch.setenv("MANYVIDS_WEBHOOK_SECRET", "mock_manyvids_webhook_secret")

@pytest.mark.asyncio
async def test_get_profile_info_success():
    """Test de récupération des informations de profil ManyVids."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "user_id": "user_123",
        "username": "test_creator",
        "display_name": "Test Creator",
        "email": "test@example.com",
        "is_verified": True,
        "total_earnings": 5000.0,
        "fan_count": 500,
        "video_count": 25,
        "member_since": "2023-01-01"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        result = await connector.get_profile_info()
        
        assert result == mock_response
        assert result["user_id"] == "user_123"
        assert result["username"] == "test_creator"
        assert result["total_earnings"] == 5000.0

@pytest.mark.asyncio
async def test_upload_video_success():
    """Test d'upload de vidéo ManyVids."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    metadata = {
        "title": "Test Video",
        "description": "Description du test",
        "tags": ["test", "premium"],
        "category": "adult",
        "price": 25.0,
        "duration": 300
    }
    
    mock_response = {
        "video_id": "video_123",
        "upload_status": "completed",
        "processing_status": "ready",
        "video_url": "https://cdn.manyvids.com/video_123.mp4",
        "thumbnail_url": "https://cdn.manyvids.com/thumb_123.jpg",
        "file_size": 104857600,
        "duration": 300
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=httpx.Response(201, json=mock_response)
        )
        
        result = await connector.upload_video("https://example.com/video.mp4", metadata)
        
        assert result == mock_response
        assert result["video_id"] == "video_123"
        assert result["upload_status"] == "completed"

@pytest.mark.asyncio
async def test_create_video_success():
    """Test de création d'une vidéo ManyVids."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    video_data = {
        "title": "Test Video Creation",
        "description": "Description de la vidéo",
        "category": "adult",
        "price": 30.0,
        "tags": ["test", "creation"],
        "is_premium": True
    }
    
    mock_response = {
        "video_id": "video_456",
        "status": "published",
        "created_at": "2024-01-01T12:00:00Z",
        "url": "https://manyvids.com/video/video_456"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=httpx.Response(201, json=mock_response)
        )
        
        result = await connector.create_video(video_data)
        
        assert result == mock_response
        assert result["video_id"] == "video_456"
        assert result["status"] == "published"

@pytest.mark.asyncio
async def test_get_earnings_success():
    """Test de récupération des revenus ManyVids."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "total_earnings": 3500.0,
        "currency": "USD",
        "period": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        },
        "breakdown": {
            "video_sales": 2000.0,
            "custom_videos": 1000.0,
            "tips": 300.0,
            "subscriptions": 200.0
        },
        "payout_status": "pending"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        result = await connector.get_earnings("2024-01-01", "2024-01-31")
        
        assert result == mock_response
        assert result["total_earnings"] == 3500.0
        assert result["currency"] == "USD"

@pytest.mark.asyncio
async def test_create_custom_video_request_success():
    """Test de création d'une demande de vidéo personnalisée."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    request_data = {
        "title": "Custom Video Request",
        "description": "Description de la demande",
        "budget": 100.0,
        "deadline": "2024-02-01",
        "special_requests": "Costume spécifique"
    }
    
    mock_response = {
        "request_id": "req_123",
        "status": "pending",
        "created_at": "2024-01-01T12:00:00Z",
        "estimated_completion": "2024-01-15"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=httpx.Response(201, json=mock_response)
        )
        
        result = await connector.create_custom_video_request(request_data)
        
        assert result == mock_response
        assert result["request_id"] == "req_123"
        assert result["status"] == "pending"

@pytest.mark.asyncio
async def test_send_message_success():
    """Test d'envoi de message ManyVids."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "message_id": "msg_123",
        "status": "sent",
        "price": 15.0,
        "is_paid": True,
        "created_at": "2024-01-01T12:00:00Z"
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=httpx.Response(201, json=mock_response)
        )
        
        result = await connector.send_message("fan_456", "Message privé", "https://example.com/media.jpg", 15.0)
        
        assert result == mock_response
        assert result["message_id"] == "msg_123"
        assert result["is_paid"] == True

@pytest.mark.asyncio
async def test_publish_to_manyvids_success():
    """Test de publication complète sur ManyVids."""
    content = {
        "id": "content_123",
        "title": "Test Video Publication",
        "description": "Description de la vidéo",
        "video_url": "https://example.com/video.mp4",
        "price": 35.0,
        "is_premium": True,
        "tags": ["test", "premium", "video"],
        "category": "adult",
        "duration": 600
    }
    
    model_info = {
        "manyvids_api_key": "test_api_key",
        "manyvids_api_secret": "test_api_secret",
        "agency_id": "agency_123",
        "muse_id": "muse_456"
    }
    
    # Mock des réponses
    upload_response = {
        "video_id": "video_789",
        "upload_status": "completed",
        "processing_status": "ready"
    }
    
    with patch("api.services.content_distributor.connectors.manyvids.ManyVidsConnector") as mock_connector_class:
        mock_connector = AsyncMock()
        mock_connector_class.return_value = mock_connector
        
        mock_connector.upload_video.return_value = upload_response
        
        result = await publish_to_manyvids(content, model_info)
        
        assert result["status"] == "success"
        assert result["video_id"] == "video_789"
        assert mock_connector.upload_video.called

@pytest.mark.asyncio
async def test_publish_to_manyvids_missing_credentials():
    """Test de publication ManyVids avec credentials manquants."""
    content = {
        "id": "content_123",
        "title": "Test Video"
    }
    
    model_info = {
        "agency_id": "agency_123",
        "muse_id": "muse_456"
        # Pas de credentials ManyVids
    }
    
    result = await publish_to_manyvids(content, model_info)
    
    assert result["status"] == "error"
    assert "Clés API ManyVids manquantes" in result["reason"]

@pytest.mark.asyncio
async def test_publish_to_manyvids_missing_video_url():
    """Test de publication ManyVids sans URL de vidéo."""
    content = {
        "id": "content_123",
        "title": "Test Video"
        # Pas d'URL de vidéo
    }
    
    model_info = {
        "manyvids_api_key": "test_api_key",
        "manyvids_api_secret": "test_api_secret",
        "agency_id": "agency_123",
        "muse_id": "muse_456"
    }
    
    result = await publish_to_manyvids(content, model_info)
    
    assert result["status"] == "error"
    assert "URL de vidéo manquante" in result["reason"]

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
    
    result = ManyVidsConnector.verify_webhook_signature(payload, expected_signature, secret)
    assert result == True

def test_verify_webhook_signature_invalid():
    """Test de vérification de signature webhook invalide."""
    payload = '{"test": "data"}'
    secret = "test_secret"
    invalid_signature = "invalid_signature"
    
    result = ManyVidsConnector.verify_webhook_signature(payload, invalid_signature, secret)
    assert result == False

@pytest.mark.asyncio
async def test_get_analytics_overview_success():
    """Test de récupération des analytics overview ManyVids."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "total_views": 25000,
        "total_likes": 1200,
        "total_purchases": 150,
        "total_earnings": 4500.0,
        "fan_growth": 50,
        "engagement_rate": 12.5,
        "top_videos": [
            {"video_id": "video_1", "views": 8000, "earnings": 800.0},
            {"video_id": "video_2", "views": 5000, "earnings": 600.0}
        ],
        "custom_video_requests": 25,
        "message_count": 200
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        result = await connector.get_analytics_overview("2024-01-01", "2024-01-31")
        
        assert result == mock_response
        assert result["total_views"] == 25000
        assert result["total_earnings"] == 4500.0
        assert len(result["top_videos"]) == 2

@pytest.mark.asyncio
async def test_get_categories_success():
    """Test de récupération des catégories ManyVids."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "categories": [
            {"id": "adult", "name": "Adult", "description": "Contenu adulte"},
            {"id": "fetish", "name": "Fetish", "description": "Contenu fétichiste"},
            {"id": "cosplay", "name": "Cosplay", "description": "Contenu cosplay"},
            {"id": "dance", "name": "Dance", "description": "Contenu de danse"}
        ]
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        result = await connector.get_categories()
        
        assert result == mock_response
        assert len(result["categories"]) == 4
        assert result["categories"][0]["id"] == "adult"

@pytest.mark.asyncio
async def test_get_trending_tags_success():
    """Test de récupération des tags tendance ManyVids."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "trending_tags": [
            {"tag": "premium", "usage_count": 1500, "trend_score": 95},
            {"tag": "exclusive", "usage_count": 1200, "trend_score": 88},
            {"tag": "custom", "usage_count": 900, "trend_score": 82},
            {"tag": "hd", "usage_count": 800, "trend_score": 75}
        ]
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        result = await connector.get_trending_tags()
        
        assert result == mock_response
        assert len(result["trending_tags"]) == 4
        assert result["trending_tags"][0]["tag"] == "premium"
        assert result["trending_tags"][0]["trend_score"] == 95

@pytest.mark.asyncio
async def test_get_fans_success():
    """Test de récupération des fans ManyVids."""
    connector = ManyVidsConnector("test_api_key", "test_api_secret")
    
    mock_response = {
        "fans": [
            {
                "fan_id": "fan_1",
                "username": "fan_user_1",
                "subscription_status": "active",
                "total_spent": 150.0,
                "last_activity": "2024-01-15T10:30:00Z"
            },
            {
                "fan_id": "fan_2",
                "username": "fan_user_2",
                "subscription_status": "inactive",
                "total_spent": 75.0,
                "last_activity": "2024-01-10T15:45:00Z"
            }
        ],
        "total_count": 2
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=httpx.Response(200, json=mock_response)
        )
        
        result = await connector.get_fans(limit=50)
        
        assert result == mock_response
        assert len(result["fans"]) == 2
        assert result["fans"][0]["fan_id"] == "fan_1"
        assert result["fans"][0]["subscription_status"] == "active"



