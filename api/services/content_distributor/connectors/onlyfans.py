import asyncio
import httpx
import os
import json
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from api.services.content_distributor.logger import logger, log_step, log_platform_event

# Variables d'environnement pour OnlyFans
ONLYFANS_API_KEY = os.getenv("ONLYFANS_API_KEY")
ONLYFANS_API_SECRET = os.getenv("ONLYFANS_API_SECRET")
ONLYFANS_BASE_URL = os.getenv("ONLYFANS_BASE_URL", "https://onlyfans.com/api/v1")
ONLYFANS_WEBHOOK_SECRET = os.getenv("ONLYFANS_WEBHOOK_SECRET")

class OnlyFansConnector:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = ONLYFANS_BASE_URL

    def _generate_signature(self, method: str, endpoint: str, timestamp: str, body: str = "") -> str:
        """Génère la signature HMAC pour l'authentification OnlyFans."""
        message = f"{method.upper()}{endpoint}{timestamp}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_headers(self, method: str, endpoint: str, body: str = "") -> Dict[str, str]:
        """Génère les headers d'authentification pour OnlyFans."""
        timestamp = str(int(utcnow().timestamp()))
        signature = self._generate_signature(method, endpoint, timestamp, body)
        
        return {
            "X-API-Key": self.api_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }

    async def create_post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouveau post sur OnlyFans."""
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
                raise Exception(f"Erreur création post OnlyFans: {data}")
            
            return data

    async def upload_media(self, media_url: str, media_type: str = "photo") -> Dict[str, Any]:
        """Upload un média sur OnlyFans."""
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
                raise Exception(f"Erreur upload média OnlyFans: {data}")
            
            return data

    async def get_analytics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Récupère les analytics OnlyFans."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/analytics?start_date={start_date}&end_date={end_date}"
            headers = self._get_headers("GET", endpoint)
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur analytics OnlyFans: {data}")
            
            return data

    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """Vérifie la signature d'un webhook OnlyFans."""
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

@log_step
async def publish_to_onlyfans(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu sur OnlyFans avec gestion avancée.

    :param content: Dictionnaire contenant media_url, caption, price, etc.
    :param model_info: Dictionnaire contenant onlyfans_api_key, onlyfans_api_secret, agency_id, muse_id.
    :return: Résultat de la publication.
    """
    try:
        api_key = model_info.get("onlyfans_api_key") or ONLYFANS_API_KEY
        api_secret = model_info.get("onlyfans_api_secret") or ONLYFANS_API_SECRET
        
        if not api_key or not api_secret:
            raise Exception("Clés API OnlyFans manquantes.")
        
        connector = OnlyFansConnector(api_key, api_secret)
        
        # Extraction des paramètres du contenu
        media_url = content.get("media_url") or content.get("media_urls", [None])[0]
        caption = content.get("caption", content.get("text", ""))
        price = content.get("price", 0)
        is_premium = content.get("is_premium", price > 0)
        tags = content.get("tags", [])
        
        if not media_url:
            raise Exception("URL de média manquante pour OnlyFans.")
        
        # Upload du média
        media_type = "video" if media_url.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')) else "photo"
        media_result = await connector.upload_media(media_url, media_type)
        media_id = media_result.get("media_id")
        
        # Création du post
        post_data = {
            "media_id": media_id,
            "caption": caption,
            "price": price,
            "is_premium": is_premium,
            "tags": tags,
            "scheduled_at": content.get("scheduled_at")
        }
        
        result = await connector.create_post(post_data)
        
        # Enregistrer un log de succès
        await log_platform_event(
            platform="onlyfans",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="success",
            message="Publication OnlyFans réussie",
            metadata={
                "caption": caption,
                "price": price,
                "is_premium": is_premium,
                "media_id": media_id,
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
            platform="onlyfans",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="error",
            message=f"Erreur lors de la publication OnlyFans: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )
        logger.error(f"Erreur publish_to_onlyfans: {e}")
        return {"status": "error", "reason": str(e)}