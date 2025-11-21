# tests/unit/test_tiktok_integration.py
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from api.services.content_distributor.connectors.tiktok import TikTokConnector, publish_to_tiktok

class TestTikTokConnector:
    """Tests pour le connecteur TikTok."""
    
    @pytest.fixture
    def connector(self):
        return TikTokConnector("test_access_token", "test_refresh_token")
    
    @pytest.fixture
    def mock_content(self):
        return {
            "video_url": "https://example.com/video.mp4",
            "title": "Test Video",
            "description": "Test Description",
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False
        }
    
    @pytest.fixture
    def mock_model_info(self):
        return {
            "tiktok_access_token": "test_access_token",
            "tiktok_refresh_token": "test_refresh_token",
            "agency_id": "test_agency",
            "muse_id": "test_muse"
        }

    @pytest.mark.asyncio
    async def test_upload_video_success(self, connector, mock_content):
        """Test de l'upload de vidéo avec succès."""
        mock_init_response = {
            "data": {"publish_id": "test_publish_id"},
            "error": {"code": "ok"}
        }
        mock_publish_response = {
            "data": {"post_id": "test_post_id"},
            "error": {"code": "ok"}
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = [
                MagicMock(json=lambda: mock_init_response),
                MagicMock(json=lambda: mock_publish_response)
            ]
            
            result = await connector.upload_video(
                video_url=mock_content["video_url"],
                title=mock_content["title"],
                description=mock_content["description"]
            )
            
            assert result == mock_publish_response

    @pytest.mark.asyncio
    async def test_upload_video_init_error(self, connector, mock_content):
        """Test de l'upload de vidéo avec erreur d'initialisation."""
        mock_error_response = {
            "error": {"code": "error", "message": "Initialization failed"}
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = MagicMock(
                json=lambda: mock_error_response
            )
            
            with pytest.raises(Exception, match="Erreur lors de l'initialisation"):
                await connector.upload_video(
                    video_url=mock_content["video_url"],
                    title=mock_content["title"]
                )

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, connector):
        """Test du rafraîchissement du token avec succès."""
        mock_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = MagicMock(
                json=lambda: mock_response
            )
            
            result = await connector.refresh_access_token()
            
            assert result == mock_response
            assert connector.access_token == "new_access_token"
            assert connector.refresh_token == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_get_user_info_success(self, connector):
        """Test de récupération des informations utilisateur."""
        mock_response = {
            "data": {
                "user": {
                    "open_id": "test_user_id",
                    "union_id": "test_union_id",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "display_name": "Test User"
                }
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = MagicMock(
                json=lambda: mock_response
            )
            
            result = await connector.get_user_info()
            
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
        
        result = TikTokConnector.verify_webhook_signature(payload, expected_signature, secret)
        assert result is True

    def test_verify_webhook_signature_invalid(self):
        """Test de vérification de signature webhook invalide."""
        payload = '{"test": "data"}'
        secret = "test_secret"
        invalid_signature = "invalid_signature"
        
        result = TikTokConnector.verify_webhook_signature(payload, invalid_signature, secret)
        assert result is False

class TestPublishToTikTok:
    """Tests pour la fonction publish_to_tiktok."""
    
    @pytest.fixture
    def mock_content(self):
        return {
            "id": "test_content_id",
            "video_url": "https://example.com/video.mp4",
            "title": "Test Video",
            "description": "Test Description"
        }
    
    @pytest.fixture
    def mock_model_info(self):
        return {
            "tiktok_access_token": "test_access_token",
            "tiktok_refresh_token": "test_refresh_token",
            "agency_id": "test_agency",
            "muse_id": "test_muse"
        }

    @pytest.mark.asyncio
    async def test_publish_success(self, mock_content, mock_model_info):
        """Test de publication avec succès."""
        mock_upload_result = {
            "data": {"publish_id": "test_publish_id"},
            "error": {"code": "ok"}
        }
        
        with patch('api.services.content_distributor.connectors.tiktok.TikTokConnector') as mock_connector_class:
            mock_connector = AsyncMock()
            mock_connector.upload_video.return_value = mock_upload_result
            mock_connector_class.return_value = mock_connector
            
            with patch('api.services.content_distributor.connectors.tiktok.log_platform_event') as mock_log:
                result = await publish_to_tiktok(mock_content, mock_model_info)
                
                assert result["status"] == "success"
                assert result["publish_id"] == "test_publish_id"
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_missing_token(self, mock_content):
        """Test de publication avec token manquant."""
        mock_model_info = {
            "agency_id": "test_agency",
            "muse_id": "test_muse"
        }
        
        with patch('api.services.content_distributor.connectors.tiktok.log_platform_event') as mock_log:
            result = await publish_to_tiktok(mock_content, mock_model_info)
            
            assert result["status"] == "error"
            assert "Access token manquant" in result["reason"]
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_missing_video_url(self, mock_model_info):
        """Test de publication avec URL de vidéo manquante."""
        mock_content = {
            "id": "test_content_id",
            "title": "Test Video"
        }
        
        with patch('api.services.content_distributor.connectors.tiktok.log_platform_event') as mock_log:
            result = await publish_to_tiktok(mock_content, mock_model_info)
            
            assert result["status"] == "error"
            assert "URL de vidéo manquante" in result["reason"]
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_token_refresh_success(self, mock_content, mock_model_info):
        """Test de publication avec rafraîchissement de token."""
        # Premier appel échoue avec token expiré
        mock_upload_error = Exception("unauthorized token")
        mock_refresh_result = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token"
        }
        mock_upload_success = {
            "data": {"publish_id": "test_publish_id"},
            "error": {"code": "ok"}
        }
        
        with patch('api.services.content_distributor.connectors.tiktok.TikTokConnector') as mock_connector_class:
            mock_connector = AsyncMock()
            mock_connector.upload_video.side_effect = [mock_upload_error, mock_upload_success]
            mock_connector.refresh_access_token.return_value = mock_refresh_result
            mock_connector_class.return_value = mock_connector
            
            with patch('api.services.content_distributor.connectors.tiktok.log_platform_event') as mock_log:
                result = await publish_to_tiktok(mock_content, mock_model_info)
                
                assert result["status"] == "success"
                assert result["publish_id"] == "test_publish_id"
                mock_connector.refresh_access_token.assert_called_once()
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_general_error(self, mock_content, mock_model_info):
        """Test de publication avec erreur générale."""
        mock_upload_error = Exception("General error")
        
        with patch('api.services.content_distributor.connectors.tiktok.TikTokConnector') as mock_connector_class:
            mock_connector = AsyncMock()
            mock_connector.upload_video.side_effect = mock_upload_error
            mock_connector_class.return_value = mock_connector
            
            with patch('api.services.content_distributor.connectors.tiktok.log_platform_event') as mock_log:
                result = await publish_to_tiktok(mock_content, mock_model_info)
                
                assert result["status"] == "error"
                assert "General error" in result["reason"]
                mock_log.assert_called_once()



