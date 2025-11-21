import abc
from typing import List, Optional
from pydantic import BaseModel

# Message model pour l'interface LLM
class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

class GeneratedResponse(BaseModel):
    text: str
    usage: Optional[dict] = None  # tokens count, etc.

class LLMService(abc.ABC):
    """
    Interface abstraite pour un client LLM (OpenAI, DeepSeek...).
    Implémentez :
      - generate : appel synchrone (one-shot)
      - stream   : appel streaming (facultatif)
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
        pass

    async def stream(
        self,
        messages: List[Message],
        tenant_id: Optional[str] = None,
    ):
        """
        Appel streaming si supporté par le fournisseur.
        Génère un itérable de fragments type Message (role="assistant").
        Optionnel : surcouche vos propres besoins.
        """
        raise NotImplementedError("Streaming non implémenté pour ce service")

# Exemple de sous-classe pour OpenAI
class OpenAIService(LLMService):
    async def generate(self, messages: List[Message], tenant_id: Optional[str] = None) -> GeneratedResponse:
        from openai import OpenAI  # supposé import
        client = OpenAI(api_key=self.api_key)
        resp = await client.chat.create(
            model=self.model,
            temperature=self.temperature,
            messages=[m.dict() for m in messages],
        )
        content = resp.choices[0].message.content
        usage = resp.usage.to_dict() if hasattr(resp, 'usage') else None
        return GeneratedResponse(text=content, usage=usage)

# Import et réexport de DeepSeekService depuis le module séparé
# L'import est fait à la fin pour éviter les problèmes d'import circulaire
# (deepseek_service.py importe depuis llm_service.py, mais après la définition des classes)
from .deepseek_service import DeepSeekService