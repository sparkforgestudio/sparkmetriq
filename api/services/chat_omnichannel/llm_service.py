# api/services/chat_omnichannel/llm_service.py
from __future__ import annotations

import abc
from typing import List, Optional, Dict, Any

from pydantic import BaseModel


class Message(BaseModel):
    """
    Représente un message échangé avec le LLM.
    role : "system" | "user" | "assistant"
    content : texte du message
    """
    role: str
    content: str


class GeneratedResponse(BaseModel):
    """
    Réponse générée par le LLM.
    text  : contenu textuel principal
    usage : métadonnées éventuelles (nb tokens, coût, etc.)
    """
    text: str
    usage: Optional[Dict[str, Any]] = None


class LLMService(abc.ABC):
    """
    Interface abstraite pour un client LLM (DeepSeek, OpenAI, etc.).

    Implémentations concrètes à placer dans des fichiers séparés, par ex. :
      - deepseek_service.py  -> class DeepSeekService(LLMService)
      - openai_service.py    -> class OpenAIService(LLMService)
    """

    def __init__(self, api_key: str, model: str, temperature: float = 0.7):
        """
        :param api_key: Clé API du fournisseur.
        :param model: Nom du modèle à utiliser.
        :param temperature: Paramètre de créativité.
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    @abc.abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tenant_id: Optional[str] = None,
    ) -> GeneratedResponse:
        """
        Envoie le prompt complet au LLM et renvoie la réponse.

        :param messages: Liste de messages {role, content}.
        :param tenant_id: Contexte multi-tenant pour logs/tracing.
        """
        raise NotImplementedError

    async def stream(
        self,
        messages: List[Message],
        tenant_id: Optional[str] = None,
    ):
        """
        Appel streaming si supporté par le fournisseur.
        Génère un itérable de fragments type Message (role="assistant").

        Par défaut : non implémenté, à surcharger si nécessaire.
        """
        raise NotImplementedError("Streaming non implémenté pour ce service")


# IMPORTANT :
# - Ne pas importer DeepSeekService ici pour éviter tout import circulaire.
# - Les services concrets doivent être définis dans leurs modules respectifs,
#   par ex. api/services/chat_omnichannel/deepseek_service.py :
#
#   from .llm_service import LLMService, Message, GeneratedResponse
#   class DeepSeekService(LLMService):
#       ...
#
# Et les autres parties du code doivent importer DeepSeekService
# DIRECTEMENT depuis deepseek_service.py, pas depuis llm_service.py.
