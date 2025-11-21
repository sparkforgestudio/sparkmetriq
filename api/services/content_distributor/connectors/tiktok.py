import httpx
import os
import json
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

# Import relatif depuis le dossier "connectors" pour accéder au logger.
from api.services.content_distributor.logger import logger, log_step, log_platform_event

# Variables d'environnement pour les identifiants de l'application TikTok
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI")
TIKTOK_WEBHOOK_SECRET = os.getenv("TIKTOK_WEBHOOK_SECRET")


class TikTokConnector:
    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.api_base_url = "https://open.tiktokapis.com/v2"
        self.auth_base_url = "https://www.tiktok.com/v2/auth"

    async def refresh_access_token(self) -> Dict[str, Any]:
        """Rafraîchit le token d'accès TikTok."""
        if not self.refresh_token:
            raise ValueError("Refresh token manquant")
        
        async with httpx.AsyncClient() as client:
            payload = {
                "client_key": TIKTOK_CLIENT_KEY,
                "client_secret": TIKTOK_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }
            
            response = await client.post(
                f"{self.auth_base_url}/token/",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            data = response.json()
            if "error" in data:
                raise Exception(f"Erreur refresh token: {data['error']}")
            
            self.access_token = data["access_token"]
            if "refresh_token" in data:
                self.refresh_token = data["refresh_token"]
            
            return data

    async def get_user_info(self) -> Dict[str, Any]:
        """Récupère les informations du profil utilisateur TikTok."""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await client.get(
                f"{self.api_base_url}/user/info/",
                headers=headers
            )
            
            data = response.json()
            if "error" in data:
                raise Exception(f"Erreur récupération profil: {data['error']}")
            
            return data

    async def upload_video(self, video_url: str, title: str, description: str = "", 
                          privacy_level: str = "PUBLIC_TO_EVERYONE", 
                          disable_duet: bool = False, disable_comment: bool = False,
                          disable_stitch: bool = False, video_cover_timestamp_ms: int = 1000) -> Dict[str, Any]:
        """
        Télécharge une vidéo sur le profil TikTok de l'utilisateur authentifié.
        
        :param video_url: URL de la vidéo à télécharger.
        :param title: Titre de la vidéo.
        :param description: Description de la vidéo.
        :param privacy_level: Niveau de confidentialité (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIEND, SELF_ONLY).
        :param disable_duet: Désactiver les duos.
        :param disable_comment: Désactiver les commentaires.
        :param disable_stitch: Désactiver les stitches.
        :param video_cover_timestamp_ms: Timestamp pour la miniature (en ms).
        :return: Dictionnaire contenant la réponse de l'API TikTok.
        """
        async with httpx.AsyncClient() as client:
            # Étape 1 : Initialiser le téléchargement de la vidéo
            init_endpoint = f"{self.api_base_url}/post/publish/inbox/video/init/"
            init_payload = {
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "video_url": video_url
                },
                "post_info": {
                    "title": title,
                    "description": description,
                    "privacy_level": privacy_level,
                    "disable_duet": disable_duet,
                    "disable_comment": disable_comment,
                    "disable_stitch": disable_stitch,
                    "video_cover_timestamp_ms": video_cover_timestamp_ms
                }
            }
            
            init_headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            init_response = await client.post(init_endpoint, json=init_payload, headers=init_headers)
            init_data = init_response.json()
            
            if "error" in init_data and init_data["error"].get("code") != "ok":
                raise Exception(f"Erreur lors de l'initialisation : {init_data['error'].get('message', init_data)}")

            # Étape 2 : Publier la vidéo
            publish_endpoint = f"{self.api_base_url}/post/publish/inbox/video/publish/"
            publish_payload = {
                "publish_id": init_data["data"]["publish_id"]
            }
            
            publish_response = await client.post(publish_endpoint, json=publish_payload, headers=init_headers)
            publish_data = publish_response.json()
            
            if "error" in publish_data and publish_data["error"].get("code") != "ok":
                raise Exception(f"Erreur lors de la publication : {publish_data['error'].get('message', publish_data)}")
            
            return publish_data

    async def get_video_status(self, publish_id: str) -> Dict[str, Any]:
        """Vérifie le statut de publication d'une vidéo."""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await client.get(
                f"{self.api_base_url}/post/publish/status/fetch/",
                params={"publish_id": publish_id},
                headers=headers
            )
            
            data = response.json()
            if "error" in data:
                raise Exception(f"Erreur statut vidéo: {data['error']}")
            
            return data

    async def get_video_list(self, max_count: int = 20, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Récupère la liste des vidéos publiées."""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            params = {"max_count": max_count}
            if cursor:
                params["cursor"] = cursor
            
            response = await client.get(
                f"{self.api_base_url}/video/list/",
                params=params,
                headers=headers
            )
            
            data = response.json()
            if "error" in data:
                raise Exception(f"Erreur liste vidéos: {data['error']}")
            
            return data

    async def get_video_analytics(self, video_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Récupère les analytics d'une vidéo."""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "video_id": video_id,
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = await client.get(
                f"{self.api_base_url}/video/query/",
                params=params,
                headers=headers
            )
            
            data = response.json()
            if "error" in data:
                raise Exception(f"Erreur analytics vidéo: {data['error']}")
            
            return data

    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """Vérifie la signature d'un webhook TikTok."""
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)


@log_step
async def publish_to_tiktok(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestre la publication d'un contenu sur TikTok avec gestion avancée.

    :param content: Dictionnaire contenant video_url, title, description, privacy_level, etc.
    :param model_info: Dictionnaire contenant tiktok_access_token, refresh_token, agency_id, muse_id.
    :return: Résultat renvoyé par l'API TikTok.
    """
    try:
        access_token = model_info.get("tiktok_access_token")
        refresh_token = model_info.get("tiktok_refresh_token")
        
        if not access_token:
            raise Exception("Access token manquant pour TikTok.")
        
        connector = TikTokConnector(access_token, refresh_token)
        
        # Extraction des paramètres du contenu
        video_url = content.get("video_url") or content.get("media_url")
        title = content.get("title", content.get("text", ""))
        description = content.get("description", content.get("caption", ""))
        privacy_level = content.get("privacy_level", "PUBLIC_TO_EVERYONE")
        disable_duet = content.get("disable_duet", False)
        disable_comment = content.get("disable_comment", False)
        disable_stitch = content.get("disable_stitch", False)
        video_cover_timestamp_ms = content.get("video_cover_timestamp_ms", 1000)
        
        if not video_url:
            raise Exception("URL de vidéo manquante pour TikTok.")
        
        # Tentative de publication
        try:
            result = await connector.upload_video(
                video_url=video_url,
                title=title,
                description=description,
                privacy_level=privacy_level,
                disable_duet=disable_duet,
                disable_comment=disable_comment,
                disable_stitch=disable_stitch,
                video_cover_timestamp_ms=video_cover_timestamp_ms
            )
        except Exception as e:
            # Si erreur d'authentification, essayer de rafraîchir le token
            if "unauthorized" in str(e).lower() or "invalid_token" in str(e).lower():
                if refresh_token:
                    logger.info("Tentative de rafraîchissement du token TikTok...")
                    await connector.refresh_access_token()
                    result = await connector.upload_video(
                        video_url=video_url,
                        title=title,
                        description=description,
                        privacy_level=privacy_level,
                        disable_duet=disable_duet,
                        disable_comment=disable_comment,
                        disable_stitch=disable_stitch,
                        video_cover_timestamp_ms=video_cover_timestamp_ms
                    )
                else:
                    raise Exception(f"Token expiré et aucun refresh token disponible: {e}")
            else:
                raise
        
        # Enregistrer un log de succès
        await log_platform_event(
            platform="tiktok",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="success",
            message="Publication TikTok réussie",
            metadata={
                "title": title,
                "video_url": video_url,
                "privacy_level": privacy_level,
                "publish_id": result.get("data", {}).get("publish_id")
            }
        )
        
        return {
            "status": "success",
            "platform_response": result,
            "publish_id": result.get("data", {}).get("publish_id")
        }

    except Exception as e:
        # En cas d'erreur, enregistrer l'événement
        await log_platform_event(
            platform="tiktok",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="error",
            message=f"Erreur lors de la publication TikTok: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )
        logger.error(f"Erreur publish_to_tiktok: {e}")
        return {"status": "error", "reason": str(e)}


async def initialize_tiktok_connector() -> None:
    """
    Fonction d'initialisation du connecteur TikTok à appeler au démarrage du serveur.
    Vérifie la présence des variables d'environnement nécessaires pour TikTok et enregistre un log d'initialisation.
    """
    if not TIKTOK_CLIENT_KEY or not TIKTOK_CLIENT_SECRET or not TIKTOK_REDIRECT_URI:
        logger.warning("Les variables d'environnement pour TikTok ne sont pas toutes définies.")
    else:
        logger.info("Connecteur TikTok initialisé avec succès.")
