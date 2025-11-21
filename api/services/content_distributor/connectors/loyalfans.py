# api/services/content_distributor/connectors/loyalfans.py
import httpx
import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from api.services.content_distributor.logger import logger, log_step, log_platform_event

# Variables d'environnement pour LoyalFans
LOYALFANS_API_KEY = os.getenv("LOYALFANS_API_KEY")
LOYALFANS_API_SECRET = os.getenv("LOYALFANS_API_SECRET")
LOYALFANS_BASE_URL = os.getenv("LOYALFANS_BASE_URL", "https://api.loyalfans.com/v1")
LOYALFANS_WEBHOOK_SECRET = os.getenv("LOYALFANS_WEBHOOK_SECRET")

class LoyalFansConnector:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = LOYALFANS_BASE_URL

    def _generate_signature(self, method: str, endpoint: str, timestamp: str, body: str = "") -> str:
        """Génère la signature HMAC pour l'authentification LoyalFans."""
        message = f"{method.upper()}{endpoint}{timestamp}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_headers(self, method: str, endpoint: str, body: str = "") -> Dict[str, str]:
        """Génère les headers d'authentification pour LoyalFans."""
        timestamp = str(int(utcnow().timestamp()))
        signature = self._generate_signature(method, endpoint, timestamp, body)
        
        return {
            "X-API-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }

    async def get_profile_info(self) -> Dict[str, Any]:
        """Récupère les informations du profil LoyalFans."""
        async with httpx.AsyncClient() as client:
            endpoint = "/profile"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération profil LoyalFans: {data}")
            
            return data

    async def create_post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau post sur LoyalFans.
        
        :param content: Dictionnaire contenant title, description, media_urls, price, etc.
        :return: Réponse de l'API LoyalFans.
        """
        async with httpx.AsyncClient() as client:
            endpoint = "/posts"
            body = json.dumps(content)
            headers = self._get_headers("POST", endpoint, body)
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                content=body
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur création post LoyalFans: {data}")
            
            return data

    async def upload_media(self, media_url: str, media_type: str = "image") -> Dict[str, Any]:
        """
        Upload un média sur LoyalFans.
        
        :param media_url: URL du média à uploader.
        :param media_type: Type de média (image, video).
        :return: Réponse de l'API LoyalFans.
        """
        async with httpx.AsyncClient() as client:
            endpoint = "/media/upload"
            payload = {
                "media_url": media_url,
                "media_type": media_type
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
                raise Exception(f"Erreur upload média LoyalFans: {data}")
            
            return data

    async def get_posts(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Récupère la liste des posts LoyalFans."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/posts?limit={limit}&offset={offset}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération posts LoyalFans: {data}")
            
            return data

    async def get_post_analytics(self, post_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Récupère les analytics d'un post LoyalFans."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/posts/{post_id}/analytics"
            params = f"?start_date={start_date}&end_date={end_date}"
            full_endpoint = endpoint + params
            headers = self._get_headers("GET", full_endpoint)
            
            response = await client.get(
                f"{self.base_url}{full_endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur analytics post LoyalFans: {data}")
            
            return data

    async def get_earnings(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Récupère les revenus LoyalFans pour une période."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/earnings?start_date={start_date}&end_date={end_date}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération revenus LoyalFans: {data}")
            
            return data

    async def get_subscribers(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Récupère la liste des abonnés."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/subscribers?limit={limit}&offset={offset}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération abonnés LoyalFans: {data}")
            
            return data

    async def create_subscription_tier(self, tier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouveau tier d'abonnement."""
        async with httpx.AsyncClient() as client:
            endpoint = "/subscription-tiers"
            body = json.dumps(tier_data)
            headers = self._get_headers("POST", endpoint, body)
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                content=body
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur création tier LoyalFans: {data}")
            
            return data

    async def send_message(self, user_id: str, message: str, media_url: str = None) -> Dict[str, Any]:
        """Envoie un message privé à un utilisateur."""
        async with httpx.AsyncClient() as client:
            endpoint = "/messages"
            payload = {
                "user_id": user_id,
                "message": message,
                "media_url": media_url
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
                raise Exception(f"Erreur envoi message LoyalFans: {data}")
            
            return data

    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """Vérifie la signature d'un webhook LoyalFans."""
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

@log_step
async def publish_to_loyalfans(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu sur LoyalFans.

    :param content: Dictionnaire contenant title, description, media_urls, price, etc.
    :param model_info: Dictionnaire contenant loyalfans_api_key, loyalfans_api_secret, agency_id, muse_id.
    :return: Résultat de la publication.
    """
    try:
        api_key = model_info.get("loyalfans_api_key") or LOYALFANS_API_KEY
        api_secret = model_info.get("loyalfans_api_secret") or LOYALFANS_API_SECRET
        
        if not api_key or not api_secret:
            raise Exception("Clés API LoyalFans manquantes.")
        
        connector = LoyalFansConnector(api_key, api_secret)
        
        # Extraction des paramètres du contenu
        title = content.get("title", content.get("text", ""))
        description = content.get("description", content.get("caption", ""))
        media_urls = content.get("media_urls", [])
        price = content.get("price", 0)
        is_premium = content.get("is_premium", price > 0)
        tags = content.get("tags", [])
        category = content.get("category", "general")
        tier_id = content.get("tier_id")
        
        # Upload des médias si nécessaire
        uploaded_media = []
        for media_url in media_urls:
            try:
                media_type = "video" if media_url.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')) else "image"
                media_result = await connector.upload_media(media_url, media_type)
                uploaded_media.append(media_result.get("media_id"))
            except Exception as e:
                logger.warning(f"Erreur upload média LoyalFans {media_url}: {e}")
                # Continuer avec les autres médias
        
        # Création du post
        post_data = {
            "title": title,
            "description": description,
            "media_ids": uploaded_media,
            "price": price,
            "is_premium": is_premium,
            "tags": tags,
            "category": category,
            "tier_id": tier_id,
            "scheduled_at": content.get("scheduled_at")
        }
        
        result = await connector.create_post(post_data)
        
        # Enregistrer un log de succès
        await log_platform_event(
            platform="loyalfans",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="success",
            message="Publication LoyalFans réussie",
            metadata={
                "title": title,
                "price": price,
                "is_premium": is_premium,
                "media_count": len(uploaded_media),
                "tier_id": tier_id,
                "post_id": result.get("post_id")
            }
        )
        
        return {
            "status": "success",
            "platform_response": result,
            "post_id": result.get("post_id")
        }

    except Exception as e:
        # En cas d'erreur, enregistrer l'événement
        await log_platform_event(
            platform="loyalfans",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="error",
            message=f"Erreur lors de la publication LoyalFans: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )
        logger.error(f"Erreur publish_to_loyalfans: {e}")
        return {"status": "error", "reason": str(e)}

async def initialize_loyalfans_connector() -> None:
    """
    Fonction d'initialisation du connecteur LoyalFans.
    """
    if not LOYALFANS_API_KEY or not LOYALFANS_API_SECRET:
        logger.warning("Les variables d'environnement pour LoyalFans ne sont pas toutes définies.")
    else:
        logger.info("Connecteur LoyalFans initialisé avec succès.")



