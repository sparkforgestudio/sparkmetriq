# api/services/content_distributor/connectors/whatsapp.py
import httpx
import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

from api.services.content_distributor.logger import logger, log_step, log_platform_event

# Variables d'environnement pour WhatsApp Business
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_BASE_URL = os.getenv("WHATSAPP_BASE_URL", "https://graph.facebook.com/v18.0")
WHATSAPP_WEBHOOK_SECRET = os.getenv("WHATSAPP_WEBHOOK_SECRET")

class WhatsAppConnector:
    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = WHATSAPP_BASE_URL

    def _get_headers(self) -> Dict[str, str]:
        """Génère les headers d'authentification pour WhatsApp."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def send_text_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Envoie un message texte via WhatsApp Business.
        
        :param to: Numéro de téléphone du destinataire (format international).
        :param message: Texte du message.
        :return: Réponse de l'API WhatsApp.
        """
        async with httpx.AsyncClient() as client:
            endpoint = f"/{self.phone_number_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur envoi message WhatsApp: {data}")
            
            return data

    async def send_media_message(self, to: str, media_url: str, media_type: str, caption: str = None) -> Dict[str, Any]:
        """
        Envoie un média (image, vidéo, document) via WhatsApp Business.
        
        :param to: Numéro de téléphone du destinataire.
        :param media_url: URL du média.
        :param media_type: Type de média (image, video, document, audio).
        :param caption: Légende du média (optionnel).
        :return: Réponse de l'API WhatsApp.
        """
        async with httpx.AsyncClient() as client:
            endpoint = f"/{self.phone_number_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": media_type,
                media_type: {
                    "link": media_url
                }
            }
            
            if caption:
                payload[media_type]["caption"] = caption
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur envoi média WhatsApp: {data}")
            
            return data

    async def send_template_message(self, to: str, template_name: str, language_code: str, components: List[Dict] = None) -> Dict[str, Any]:
        """
        Envoie un message template via WhatsApp Business.
        
        :param to: Numéro de téléphone du destinataire.
        :param template_name: Nom du template approuvé.
        :param language_code: Code de langue (ex: "fr", "en").
        :param components: Composants du template (paramètres).
        :return: Réponse de l'API WhatsApp.
        """
        async with httpx.AsyncClient() as client:
            endpoint = f"/{self.phone_number_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur envoi template WhatsApp: {data}")
            
            return data

    async def send_interactive_message(self, to: str, interactive_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie un message interactif (boutons, listes) via WhatsApp Business.
        
        :param to: Numéro de téléphone du destinataire.
        :param interactive_data: Données du message interactif.
        :return: Réponse de l'API WhatsApp.
        """
        async with httpx.AsyncClient() as client:
            endpoint = f"/{self.phone_number_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": interactive_data
            }
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur envoi message interactif WhatsApp: {data}")
            
            return data

    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Récupère le statut d'un message envoyé."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/{self.phone_number_id}/messages/{message_id}"
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers()
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération statut WhatsApp: {data}")
            
            return data

    async def get_phone_number_info(self) -> Dict[str, Any]:
        """Récupère les informations du numéro de téléphone WhatsApp Business."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/{self.phone_number_id}"
            
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers()
            )
            
            data = response.json()
            if response.status_code != 200:
                raise Exception(f"Erreur récupération info numéro WhatsApp: {data}")
            
            return data

    async def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """Marque un message comme lu."""
        async with httpx.AsyncClient() as client:
            endpoint = f"/{self.phone_number_id}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                json=payload
            )
            
            data = response.json()
            if response.status_code not in [200, 201]:
                raise Exception(f"Erreur marquage message lu WhatsApp: {data}")
            
            return data

    @staticmethod
    def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
        """Vérifie la signature d'un webhook WhatsApp."""
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

@log_step
async def publish_to_whatsapp(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu via WhatsApp Business.

    :param content: Dictionnaire contenant to, message, media_url, etc.
    :param model_info: Dictionnaire contenant whatsapp_access_token, whatsapp_phone_number_id, agency_id, muse_id.
    :return: Résultat de la publication.
    """
    try:
        access_token = model_info.get("whatsapp_access_token") or WHATSAPP_ACCESS_TOKEN
        phone_number_id = model_info.get("whatsapp_phone_number_id") or WHATSAPP_PHONE_NUMBER_ID
        
        if not access_token or not phone_number_id:
            raise Exception("Credentials WhatsApp Business manquants.")
        
        connector = WhatsAppConnector(access_token, phone_number_id)
        
        # Extraction des paramètres du contenu
        to = content.get("to")  # Numéro de téléphone du destinataire
        message = content.get("message", content.get("text", ""))
        media_url = content.get("media_url")
        media_type = content.get("media_type", "image")
        template_name = content.get("template_name")
        language_code = content.get("language_code", "fr")
        interactive_data = content.get("interactive_data")
        
        if not to:
            raise Exception("Numéro de téléphone destinataire manquant pour WhatsApp.")
        
        result = None
        
        # Déterminer le type de message à envoyer
        if template_name:
            # Message template
            components = content.get("template_components", [])
            result = await connector.send_template_message(to, template_name, language_code, components)
        elif interactive_data:
            # Message interactif
            result = await connector.send_interactive_message(to, interactive_data)
        elif media_url:
            # Message avec média
            caption = content.get("caption", content.get("description", ""))
            result = await connector.send_media_message(to, media_url, media_type, caption)
        elif message:
            # Message texte simple
            result = await connector.send_text_message(to, message)
        else:
            raise Exception("Aucun contenu valide fourni pour WhatsApp.")
        
        # Enregistrer un log de succès
        await log_platform_event(
            platform="whatsapp",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="success",
            message="Message WhatsApp envoyé avec succès",
            metadata={
                "to": to,
                "message_type": "template" if template_name else ("interactive" if interactive_data else ("media" if media_url else "text")),
                "message_id": result.get("messages", [{}])[0].get("id") if result.get("messages") else None
            }
        )
        
        return {
            "status": "success",
            "platform_response": result,
            "message_id": result.get("messages", [{}])[0].get("id") if result.get("messages") else None
        }

    except Exception as e:
        # En cas d'erreur, enregistrer l'événement
        await log_platform_event(
            platform="whatsapp",
            agency_id=model_info.get("agency_id", ""),
            muse_id=model_info.get("muse_id", ""),
            content_id=content.get("id", ""),
            status="error",
            message=f"Erreur lors de l'envoi WhatsApp: {str(e)}",
            metadata={"error_type": type(e).__name__}
        )
        logger.error(f"Erreur publish_to_whatsapp: {e}")
        return {"status": "error", "reason": str(e)}

async def initialize_whatsapp_connector() -> None:
    """
    Fonction d'initialisation du connecteur WhatsApp.
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("Les variables d'environnement pour WhatsApp ne sont pas toutes définies.")
    else:
        logger.info("Connecteur WhatsApp initialisé avec succès.")



