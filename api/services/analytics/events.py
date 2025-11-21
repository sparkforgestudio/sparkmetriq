# api/services/analytics/events.py
"""
Service d'analytics pour les événements de traduction et autres événements métier.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from api.databases.databases import get_bi_db


async def emit_translation_event(
    org_id: str,
    conversation_id: Optional[str],
    direction: str,
    source: str,
    target: str
) -> str:
    """
    Émet un événement analytics pour une traduction.
    
    Args:
        org_id: ID de l'organisation
        conversation_id: ID de la conversation
        direction: Direction (inbound|outbound)
        source: Langue source
        target: Langue cible
        
    Returns:
        ID du document créé
    """
    db_bi = get_bi_db()
    
    event_doc = {
        "org_id": org_id,
        "type": "translator_used",
        "direction": direction,  # inbound|outbound
        "source_lang": source,
        "target_lang": target,
        "conversation_id": conversation_id,
        "ts": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db_bi["analytics_events"].insert_one(event_doc)
    return str(result.inserted_id)


async def emit_event(
    org_id: str,
    event_type: str,
    data: Dict[str, Any],
    conversation_id: Optional[str] = None,
    timestamp: Optional[datetime] = None
) -> str:
    """
    Émet un événement analytics générique.
    
    Args:
        org_id: ID de l'organisation
        event_type: Type d'événement
        data: Données de l'événement
        conversation_id: ID de la conversation (optionnel)
        timestamp: Timestamp (défaut: maintenant)
        
    Returns:
        ID du document créé
    """
    db_bi = get_bi_db()
    
    event_doc = {
        "org_id": org_id,
        "type": event_type,
        "data": data,
        "conversation_id": conversation_id,
        "ts": timestamp or datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db_bi["analytics_events"].insert_one(event_doc)
    return str(result.inserted_id)


async def emit_recap_event(
    org_id: str,
    conversation_id: str,
    kind: str,
    count: int
) -> str:
    """
    Émet un événement analytics pour un recap de conversation.
    
    Args:
        org_id: ID de l'organisation
        conversation_id: ID de la conversation
        kind: Type de recap (full|delta)
        count: Nombre de messages traités
        
    Returns:
        ID du document créé
    """
    db_bi = get_bi_db()
    
    event_doc = {
        "org_id": org_id,
        "type": "conversation_recap",
        "kind": kind,  # full|delta
        "messages_count": count,
        "conversation_id": conversation_id,
        "ts": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db_bi["analytics_events"].insert_one(event_doc)
    return str(result.inserted_id)


async def emit_campaign_event(
    org_id: str,
    campaign_id: str,
    kind: str,
    count: int
) -> str:
    """
    Émet un événement analytics pour une campagne.
    
    Args:
        org_id: ID de l'organisation
        campaign_id: ID de la campagne
        kind: Type d'événement (queued|sent|failed)
        count: Nombre de messages
        
    Returns:
        ID du document créé
    """
    db_bi = get_bi_db()
    
    event_doc = {
        "org_id": org_id,
        "type": "campaign",
        "kind": kind,  # queued|sent|failed
        "count": count,
        "campaign_id": campaign_id,
        "ts": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db_bi["analytics_events"].insert_one(event_doc)
    return str(result.inserted_id)


async def ensure_analytics_indexes():
    """Crée les index nécessaires pour analytics_events."""
    db_bi = get_bi_db()
    await db_bi["analytics_events"].create_index([("org_id", 1), ("type", 1), ("ts", -1)])
    await db_bi["analytics_events"].create_index([("org_id", 1), ("conversation_id", 1), ("ts", -1)])
    await db_bi["analytics_events"].create_index([("type", 1), ("ts", -1)])
    await db_bi["analytics_events"].create_index([("campaign_id", 1), ("ts", -1)])
