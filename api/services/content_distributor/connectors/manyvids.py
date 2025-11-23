# api/services/content_distributor/connectors/manyvids.py
import httpx
import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from api.services.content_distributor.logger import logger, log_step, log_platform_event

# Variables d'environnement pour ManyVids
MANYVIDS_API_KEY = os.getenv("MANYVIDS_API_KEY")
MANYVIDS_API_SECRET = os.getenv("MANYVIDS_API_SECRET")
MANYVIDS_BASE_URL = os.getenv("MANYVIDS_BASE_URL", "https://api.manyvids.com/v1")
MANYVIDS_WEBHOOK_SECRET = os.getenv("MANYVIDS_WEBHOOK_SECRET")

class ManyVidsConnector:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = MANYVIDS_BASE_URL

    def _generate_signature(self, method: str, endpoint: str, timestamp: str, body: str = "") -> str:
        """Génère la signature HMAC pour l'authentification ManyVids."""
        message = f"{method.upper()}{endpoint}{timestamp}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_headers(self, method: str, endpoint: str, body: str = "") -> Dict[str, str]:
        """Génère les headers d'authentification pour ManyVids."""
        timestamp = str(int(utcnow().timestamp()))
        signature = self._generate_signature(method, endpoint, timestamp, body)
        
        return {
            "X-API-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json",
            "User-Agent": "MuseMgmt-Platform/1.0",
            "Accept": "application/json"
        }

    async def get_profile_info(self) -> Dict[str, Any]:
        """Récupère les informations du profil ManyVids."""
        async with httpx.AsyncClient() as client:
            endpoint = "/profile"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération profil ManyVids: {data}")
            
            return data

    async def create_video(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle vidéo sur ManyVids.
        
        :param content: Dictionnaire contenant title, description, video_url, price, etc.
        :return: Réponse de l'API ManyVids.
        """
        async with httpx.AsyncClient() as client:
            endpoint = "/videos"
            body = json.dumps(content)
            headers = self._get_headers("POST", endpoint, body)
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                content=body
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur création vidéo ManyVids: {data}")
            
            return data

    async def upload_video(self, video_url: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload une vidéo sur ManyVids.
        
        :param video_url: URL de la vidéo à uploader.
        :param metadata: Métadonnées de la vidéo.
        :return: Réponse de l'API ManyVids.
        """
        async with httpx.AsyncClient() as client:
            endpoint = "/videos/upload"
            payload = {
                "video_url": video_url,
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "tags": metadata.get("tags", []),
                "category": metadata.get("category", "general"),
                "price": metadata.get("price", 0),
                "is_premium": metadata.get("is_premium", False),
                "duration": metadata.get("duration", 0),
                "thumbnail_url": metadata.get("thumbnail_url")
            }
            body = json.dumps(payload)
            headers = self._get_headers("POST", endpoint, body)
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                content=body
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur upload vidéo ManyVids: {data}")
            
            return data

    async def get_videos(self, limit: int = 20, offset: int = 0, status: str = "published") -> Dict[str, Any]:
        """Récupère la liste des vidéos ManyVids."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/videos?limit={limit}&offset={offset}&status={status}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération vidéos ManyVids: {data}")
            
            return data

    async def get_video_analytics(self, video_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Récupère les analytics d'une vidéo ManyVids."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/videos/{video_id}/analytics"
            params = f"?start_date={start_date}&end_date={end_date}"
            full_endpoint = endpoint + params
            headers = self._get_headers("GET", full_endpoint)
            
            response = await client.get(
                f"{self.base_url}{full_endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur analytics vidéo ManyVids: {data}")
            
            return data

    async def get_earnings(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Récupère les revenus ManyVids pour une période."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/earnings?start_date={start_date}&end_date={end_date}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération revenus ManyVids: {data}")
            
            return data

    async def get_fans(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Récupère la liste des fans."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/fans?limit={limit}&offset={offset}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération fans ManyVids: {data}")
            
            return data

    async def create_custom_video_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une demande de vidéo personnalisée."""
        async with httpx.AsyncClient() as client:
            endpoint = "/custom-videos/requests"
            body = json.dumps(request_data)
            headers = self._get_headers("POST", endpoint, body)
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                content=body
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur création demande vidéo personnalisée ManyVids: {data}")
            
            return data

    async def get_custom_video_requests(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Récupère les demandes de vidéos personnalisées."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/custom-videos/requests?limit={limit}&offset={offset}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération demandes vidéos personnalisées ManyVids: {data}")
            
            return data

    async def send_message(self, fan_id: str, message: str, media_url: str = None, price: float = 0) -> Dict[str, Any]:
        """Envoie un message à un fan."""
        async with httpx.AsyncClient() as client:
            endpoint = "/messages"
            payload = {
                "fan_id": fan_id,
                "message": message,
                "media_url": media_url,
                "price": price,
                "is_paid": price > 0
            }
            body = json.dumps(payload)
            headers = self._get_headers("POST", endpoint, body)
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                content=body
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur envoi message ManyVids: {data}")
            
            return data

    async def get_messages(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Récupère la liste des messages."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/messages?limit={limit}&offset={offset}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération messages ManyVids: {data}")
            
            return data

    async def get_analytics_overview(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Récupère un aperçu des analytics ManyVids."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/analytics/overview?start_date={start_date}&end_date={end_date}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur analytics overview ManyVids: {data}")
            
            return data

    async def update_video(self, video_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour une vidéo existante."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/videos/{video_id}"
            body = json.dumps(update_data)
            headers = self._get_headers("PUT", endpoint, body)
            
            response = await client.put(
                f"{self.base_url}{endpoint}",
                headers=headers,
                content=body
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur mise à jour vidéo ManyVids: {data}")
            
            return data

    async def delete_video(self, video_id: str) -> Dict[str, Any]:
        """Supprime une vidéo."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/videos/{video_id}"
            headers = self._get_headers("DELETE", endpoint)
            
            response = await client.delete(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code not in [200, 204]:
                raise Exception(f"Erreur suppression vidéo ManyVids: {data}")
            
            return data

    async def get_categories(self) -> Dict[str, Any]:
        """Récupère la liste des catégories disponibles."""
        async with httpx.AsyncClient() as client:
            endpoint = "/categories"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération catégories ManyVids: {data}")
            
            return data

    async def get_trending_tags(self) -> Dict[str, Any]:
        """Récupère les tags tendance."""
        async with httpx.AsyncClient() as client:
            endpoint = "/trending/tags"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération tags tendance ManyVids: {data}")
            
            return data

    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """Vérifie la signature d'un webhook ManyVids."""
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

@log_step
async def publish_to_manyvids(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu sur ManyVids.

    :param content: Dictionnaire contenant title, description, video_url, price, etc.
    :param model_info: Dictionnaire contenant manyvids_api_key, manyvids_api_secret, agency_id, muse_id.
    :return: Résultat de la publication.
    """
    try:
        api_key = model_info.get("manyvids_api_key") or MANYVIDS_API_KEY
        api_secret = model_info.get("manyvids_api_secret") or MANYVIDS_API_SECRET
        
        if not api_key or not api_secret:
            raise Exception("Clés API ManyVids manquantes.")
        
        connector = ManyVidsConnector(api_key, api_secret)
        
        # Extraction des paramètres du contenu
        title = content.get("title", content.get("text", ""))
        description = content.get("description", content.get("caption", ""))
        video_url = content.get("video_url") or content.get("media_url")
        price = content.get("price", 0)
        is_premium = content.get("is_premium", price > 0)
        tags = content.get("tags", [])
        category = content.get("category", "general")
        duration = content.get("duration", 0)
        thumbnail_url = content.get("thumbnail_url")
        
        if not video_url:
            raise Exception("URL de vidéo manquante pour ManyVids.")
        
        # Préparer les métadonnées de la vidéo
        video_metadata = {
            "title": title,
            "description": description,
            "tags": tags,
            "category": category,
            "price": price,
            "is_premium": is_premium,
            "duration": duration,
            "thumbnail_url": thumbnail_url
        }
        
        # Upload de la vidéo
        upload_result = await connector.upload_video(video_url, video_metadata)
        video_id = upload_result.get("video_id")
        
        if not video_id:
            raise Exception("Échec de l'upload de la vidéo sur ManyVids.")
        
        # Enregistrer un log de succès
        await log_platform_event(
            platform="manyvids",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="success",
            message="Vidéo ManyVids uploadée avec succès",
            metadata={
                "title": title,
                "price": price,
                "is_premium": is_premium,
                "category": category,
                "duration": duration,
                "video_id": video_id,
                "tags": tags
            }
        )
        
        return {
            "status": "success",
            "platform_response": upload_result,
            "video_id": video_id
        }

    except Exception as e:
        # En cas d'erreur, enregistrer l'événement
        await log_platform_event(
            platform="manyvids",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="error",
            message=f"Erreur lors de l'upload ManyVids: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )
        logger.error(f"Erreur publish_to_manyvids: {e}")
        return {"status": "error", "reason": str(e)}

async def initialize_manyvids_connector() -> None:
    """
    Fonction d'initialisation du connecteur ManyVids.
    """
    if not MANYVIDS_API_KEY or not MANYVIDS_API_SECRET:
        logger.warning("Les variables d'environnement pour ManyVids ne sont pas toutes définies.")
    else:
        logger.info("Connecteur ManyVids initialisé avec succès.")




