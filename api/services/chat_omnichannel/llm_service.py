# api/services/chat_omnichannel/llm_service.py
from __future__ import annotations

import abc
from typing import List, Optional, Dict, Any

from pydantic import BaseModel


class Message(BaseModel):
    """
    Représente un message dans une conversation LLM.
    role : "system" | "user" | "assistant"
    content : texte du message
    """
    role: str
    content: str


class GeneratedResponse(BaseModel):
    """
    Réponse standardisée renvoyée par un LLM provider.
    text   : texte généré
    usage  : infos d'usage (tokens, coût…) optionnelles
    """
    text: str
    usage: Optional[Dict[str, Any]] = None


class LLMService(abc.ABC):
    """
    Interface abstraite pour un client LLM (OpenAI, DeepSeek, etc.).
    Implémentez :
      - generate : appel synchrone (one-shot)
      - stream   : appel streaming (facultatif)
    """

    def __init__(self, api_key: str, model: str, temperature: float = 0.7) -> None:
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
        Par défaut, non implémenté.
        """
        raise NotImplementedError("Streaming non implémenté pour ce service")


# -------------------------------------------------------------------
# Implémentation facultative pour OpenAI
# (ne doit PAS casser si openai n'est pas installé et n'est pas utilisée)
# -------------------------------------------------------------------
try:
    # Async client moderne (openai>=1.*). Adapte si tu utilises une autre version.
    from openai import AsyncOpenAI  # type: ignore
except ImportError:  # pragma: no cover - dépendance optionnelle
    AsyncOpenAI = None  # type: ignore


class OpenAIService(LLMService):
    """
    Exemple de sous-classe LLMService pour OpenAI.
    À n'utiliser que si la lib 'openai' est installée.
    """

    async def generate(
        self,
        messages: List[Message],
        tenant_id: Optional[str] = None,
    ) -> GeneratedResponse:
        if AsyncOpenAI is None:
            raise RuntimeError(
                "La bibliothèque 'openai' n'est pas installée. "
                "Installez-la ou n'utilisez pas OpenAIService."
            )

        client = AsyncOpenAI(api_key=self.api_key)
        resp = await client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[m.model_dump() for m in messages],
        )

        content = resp.choices[0].message.content or ""
        usage = resp.usage.model_dump() if getattr(resp, "usage", None) else None

        return GeneratedResponse(text=content, usage=usage)


# Note important :
# DeepSeekService est défini dans deepseek_service.py
# Pour éviter tout import circulaire :
# - deepseek_service.py importe LLMService, Message, GeneratedResponse depuis ce module
# - MAIS ce module ne doit PAS importer DeepSeekService.
# Si tu as besoin d'un "factory" pour choisir le provider, fais-le
# dans un autre fichier (ex: provider_registry.py) ou via un import local
# à l'intérieur d'une fonction, jamais en import global ici.
