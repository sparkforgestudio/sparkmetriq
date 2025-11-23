# api/services/content_distributor/connectors/discord.py
import httpx
import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from api.services.content_distributor.logger import logger, log_step, log_platform_event

# Variables d'environnement pour Discord
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_BASE_URL = os.getenv("DISCORD_BASE_URL", "https://discord.com/api/v10")
DISCORD_WEBHOOK_SECRET = os.getenv("DISCORD_WEBHOOK_SECRET")

class DiscordConnector:
    def __init__(self, bot_token: str, client_id: str = None, client_secret: str = None):
        self.bot_token = bot_token
        self.client_id = client_id or DISCORD_CLIENT_ID
        self.client_secret = client_secret or DISCORD_CLIENT_SECRET
        self.base_url = DISCORD_BASE_URL

    def _get_headers(self) -> Dict[str, str]:
        """Génère les headers d'authentification pour Discord."""
        return {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }

    async def send_message(self, channel_id: str, content: str, embeds: List[Dict] = None, components: List[Dict] = None) -> Dict[str, Any]:
        """
        Envoie un message dans un canal Discord.
        
        :param channel_id: ID du canal Discord.
        :param content: Contenu du message.
        :param embeds: Liste des embeds (optionnel).
        :param components: Liste des composants (boutons, menus) (optionnel).
        :return: Réponse de l'API Discord.
        """
        async with httpx.AsyncClient() as client:
            endpoint = f"/channels/{channel_id}/messages"
            payload = {
                "content": content
            }
            
            if embeds:
                payload["embeds"] = embeds
            if components:
                payload["components"] = components
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur envoi message Discord: {data}")
            
            return data

    async def send_embed_message(self, channel_id: str, embed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie un message avec embed dans un canal Discord.
        
        :param channel_id: ID du canal Discord.
        :param embed_data: Données de l'embed.
        :return: Réponse de l'API Discord.
        """
        async with httpx.AsyncClient() as client:
            endpoint = f"/channels/{channel_id}/messages"
            payload = {
                "embeds": [embed_data]
            }
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur envoi embed Discord: {data}")
            
            return data

    async def send_file(self, channel_id: str, file_url: str, filename: str, content: str = None) -> Dict[str, Any]:
        """
        Envoie un fichier dans un canal Discord.
        
        :param channel_id: ID du canal Discord.
        :param file_url: URL du fichier.
        :param filename: Nom du fichier.
        :param content: Contenu du message (optionnel).
        :return: Réponse de l'API Discord.
        """
        async with httpx.AsyncClient() as client:
            # Télécharger le fichier
            file_response = await client.get(file_url)
            file_content = file_response.content
            
            # Préparer les données multipart
            files = {
                'file': (filename, file_content)
            }
            
            data = {}
            if content:
                data['content'] = content
            
            headers = {
                "Authorization": f"Bot {self.bot_token}"
            }
            
            endpoint = f"/channels/{channel_id}/messages"
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                data=data,
                files=files
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur envoi fichier Discord: {data}")
            
            return data

    async def create_thread(self, channel_id: str, name: str, message_id: str = None) -> Dict[str, Any]:
        """
        Crée un thread dans un canal Discord.
        
        :param channel_id: ID du canal Discord.
        :param name: Nom du thread.
        :param message_id: ID du message pour créer un thread (optionnel).
        :return: Réponse de l'API Discord.
        """
        async with httpx.AsyncClient() as client:
            if message_id:
                endpoint = f"/channels/{channel_id}/messages/{message_id}/threads"
            else:
                endpoint = f"/channels/{channel_id}/threads"
            
            payload = {
                "name": name,
                "type": 11  # Type thread public
            }
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur création thread Discord: {data}")
            
            return data

    async def get_guild_info(self, guild_id: str) -> Dict[str, Any]:
        """Récupère les informations d'un serveur Discord."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/guilds/{guild_id}"
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers()
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération serveur Discord: {data}")
            
            return data

    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Récupère les informations d'un canal Discord."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/channels/{channel_id}"
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers()
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération canal Discord: {data}")
            
            return data

    async def get_messages(self, channel_id: str, limit: int = 50) -> Dict[str, Any]:
        """Récupère les messages d'un canal Discord."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/channels/{channel_id}/messages"
            params = {"limit": limit}
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                params=params
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération messages Discord: {data}")
            
            return data

    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """Vérifie la signature d'un webhook Discord."""
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

@log_step
async def publish_to_discord(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu sur Discord.

    :param content: Dictionnaire contenant channel_id, message, embeds, etc.
    :param model_info: Dictionnaire contenant discord_bot_token, agency_id, muse_id.
    :return: Résultat de la publication.
    """
    try:
        bot_token = model_info.get("discord_bot_token") or DISCORD_BOT_TOKEN
        
        if not bot_token:
            raise Exception("Token bot Discord manquant.")
        
        connector = DiscordConnector(bot_token)
        
        # Extraction des paramètres du contenu
        channel_id = content.get("channel_id")
        message = content.get("message", content.get("text", ""))
        embeds = content.get("embeds", [])
        components = content.get("components", [])
        file_url = content.get("file_url")
        filename = content.get("filename")
        thread_name = content.get("thread_name")
        
        if not channel_id:
            raise Exception("ID de canal Discord manquant.")
        
        result = None
        
        # Déterminer le type de contenu à envoyer
        if file_url:
            # Envoi de fichier
            result = await connector.send_file(channel_id, file_url, filename, message)
        elif embeds:
            # Message avec embeds
            if len(embeds) == 1:
                result = await connector.send_embed_message(channel_id, embeds[0])
            else:
                result = await connector.send_message(channel_id, message, embeds, components)
        elif thread_name:
            # Création de thread
            result = await connector.create_thread(channel_id, thread_name)
        else:
            # Message texte simple
            result = await connector.send_message(channel_id, message, embeds, components)
        
        # Enregistrer un log de succès
        await log_platform_event(
            platform="discord",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="success",
            message="Message Discord envoyé avec succès",
            metadata={
                "channel_id": channel_id,
                "message_type": "file" if file_url else ("embed" if embeds else ("thread" if thread_name else "text")),
                "message_id": result.get("id")
            }
        )
        
        return {
            "status": "success",
            "platform_response": result,
            "message_id": result.get("id")
        }

    except Exception as e:
        # En cas d'erreur, enregistrer l'événement
        await log_platform_event(
            platform="discord",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="error",
            message=f"Erreur lors de l'envoi Discord: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )
        logger.error(f"Erreur publish_to_discord: {e}")
        return {"status": "error", "reason": str(e)}

async def initialize_discord_connector() -> None:
    """
    Fonction d'initialisation du connecteur Discord.
    """
    if not DISCORD_BOT_TOKEN:
        logger.warning("Les variables d'environnement pour Discord ne sont pas toutes définies.")
    else:
        logger.info("Connecteur Discord initialisé avec succès.")




