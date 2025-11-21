# api/services/content_distributor/connectors/patreon.py
import httpx
import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from api.services.content_distributor.logger import logger, log_step, log_platform_event

# Variables d'environnement pour Patreon
PATREON_CLIENT_ID = os.getenv("PATREON_CLIENT_ID")
PATREON_CLIENT_SECRET = os.getenv("PATREON_CLIENT_SECRET")
PATREON_ACCESS_TOKEN = os.getenv("PATREON_ACCESS_TOKEN")
PATREON_BASE_URL = os.getenv("PATREON_BASE_URL", "https://www.patreon.com/api/oauth2/v2")
PATREON_WEBHOOK_SECRET = os.getenv("PATREON_WEBHOOK_SECRET")

class PatreonConnector:
    def __init__(self, access_token: str, client_id: str = None, client_secret: str = None):
        self.access_token = access_token
        self.client_id = client_id or PATREON_CLIENT_ID
        self.client_secret = client_secret or PATREON_CLIENT_SECRET
        self.base_url = PATREON_BASE_URL

    def _get_headers(self) -> Dict[str, str]:
        """Génère les headers d'authentification pour Patreon."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def get_campaign_info(self) -> Dict[str, Any]:
        """Récupère les informations de la campagne Patreon."""
        async with httpx.AsyncClient() as client:
            endpoint = "/campaigns"
            params = {
                "include": "creator,goals,rewards,creator.access_rules"
            }
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération campagne Patreon: {data}")
            
            return data

    async def get_patrons(self, campaign_id: str, limit: int = 25) -> Dict[str, Any]:
        """Récupère la liste des patrons."""
        async with httpx.AsyncClient() as client:
            endpoint = "/campaigns/{campaign_id}/pledges".format(campaign_id=campaign_id)
            params = {
                "include": "patron,patron.user,reward,reward.patron_benefits",
                "page[count]": limit
            }
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération patrons Patreon: {data}")
            
            return data

    async def get_posts(self, campaign_id: str, limit: int = 25) -> Dict[str, Any]:
        """Récupère les posts de la campagne."""
        async with httpx.AsyncClient() as client:
            endpoint = "/campaigns/{campaign_id}/posts".format(campaign_id=campaign_id)
            params = {
                "include": "user,attachments,user_defined_tags,campaign,access_rules",
                "page[count]": limit
            }
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération posts Patreon: {data}")
            
            return data

    async def create_post(self, campaign_id: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau post sur Patreon.
        
        :param campaign_id: ID de la campagne.
        :param content: Dictionnaire contenant title, content, etc.
        :return: Réponse de l'API Patreon.
        """
        async with httpx.AsyncClient() as client:
            endpoint = "/posts"
            payload = {
                "data": {
                    "type": "post",
                    "attributes": {
                        "title": content.get("title", ""),
                        "content": content.get("content", ""),
                        "is_paid": content.get("is_paid", False),
                        "is_public": content.get("is_public", True),
                        "published_at": content.get("published_at", utcnow().isoformat())
                    },
                    "relationships": {
                        "campaign": {
                            "data": {
                                "type": "campaign",
                                "id": campaign_id
                            }
                        }
                    }
                }
            }
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur création post Patreon: {data}")
            
            return data

    async def get_analytics(self, campaign_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Récupère les analytics de la campagne."""
        async with httpx.AsyncClient() as client:
            endpoint = "/campaigns/{campaign_id}/analytics".format(campaign_id=campaign_id)
            params = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur analytics Patreon: {data}")
            
            return data

    async def get_earnings(self, campaign_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Récupère les revenus de la campagne."""
        async with httpx.AsyncClient() as client:
            endpoint = "/campaigns/{campaign_id}/earnings".format(campaign_id=campaign_id)
            params = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération revenus Patreon: {data}")
            
            return data

    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """Vérifie la signature d'un webhook Patreon."""
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

@log_step
async def publish_to_patreon(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu sur Patreon.

    :param content: Dictionnaire contenant title, content, campaign_id, etc.
    :param model_info: Dictionnaire contenant patreon_access_token, patreon_campaign_id, agency_id, muse_id.
    :return: Résultat de la publication.
    """
    try:
        access_token = model_info.get("patreon_access_token") or PATREON_ACCESS_TOKEN
        campaign_id = model_info.get("patreon_campaign_id")
        
        if not access_token:
            raise Exception("Token d'accès Patreon manquant.")
        if not campaign_id:
            raise Exception("ID de campagne Patreon manquant.")
        
        connector = PatreonConnector(access_token)
        
        # Extraction des paramètres du contenu
        title = content.get("title", content.get("text", ""))
        post_content = content.get("content", content.get("description", ""))
        is_paid = content.get("is_paid", False)
        is_public = content.get("is_public", True)
        published_at = content.get("published_at")
        
        # Création du post
        post_data = {
            "title": title,
            "content": post_content,
            "is_paid": is_paid,
            "is_public": is_public,
            "published_at": published_at
        }
        
        result = await connector.create_post(campaign_id, post_data)
        
        # Enregistrer un log de succès
        await log_platform_event(
            platform="patreon",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="success",
            message="Post Patreon créé avec succès",
            metadata={
                "title": title,
                "is_paid": is_paid,
                "is_public": is_public,
                "campaign_id": campaign_id,
                "post_id": result.get("data", {}).get("id")
            }
        )
        
        return {
            "status": "success",
            "platform_response": result,
            "post_id": result.get("data", {}).get("id")
        }

    except Exception as e:
        # En cas d'erreur, enregistrer l'événement
        await log_platform_event(
            platform="patreon",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="error",
            message=f"Erreur lors de la publication Patreon: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )
        logger.error(f"Erreur publish_to_patreon: {e}")
        return {"status": "error", "reason": str(e)}

async def initialize_patreon_connector() -> None:
    """
    Fonction d'initialisation du connecteur Patreon.
    """
    if not PATREON_ACCESS_TOKEN:
        logger.warning("Les variables d'environnement pour Patreon ne sont pas toutes définies.")
    else:
        logger.info("Connecteur Patreon initialisé avec succès.")



