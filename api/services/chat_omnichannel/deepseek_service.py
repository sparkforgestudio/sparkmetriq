# api/services/chat_omnichannel/deepseek_service.py

from typing import List, Any, Optional
import httpx

# On importe les types et l'interface abstraite depuis llm_service.py
from .llm_service import LLMService, Message, GeneratedResponse

class DeepSeekService(LLMService):
    """
    Client self-hosted pour DeepSeek.
    Expose la méthode `generate` asynchrone.
    """

    def __init__(self, endpoint_url: str, api_key: str):
        self.endpoint_url = endpoint_url
        self.api_key = api_key

    async def generate(
        self,
        messages: List[Message],
        tenant_id: Optional[str] = None
    ) -> GeneratedResponse:
        """
        Envoie le prompt à DeepSeek et retourne un GeneratedResponse.
        """
        # Construire la payload selon votre API DeepSeek
        payload = {
            "tenant_id": tenant_id,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "api_key": self.api_key
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.endpoint_url}/v1/chat/completions",
                json=payload,
                timeout=30.0
            )
            resp.raise_for_status()
            data = resp.json()

        # Adapter selon la structure de réponse de DeepSeek
        text = data["choices"][0]["message"]["content"]
        return GeneratedResponse(text=text)
