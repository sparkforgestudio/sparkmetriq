# api/services/talent/audit_service.py
"""
Service d'audit trail pour la gestion des talents.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from api.databases.databases import db

async def log_event(
    tenant_id: str, 
    actor_id: str, 
    action: str, 
    muse_id: Optional[str] = None, 
    user_hash: Optional[str] = None, 
    meta: Optional[Dict[str, Any]] = None
):
    """Enregistre un événement dans l'audit trail."""
    doc = {
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "muse_id": muse_id,
        "user_hash": user_hash,
        "action": action,
        "meta": meta or {},
        "ts": datetime.now(timezone.utc)
    }
    await db["audit_events"].insert_one(doc)

async def log_message_event(
    tenant_id: str,
    actor_id: str,
    muse_id: str,
    user_hash: str,
    platform: str,
    action: str,
    message_id: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
):
    """Enregistre un événement lié à un message."""
    await log_event(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        muse_id=muse_id,
        user_hash=user_hash,
        meta={
            "platform": platform,
            "message_id": message_id,
            **(meta or {})
        }
    )

async def log_tag_event(
    tenant_id: str,
    actor_id: str,
    muse_id: str,
    user_hash: str,
    tag: str,
    action: str = "tag_added"
):
    """Enregistre un événement de tag."""
    await log_event(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        muse_id=muse_id,
        user_hash=user_hash,
        meta={"tag": tag}
    )

async def log_note_event(
    tenant_id: str,
    actor_id: str,
    muse_id: str,
    user_hash: str,
    note_id: str,
    action: str = "note_added"
):
    """Enregistre un événement de note."""
    await log_event(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        muse_id=muse_id,
        user_hash=user_hash,
        meta={"note_id": note_id}
    )

async def log_escalation_event(
    tenant_id: str,
    actor_id: str,
    muse_id: str,
    user_hash: str,
    level: int,
    reason: Optional[str] = None
):
    """Enregistre un événement d'escalade."""
    await log_event(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action="escalated",
        muse_id=muse_id,
        user_hash=user_hash,
        meta={
            "level": level,
            "reason": reason
        }
    )

async def log_role_event(
    tenant_id: str,
    actor_id: str,
    target_user_id: str,
    role: str,
    action: str = "role_granted"
):
    """Enregistre un événement de rôle."""
    await log_event(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        meta={
            "target_user_id": target_user_id,
            "role": role
        }
    )

async def log_assignment_event(
    tenant_id: str,
    actor_id: str,
    muse_id: str,
    platform: str,
    operator_id: str,
    action: str = "assignment_added"
):
    """Enregistre un événement d'assignation."""
    await log_event(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        muse_id=muse_id,
        meta={
            "platform": platform,
            "operator_id": operator_id
        }
    )

async def log_integration_event(
    tenant_id: str,
    actor_id: str,
    provider: str,
    action: str,
    meta: Optional[Dict[str, Any]] = None
):
    """Enregistre un événement d'intégration."""
    await log_event(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        meta={
            "provider": provider,
            **(meta or {})
        }
    )

async def get_audit_events(
    tenant_id: str,
    muse_id: Optional[str] = None,
    user_hash: Optional[str] = None,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 500
) -> List[Dict[str, Any]]:
    """Récupère les événements d'audit avec filtres."""
    query = {"tenant_id": tenant_id}
    
    if muse_id:
        query["muse_id"] = muse_id
    if user_hash:
        query["user_hash"] = user_hash
    if actor_id:
        query["actor_id"] = actor_id
    if action:
        query["action"] = action
    if date_from or date_to:
        query["ts"] = {}
        if date_from:
            query["ts"]["$gte"] = date_from
        if date_to:
            query["ts"]["$lte"] = date_to
    
    cursor = db["audit_events"].find(query).sort("ts", -1).limit(limit)
    events = []
    
    for event in await cursor.to_list(None):
        event["id"] = str(event["_id"])
        del event["_id"]
        events.append(event)
    
    return events

async def get_audit_summary(
    tenant_id: str,
    muse_id: Optional[str] = None,
    days: int = 7
) -> Dict[str, Any]:
    """Récupère un résumé des événements d'audit."""
    from datetime import timedelta
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Compter les événements par type
    pipeline = [
        {
            "$match": {
                "tenant_id": tenant_id,
                "ts": {"$gte": cutoff}
            }
        },
        {
            "$group": {
                "_id": "$action",
                "count": {"$sum": 1}
            }
        }
    ]
    
    if muse_id:
        pipeline[0]["$match"]["muse_id"] = muse_id
    
    events_by_action = await db["audit_events"].aggregate(pipeline).to_list(None)
    action_counts = {item["_id"]: item["count"] for item in events_by_action}
    
    # Compter les événements par acteur
    pipeline_actor = [
        {
            "$match": {
                "tenant_id": tenant_id,
                "ts": {"$gte": cutoff}
            }
        },
        {
            "$group": {
                "_id": "$actor_id",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"count": -1}
        },
        {
            "$limit": 10
        }
    ]
    
    if muse_id:
        pipeline_actor[0]["$match"]["muse_id"] = muse_id
    
    top_actors = await db["audit_events"].aggregate(pipeline_actor).to_list(None)
    
    return {
        "period_days": days,
        "total_events": sum(action_counts.values()),
        "events_by_action": action_counts,
        "top_actors": top_actors,
        "muse_id": muse_id
    }

async def export_audit_data(
    tenant_id: str,
    format: str = "json",
    muse_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """Exporte les données d'audit."""
    events = await get_audit_events(
        tenant_id=tenant_id,
        muse_id=muse_id,
        date_from=date_from,
        date_to=date_to,
        limit=10000  # Limite pour l'export
    )
    
    return {
        "format": format,
        "data": events,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_records": len(events),
        "filters": {
            "muse_id": muse_id,
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None
        }
    }

async def cleanup_old_audit_events(tenant_id: str, days_to_keep: int = 365) -> int:
    """Nettoie les anciens événements d'audit."""
    from datetime import timedelta
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    
    result = await db["audit_events"].delete_many({
        "tenant_id": tenant_id,
        "ts": {"$lt": cutoff}
    })
    
    return result.deleted_count



