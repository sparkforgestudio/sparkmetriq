# api/services/intent/llm_handler.py
"""
Handler LLM pour le Moteur d'Intentions.
Deux chemins : freeform_reply (Mode A) et style_rewrite (Mode B).
"""

import logging
import os
from typing import Dict, Any, List
from api.services.chat_omnichannel.llm_service import Message
from api.services.chat_omnichannel.deepseek_service import DeepSeekService

logger = logging.getLogger(__name__)


def _get_llm_service() -> DeepSeekService:
    """
    Récupère le service LLM DeepSeek.
    
    Returns:
        Instance de DeepSeekService
    """
    endpoint_url = (
        os.getenv("DEEPSEEK_ENDPOINT_URL") or
        os.getenv("LLM_BASE_URL") or
        "http://localhost:11434"
    )
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    
    return DeepSeekService(endpoint_url=endpoint_url, api_key=api_key)


class LLMHandler:
    """
    Handler LLM pour deux modes :
    - freeform_reply: génération complète (Mode A)
    - style_rewrite: paraphrase stylée d'un template (Mode B)
    """
    
    def __init__(self, temperature: float = 0.7):
        """
        Initialise le handler.
        
        Args:
            temperature: Température pour la génération (0.0-1.0)
        """
        self.temperature = temperature
        self.llm = _get_llm_service()
    
    async def freeform_reply(self, prompt_context: Dict[str, Any]) -> str:
        """
        Génère une réponse libre en mode LLM Pilote (Mode A).
        
        Args:
            prompt_context: Contexte avec system, user, retrieved, brand_rules, platform, persona
            
        Returns:
            Texte généré
        """
        system = prompt_context.get("system", "You are a muse assistant.")
        user_text = prompt_context.get("user", "")
        retrieved = prompt_context.get("retrieved", [])
        brand_rules = prompt_context.get("brand_rules", [])
        platform = prompt_context.get("platform", "instagram")
        persona = prompt_context.get("persona", {})
        
        # Construire le prompt système
        system_parts = [system]
        
        # Ajouter les règles de branding
        if brand_rules:
            brand_text = "\n".join([f"- {rule}" for rule in brand_rules])
            system_parts.append(f"\nBrand rules (MANDATORY):\n{brand_text}")
        
        # Ajouter le profil de persona
        if persona:
            tone_info = []
            if isinstance(persona, dict):
                if persona.get("do"):
                    tone_info.append(f"DO: {', '.join(persona.get('do', []))}")
                if persona.get("dont"):
                    tone_info.append(f"DON'T: {', '.join(persona.get('dont', []))}")
                if persona.get("keywords"):
                    tone_info.append(f"Keywords: {', '.join(persona.get('keywords', []))}")
                emoji_ratio = persona.get("emoji_ratio", 0.2)
                if emoji_ratio > 0:
                    tone_info.append(f"Emoji usage: {'low' if emoji_ratio < 0.3 else 'medium' if emoji_ratio < 0.6 else 'high'}")
            
            if tone_info:
                system_parts.append(f"\nTone profile:\n" + "\n".join([f"- {info}" for info in tone_info]))
        
        # Construire le contexte utilisateur
        user_parts = []
        
        # Ajouter les snippets de contexte
        if retrieved:
            context_text = "\n".join([
                f"- [{c.get('kind', 'unknown')}] {c.get('text', '')[:200]}"
                for c in retrieved[:5]  # Limiter à 5 pour éviter trop de tokens
            ])
            user_parts.append(f"Context snippets:\n{context_text}")
        
        # Plateforme
        user_parts.append(f"\nPlatform: {platform}")
        user_parts.append(f"User says: {user_text}")
        user_parts.append("\nReply naturally, persuasively, and compliantly. Be authentic to the muse's brand.")
        
        system_content = "\n".join(system_parts)
        user_content = "\n".join(user_parts)
        
        messages = [
            Message(role="system", content=system_content),
            Message(role="user", content=user_content)
        ]
        
        try:
            response = await self.llm.generate(messages=messages)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Erreur lors de la génération LLM (freeform): {e}")
            return "Thanks for your message! 😊"
    
    async def style_rewrite(self, template: str, prompt_context: Dict[str, Any]) -> str:
        """
        Réécrit un template avec le style de la muse (Mode B).
        
        Args:
            template: Template de base
            prompt_context: Contexte avec brand_rules, platform, persona, retrieved
            
        Returns:
            Texte stylisé
        """
        brand_rules = prompt_context.get("brand_rules", [])
        platform = prompt_context.get("platform", "instagram")
        persona = prompt_context.get("persona", {})
        retrieved = prompt_context.get("retrieved", [])
        
        # Construire le prompt
        system_parts = [
            "You are a careful, brand-compliant stylist. Rewrite the template "
            "while respecting the muse's tone and brand rules exactly."
        ]
        
        # Règles de branding
        if brand_rules:
            brand_text = "\n".join([f"- {rule}" for rule in brand_rules])
            system_parts.append(f"\nBrand rules (MANDATORY):\n{brand_text}")
        
        # Profil de persona
        if persona:
            tone_info = []
            if isinstance(persona, dict):
                if persona.get("do"):
                    tone_info.append(f"DO: {', '.join(persona.get('do', []))}")
                if persona.get("dont"):
                    tone_info.append(f"DON'T: {', '.join(persona.get('dont', []))}")
                if persona.get("emoji_ratio"):
                    emoji_ratio = persona.get("emoji_ratio", 0.2)
                    tone_info.append(f"Emoji usage: {'low' if emoji_ratio < 0.3 else 'medium' if emoji_ratio < 0.6 else 'high'}")
            
            if tone_info:
                system_parts.append(f"\nTone profile:\n" + "\n".join([f"- {info}" for info in tone_info]))
        
        # Contexte utilisateur
        user_parts = []
        
        # Context snippets (limité pour le rewrite)
        if retrieved:
            context_text = "\n".join([
                f"- [{c.get('kind', 'unknown')}] {c.get('text', '')[:150]}"
                for c in retrieved[:3]
            ])
            user_parts.append(f"Context (for reference):\n{context_text}")
        
        user_parts.append(f"\nPlatform: {platform}")
        user_parts.append(f"\nTemplate to rewrite:\n{template}")
        user_parts.append(
            "\nConstraints:\n"
            "- Respect brand do/don't exactly\n"
            "- Keep approximate length & platform etiquette\n"
            "- Use subtle emojis if consistent with tone\n"
            "- Maintain the template's intent and key information\n"
            "- Sound natural and authentic"
        )
        
        system_content = "\n".join(system_parts)
        user_content = "\n".join(user_parts)
        
        messages = [
            Message(role="system", content=system_content),
            Message(role="user", content=user_content)
        ]
        
        try:
            response = await self.llm.generate(messages=messages)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Erreur lors de la génération LLM (rewrite): {e}")
            # Fallback : retourner le template tel quel si erreur
            return template.strip()




