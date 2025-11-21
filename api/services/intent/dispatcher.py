# api/services/intent/dispatcher.py
"""
Dispatcher pour l'envoi de messages vers les plateformes.
Utilise les connecteurs existants ou un mécanisme de routage.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ChannelDispatcher:
    """
    Dispatcher pour envoyer des messages via les canaux.
    
    NOTE: Version simplifiée. Pour production, intégrer avec les connecteurs
    réels (Instagram DM API, Telegram Bot API, etc.).
    """
    
    async def send(self, platform: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie un message via la plateforme spécifiée.
        
        Args:
            platform: Plateforme cible (instagram, tiktok, telegram, etc.)
            payload: Payload avec conversation_id, text, attachments, metadata
            
        Returns:
            Résultat de l'envoi
        """
        conversation_id = payload.get("conversation_id")
        text = payload.get("text", "")
        attachments = payload.get("attachments")
        metadata = payload.get("metadata", {})
        
        logger.info(
            f"Dispatching message to {platform} for conversation_id={conversation_id}, "
            f"text_length={len(text)}"
        )
        
        # TODO: Intégrer avec les connecteurs réels
        # Pour l'instant, on simule l'envoi
        
        # Exemple d'intégration future :
        # if platform == "instagram":
        #     from api.services.content_distributor.connectors.instagram import InstagramConnector
        #     connector = InstagramConnector(...)
        #     result = await connector.send_dm(conversation_id, text, attachments)
        # elif platform == "telegram":
        #     from api.services.content_distributor.connectors.telegram import TelegramConnector
        #     connector = TelegramConnector(...)
        #     result = await connector.send_message(conversation_id, text)
        # etc.
        
        # Simulation pour MVP
        result = {
            "ok": True,
            "platform": platform,
            "conversation_id": conversation_id,
            "message_id": f"msg_{platform}_{conversation_id}",
            "timestamp": None,  # Sera rempli par le vrai connecteur
            "echo": {
                "text_preview": text[:100] if text else "",
                "has_attachments": bool(attachments)
            }
        }
        
        logger.info(
            f"Message dispatched to {platform} for conversation_id={conversation_id} "
            f"(simulated={True})"
        )
        
        return result



