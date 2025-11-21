# api/services/ai/translate_service.py
"""
Service de traduction IA avec détection de langue et réécriture.
Utilise DeepSeek self-host pour la traduction et la réécriture.
"""

import json
import logging
from typing import Tuple, Dict, Any, Optional
from api.core.settings import settings
from api.schemas.translator import TranslateIn, TranslateOut
from api.core.rate_limit import allow
from api.services.chat_omnichannel.llm_service import (
    Message, LLMService, GeneratedResponse
)
from api.services.chat_omnichannel.deepseek_service import DeepSeekService

logger = logging.getLogger(__name__)

# Importer langdetect si disponible
try:
    from langdetect import detect as langdetect_detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    logger.warning("langdetect not installed. Install with: pip install langdetect")
    LANGDETECT_AVAILABLE = False


def _detect_lang(text: str) -> str:
    """
    Détecte la langue du texte.
    
    Args:
        text: Texte à analyser
        
    Returns:
        Code langue ISO-639-1 ou "und" si indéterminé
    """
    if not LANGDETECT_AVAILABLE:
        logger.warning("langdetect not available, returning 'und'")
        return "und"
    
    try:
        return langdetect_detect(text)
    except Exception as e:
        logger.warning(f"Erreur détection langue: {e}")
        return "und"


def _build_prompt(
    text: str,
    source: str,
    target: str,
    tone: str,
    emoji: str,
    formality: str
) -> str:
    """
    Construit le prompt pour le LLM.
    
    Args:
        text: Texte à traduire
        source: Langue source
        target: Langue cible
        tone: Ton souhaité
        emoji: Niveau d'emojis
        formality: Niveau de formalité
        
    Returns:
        Prompt formaté
    """
    return f"""You are a professional multilingual rewriter for creator-fan messaging.
Source language: {source}
Target language: {target}
Tone: {tone}  # neutral|flirt|respectful|playful
Emoji level: {emoji}  # none|low|medium|high
Formality: {formality}  # casual|standard|formal

Task:
1) Translate the text to the target language.
2) Then rewrite it in a natural, platform-appropriate style respecting tone, emoji density and formality.
3) Keep meaning; avoid adding facts; keep it short if original is short.

Output JSON with keys: "translated", "rewritten".
Text:
\"\"\"{text}\"\"\"
"""


def _postprocess(raw: str) -> Tuple[str, str]:
    """
    Post-traite la réponse du LLM pour extraire translated et rewritten.
    
    Args:
        raw: Réponse brute du LLM
        
    Returns:
        Tuple (translated, rewritten)
    """
    # Essayer de parser JSON
    try:
        # Nettoyer le texte si nécessaire
        cleaned = raw.strip()
        
        # Chercher un bloc JSON dans la réponse
        if "{" in cleaned and "}" in cleaned:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            json_str = cleaned[start:end]
            data = json.loads(json_str)
            translated = data.get("translated", "").strip()
            rewritten = data.get("rewritten", "").strip()
            
            if translated and rewritten:
                return translated, rewritten
        
        # Fallback: essayer de parser directement
        data = json.loads(cleaned)
        translated = data.get("translated", "").strip()
        rewritten = data.get("rewritten", "").strip()
        return translated or cleaned, rewritten or cleaned
        
    except json.JSONDecodeError:
        # Fallback: utiliser le texte tel quel pour les deux
        cleaned = raw.strip().strip('"').strip("'")
        return cleaned, cleaned
    except Exception as e:
        logger.warning(f"Erreur post-processing: {e}, using raw text")
        cleaned = raw.strip().strip('"').strip("'")
        return cleaned, cleaned


def _get_llm_service() -> LLMService:
    """
    Récupère le service LLM approprié selon la configuration.
    
    Returns:
        Instance de LLMService
    """
    import os
    
    # Configuration du traducteur ou fallback sur la config générale
    base_url = settings.translator_llm_base_url or os.getenv("DEEPSEEK_ENDPOINT_URL") or os.getenv("LLM_BASE_URL")
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    
    # Par défaut, utiliser DeepSeek self-host
    endpoint_url = base_url or "http://localhost:11434"
    return DeepSeekService(endpoint_url=endpoint_url, api_key=api_key)


async def translate_once(payload: TranslateIn) -> TranslateOut:
    """
    Effectue une traduction unique.
    
    Args:
        payload: Requête de traduction
        
    Returns:
        Résultat de traduction
        
    Raises:
        RuntimeError: Si le feature flag est désactivé ou rate limit atteint
        ValueError: Si le texte est trop long
    """
    # Vérifier le feature flag
    if not settings.feature_translator_enabled:
        raise RuntimeError("Translator feature disabled")
    
    # Vérifier le rate limit
    org_id = payload.org_id or "default"
    ok, reason = allow(org_id)
    if not ok:
        raise RuntimeError(f"Translator rate limit: {reason}")
    
    # Vérifier la longueur
    if len(payload.text) > settings.translator_max_chars:
        raise ValueError(f"Text too long (max {settings.translator_max_chars} chars)")
    
    # Détecter la langue source si non fournie
    source = payload.source_lang or _detect_lang(payload.text)
    
    # Construire le prompt
    prompt = _build_prompt(
        text=payload.text,
        source=source,
        target=payload.target_lang,
        tone=payload.tone,
        emoji=payload.emoji,
        formality=payload.formality
    )
    
    # Appeler le LLM
    try:
        llm_service = _get_llm_service()
        messages = [Message(role="user", content=prompt)]
        
        response = await llm_service.generate(
            messages=messages,
            tenant_id=org_id
        )
        
        raw_text = response.text
        
        # Post-traiter la réponse
        translated, rewritten = _postprocess(raw_text)
        
        # Extraire les tokens utilisés si disponibles
        tokens_used = None
        if response.usage and isinstance(response.usage, dict):
            tokens_used = response.usage.get("total_tokens") or response.usage.get("tokens")
        
        return TranslateOut(
            source_lang=source,
            target_lang=payload.target_lang,
            original=payload.text,
            translated=translated,
            rewritten=rewritten,
            quality="ok" if translated and rewritten else "needs_review",
            tokens_used=tokens_used,
            extras={
                "tone": payload.tone,
                "emoji": payload.emoji,
                "formality": payload.formality
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur traduction: {e}")
        raise RuntimeError(f"Translation failed: {str(e)}")
