# api/services/ai/recap_service.py
"""
Service de résumé IA des conversations.
Utilise DeepSeek pour générer des recaps structurés.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from api.core.settings import settings
from api.databases.databases import get_core_db
from api.schemas.recap import RecapGenerateIn, RecapOut, RecapStructured
from api.services.chat_omnichannel.llm_service import Message
from api.services.chat_omnichannel.deepseek_service import DeepSeekService

logger = logging.getLogger(__name__)

# Collections
CHAT_COLL = "chat_messages"
RECAP_COLL = "conversation_recaps"


def _fetch_window_desc(kind: str, since_ts: Optional[datetime], total: int) -> Dict[str, Any]:
    """Génère la description de la fenêtre."""
    out = {"kind": kind, "count": total}
    if since_ts:
        out["since_ts"] = since_ts
    return out


async def _load_messages(
    org_id: str,
    conversation_id: str,
    since_ts: Optional[datetime],
    max_messages: int
) -> List[Dict[str, Any]]:
    """
    Charge les messages d'une conversation dans une fenêtre donnée.
    
    Args:
        org_id: ID de l'organisation
        conversation_id: ID de la conversation
        since_ts: Timestamp depuis lequel charger (None pour tout)
        max_messages: Nombre maximum de messages
        
    Returns:
        Liste des messages
    """
    db = get_core_db()
    query = {"org_id": org_id, "conversation_id": conversation_id}
    if since_ts:
        query["timestamp"] = {"$gt": since_ts}
    
    cursor = (
        db[CHAT_COLL]
        .find(query)
        .sort("timestamp", 1)
        .limit(max_messages)
    )
    return await cursor.to_list(length=max_messages)


def _format_messages_for_prompt(messages: List[Dict[str, Any]]) -> str:
    """
    Formate les messages en transcript pour le prompt.
    
    Args:
        messages: Liste des messages
        
    Returns:
        Transcript formaté
    """
    lines = []
    for m in messages:
        role = m.get("role", "user")
        ts = m.get("timestamp")
        if isinstance(ts, datetime):
            ts_str = ts.isoformat()
        else:
            ts_str = str(ts)
        text = (m.get("text") or m.get("message") or "").strip().replace("\n", " ")
        lines.append(f"[{ts_str}] {role.upper()}: {text}")
    return "\n".join(lines)


def _recap_prompt(transcript: str, include_examples: bool) -> str:
    """
    Construit le prompt pour le LLM.
    
    Args:
        transcript: Transcript formaté
        include_examples: Inclure des exemples
        
    Returns:
        Prompt complet
    """
    examples = """
Examples (style):
- Preferences: "Loves cosplay elf & teasing DMs", "Responds well to playful tone"
- Objections: "Price too high", "Wants more previews before PPV"
- Purchases: [{"item":"PPV custom video", "amount": 25, "date":"2025-10-25"}]
- Sensitive: ["jealousy", "privacy anxiety"]
- Next actions: ["Send teaser pack Friday", "Offer 20% PPV bundle in 3 days"]
- Tone: "playful with light emojis"
""" if include_examples else ""
    
    return f"""You are a CRM assistant for creator-fan messaging.
Read the transcript and produce a structured recap JSON with keys:
summary, preferences[], objections[], purchases[], sensitive_topics[], next_actions[], recommended_tone.

Rules:
- Be concise, faithful, and helpful for the next operator who joins.
- Extract concrete details (preferences/objections) if present; otherwise leave list empty.
- Purchases should be inferred only if explicitly mentioned.
- Sensitive topics list must be cautious and non-judgmental.
- recommended_tone should be a short phrase.

Transcript:
\"\"\"
{transcript}
\"\"\"
{examples}
Output pure JSON only.
"""


def _parse_structured(raw: str) -> RecapStructured:
    """
    Parse la réponse du LLM en structure RecapStructured.
    
    Args:
        raw: Réponse brute du LLM
        
    Returns:
        Structure parsée
    """
    try:
        # Nettoyer et parser JSON
        cleaned = raw.strip()
        
        # Chercher un bloc JSON dans la réponse
        if "{" in cleaned and "}" in cleaned:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            json_str = cleaned[start:end]
            data = json.loads(json_str)
        else:
            data = json.loads(cleaned)
            
    except json.JSONDecodeError as e:
        logger.warning(f"Erreur parsing JSON recap: {e}, using fallback")
        # Fallback: tout dans le summary
        return RecapStructured(summary=cleaned.strip()[:500])
    except Exception as e:
        logger.error(f"Erreur parsing structured recap: {e}")
        return RecapStructured(summary=raw.strip()[:500])
    
    def _list(x, typ=str):
        """Convertit en liste de strings."""
        if not isinstance(x, list):
            return []
        return [str(v) for v in x]
    
    def _purchases(x):
        """Convertit en liste de dicts."""
        if not isinstance(x, list):
            return []
        out = []
        for it in x:
            if isinstance(it, dict):
                out.append({k: it[k] for k in it.keys()})
            else:
                out.append({"item": str(it)})
        return out
    
    return RecapStructured(
        summary=str(data.get("summary", "")).strip(),
        preferences=_list(data.get("preferences", [])),
        objections=_list(data.get("objections", [])),
        purchases=_purchases(data.get("purchases", [])),
        sensitive_topics=_list(data.get("sensitive_topics", [])),
        next_actions=_list(data.get("next_actions", [])),
        recommended_tone=(data.get("recommended_tone") or None)
    )


def _get_llm_service() -> DeepSeekService:
    """
    Récupère le service LLM pour le recap.
    
    Returns:
        Instance de DeepSeekService
    """
    import os
    
    base_url = settings.recap_llm_base_url or os.getenv("DEEPSEEK_ENDPOINT_URL") or os.getenv("LLM_BASE_URL")
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    
    endpoint_url = base_url or "http://localhost:11434"
    return DeepSeekService(endpoint_url=endpoint_url, api_key=api_key)


async def generate_recap(payload: RecapGenerateIn) -> RecapOut:
    """
    Génère un recap pour une conversation.
    
    Args:
        payload: Requête de génération
        
    Returns:
        Recap généré
        
    Raises:
        RuntimeError: Si le feature flag est désactivé
        ValueError: Si aucun message trouvé
    """
    if not settings.feature_convo_recap_enabled:
        raise RuntimeError("Conversation recap feature disabled")
    
    db = get_core_db()
    
    # Charger les messages
    messages = await _load_messages(
        org_id=payload.org_id,
        conversation_id=payload.conversation_id,
        since_ts=payload.since_ts,
        max_messages=min(payload.max_messages, settings.recap_max_messages_per_call),
    )
    
    if not messages:
        raise ValueError("No messages found for this window")
    
    # Formater le transcript
    transcript = _format_messages_for_prompt(messages)
    if len(transcript) > settings.recap_max_chars:
        transcript = transcript[-settings.recap_max_chars:]  # Garder la queue
    
    # Construire le prompt
    prompt = _recap_prompt(transcript, payload.include_examples)
    
    # Appeler le LLM
    try:
        llm_service = _get_llm_service()
        messages_llm = [Message(role="user", content=prompt)]
        
        response = await llm_service.generate(
            messages=messages_llm,
            tenant_id=payload.org_id
        )
        
        raw_text = response.text
        
        # Parser la réponse
        structured = _parse_structured(raw_text)
        
        # Extraire les tokens si disponibles
        tokens_used = None
        if response.usage and isinstance(response.usage, dict):
            tokens_used = response.usage.get("total_tokens") or response.usage.get("tokens")
        
    except Exception as e:
        logger.error(f"Erreur génération recap LLM: {e}")
        raise RuntimeError(f"Recap generation failed: {str(e)}")
    
    # Préparer le document
    last_ts = messages[-1].get("timestamp")
    window = _fetch_window_desc(payload.kind, payload.since_ts, len(messages))
    
    doc = {
        "org_id": payload.org_id,
        "conversation_id": payload.conversation_id,
        "muse_id": payload.muse_id,
        "user_id": payload.user_id,
        "last_message_ts": last_ts,
        "window": window,
        "structured": structured.model_dump(),
        "tokens_used": tokens_used,
        "version": "v1",
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Sauvegarder (upsert)
    await db[RECAP_COLL].update_one(
        {"org_id": payload.org_id, "conversation_id": payload.conversation_id},
        {"$set": doc},
        upsert=True
    )
    
    return RecapOut(**doc)



