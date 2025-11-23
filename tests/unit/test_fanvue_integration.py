# tests/unit/test_fanvue_integration.py
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from api.services.content_distributor.connectors.fanvue import FanvueConnector, publish_to_fanvue

class TestFanvueConnector:
    """Tests pour le connecteur Fanvue."""
    
    @pytest.fixture
    def connector(self):
        return FanvueConnector("test_api_key", "test_api_secret")
    
    @pytest.fixture
    def mock_content(self):
        return {
            "title": "Test Post",
            "description": "Test Description",
            "media_urls": ["https://example.com/image.jpg"],
            "price": 10.0,
            "is_premium": True,
            "tags": ["test", "content"],
            "category": "general"
        }
    
    @pytest.fixture
    def mock_model_info(self):
        return {
            "fanvue_api_key": "test_api_key",
            "fanvue_api_secret": "test_api_secret",
            "agency_id": "test_agency",
            "muse_id": "test_muse"
        }

    @pytest.mark.asyncio
    async def test_create_post_success(self, connector, mock_content):
        """Test de création de post avec succès."""
        mock_response = {
            "post_id": "test_post_id",
            "status": "created",
            "message": "Post created successfully"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = MagicMock(
                json=lambda: mock_response,
                status_code=201
            )
            
            result = await connector.create_post(mock_content)
            
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_create_post_error(self, connector, mock_content):
        """Test de création de post avec erreur."""
        mock_error_response = {
            "error": "Invalid content",
            "message": "Content validation failed"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = MagicMock(
                json=lambda: mock_error_response,
                status_code=400
            )
            
            with pytest.raises(Exception, match="Erreur création post Fanvue"):
                await connector.create_post(mock_content)

    @pytest.mark.asyncio
    async def test_upload_media_success(self, connector):
        """Test d'upload de média avec succès."""
        mock_response = {
            "media_id": "test_media_id",
            "status": "uploaded",
            "url": "https://fanvue.com/media/test_media_id"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = MagicMock(
                json=lambda: mock_response,
                status_code=201
            )
            
            result = await connector.upload_media("https://example.com/image.jpg", "image")
            
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_posts_success(self, connector):
        """Test de récupération des posts avec succès."""
        mock_response = {
            "posts": [
                {
                    "post_id": "post_1",
                    "title": "Post 1",
                    "created_at": "2024-01-01T00:00:00Z"
                },
                {
                    "post_id": "post_2",
                    "title": "Post 2",
                    "created_at": "2024-01-02T00:00:00Z"
                }
            ],
            "total": 2,
            "has_more": False
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = MagicMock(
                json=lambda: mock_response,
                status_code=200
            )
            
            result = await connector.get_posts(limit=20, offset=0)
            
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_earnings_success(self, connector):
        """Test de récupération des revenus avec succès."""
        mock_response = {
            "total_earnings": 1500.0,
            "subscription_earnings": 1000.0,
            "post_earnings": 400.0,
            "tips_earnings": 100.0,
            "period_start": "2024-01-01",
            "period_end": "2024-01-31",
            "currency": "USD"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = MagicMock(
                json=lambda: mock_response,
                status_code=200
            )
            
            result = await connector.get_earnings("2024-01-01", "2024-01-31")
            
            assert result == mock_response

    def test_verify_webhook_signature_valid(self):
        """Test de vérification de signature webhook valide."""
        payload = '{"test": "data"}'
        secret = "test_secret"
        
        # Génération de la signature attendue
        import hmac
        import hashlib
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = FanvueConnector.verify_webhook_signature(payload, expected_signature, secret)
        assert result is True

    def test_verify_webhook_signature_invalid(self):
        """Test de vérification de signature webhook invalide."""
        payload = '{"test": "data"}'
        secret = "test_secret"
        invalid_signature = "invalid_signature"
        
        result = FanvueConnector.verify_webhook_signature(payload, invalid_signature, secret)
        assert result is False

class TestPublishToFanvue:
    """Tests pour la fonction publish_to_fanvue."""
    
    @pytest.fixture
    def mock_content(self):
        return {
            "id": "test_content_id",
            "title": "Test Post",
            "description": "Test Description",
            "media_urls": ["https://example.com/image.jpg"],
            "price": 10.0,
            "is_premium": True,
            "tags": ["test", "content"]
        }
    
    @pytest.fixture
    def mock_model_info(self):
        return {
            "fanvue_api_key": "test_api_key",
            "fanvue_api_secret": "test_api_secret",
            "agency_id": "test_agency",
            "muse_id": "test_muse"
        }

    @pytest.mark.asyncio
    async def test_publish_success(self, mock_content, mock_model_info):
        """Test de publication avec succès."""
        mock_upload_result = {
            "media_id": "test_media_id",
            "status": "uploaded"
        }
        mock_post_result = {
            "post_id": "test_post_id",
            "status": "created"
        }
        
        with patch('api.services.content_distributor.connectors.fanvue.FanvueConnector') as mock_connector_class:
            mock_connector = AsyncMock()
            mock_connector.upload_media.return_value = mock_upload_result
            mock_connector.create_post.return_value = mock_post_result
            mock_connector_class.return_value = mock_connector
            
            with patch('api.services.content_distributor.connectors.fanvue.log_platform_event') as mock_log:
                result = await publish_to_fanvue(mock_content, mock_model_info)
                
                assert result["status"] == "success"
                assert result["post_id"] == "test_post_id"
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_missing_credentials(self, mock_content):
        """Test de publication avec credentials manquants."""
        mock_model_info = {
            "agency_id": "test_agency",
            "muse_id": "test_muse"
        }
        
        with patch('api.services.content_distributor.connectors.fanvue.log_platform_event') as mock_log:
            result = await publish_to_fanvue(mock_content, mock_model_info)
            
            assert result["status"] == "error"
            assert "Clés API Fanvue manquantes" in result["reason"]
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_missing_media_urls(self, mock_model_info):
        """Test de publication avec URLs de médias manquantes."""
        mock_content = {
            "id": "test_content_id",
            "title": "Test Post",
            "description": "Test Description"
        }
        
        with patch('api.services.content_distributor.connectors.fanvue.log_platform_event') as mock_log:
            result = await publish_to_fanvue(mock_content, mock_model_info)
            
            assert result["status"] == "error"
            assert "URLs des médias manquantes" in result["reason"]
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_upload_error(self, mock_content, mock_model_info):
        """Test de publication avec erreur d'upload."""
        mock_upload_error = Exception("Upload failed")
        
        with patch('api.services.content_distributor.connectors.fanvue.FanvueConnector') as mock_connector_class:
            mock_connector = AsyncMock()
            mock_connector.upload_media.side_effect = mock_upload_error
            mock_connector_class.return_value = mock_connector
            
            with patch('api.services.content_distributor.connectors.fanvue.log_platform_event') as mock_log:
                result = await publish_to_fanvue(mock_content, mock_model_info)
                
                assert result["status"] == "error"
                assert "Upload failed" in result["reason"]
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_create_post_error(self, mock_content, mock_model_info):
        """Test de publication avec erreur de création de post."""
        mock_upload_result = {
            "media_id": "test_media_id",
            "status": "uploaded"
        }
        mock_post_error = Exception("Post creation failed")
        
        with patch('api.services.content_distributor.connectors.fanvue.FanvueConnector') as mock_connector_class:
            mock_connector = AsyncMock()
            mock_connector.upload_media.return_value = mock_upload_result
            mock_connector.create_post.side_effect = mock_post_error
            mock_connector_class.return_value = mock_connector
            
            with patch('api.services.content_distributor.connectors.fanvue.log_platform_event') as mock_log:
                result = await publish_to_fanvue(mock_content, mock_model_info)
                
                assert result["status"] == "error"
                assert "Post creation failed" in result["reason"]
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_multiple_media_urls(self, mock_model_info):
        """Test de publication avec plusieurs URLs de médias."""
        mock_content = {
            "id": "test_content_id",
            "title": "Test Post",
            "description": "Test Description",
            "media_urls": [
                "https://example.com/image1.jpg",
                "https://example.com/video.mp4"
            ],
            "price": 10.0
        }
        
        mock_upload_results = [
            {"media_id": "media_1", "status": "uploaded"},
            {"media_id": "media_2", "status": "uploaded"}
        ]
        mock_post_result = {
            "post_id": "test_post_id",
            "status": "created"
        }
        
        with patch('api.services.content_distributor.connectors.fanvue.FanvueConnector') as mock_connector_class:
            mock_connector = AsyncMock()
            mock_connector.upload_media.side_effect = mock_upload_results
            mock_connector.create_post.return_value = mock_post_result
            mock_connector_class.return_value = mock_connector
            
            with patch('api.services.content_distributor.connectors.fanvue.log_platform_event') as mock_log:
                result = await publish_to_fanvue(mock_content, mock_model_info)
                
                assert result["status"] == "success"
                assert result["post_id"] == "test_post_id"
                assert mock_connector.upload_media.call_count == 2
                mock_log.assert_called_once()




