# api/services/collab/chat_service.py
"""
Service de chat interne pour la collaboration.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId

from api.databases.databases import get_core_db

CORE = get_core_db()


async def create_thread(payload, created_by: str) -> Dict[str, Any]:
    """
    Crée un thread de collaboration.
    
    Args:
        payload: Requête de création de thread
        created_by: Email du créateur
        
    Returns:
        Thread créé
    """
    now = datetime.now(timezone.utc)
    doc = {
        "org_id": payload.org_id,
        "title": payload.title,
        "muse_id": payload.muse_id,
        "tags": payload.tags or [],
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
        "last_message_preview": None,
        "unread_count": 0
    }
    
    result = await CORE["collab_threads"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc["_id"] = result.inserted_id
    
    return doc


async def post_message(
    org_id: str,
    user_email: str,
    user_role: str,
    payload
) -> Dict[str, Any]:
    """
    Poste un message dans un thread.
    
    Args:
        org_id: ID de l'organisation
        user_email: Email de l'auteur
        user_role: Rôle de l'auteur
        payload: Requête de création de message
        
    Returns:
        Message créé
        
    Raises:
        LookupError: Si thread non trouvé
    """
    try:
        thr = await CORE["collab_threads"].find_one({
            "_id": ObjectId(payload.thread_id),
            "org_id": org_id
        })
    except Exception:
        thr = None
    
    if not thr:
        raise LookupError("Thread not found")
    
    now = datetime.now(timezone.utc)
    msg = {
        "thread_id": thr["_id"],
        "org_id": org_id,
        "author": user_email,
        "role": user_role,
        "body": payload.body,
        "mentions": payload.mentions or [],
        "attachments": payload.attachments or [],
        "meta": payload.meta or {},
        "created_at": now
    }
    
    result = await CORE["collab_messages"].insert_one(msg)
    msg["id"] = str(result.inserted_id)
    msg["_id"] = result.inserted_id
    
    # Mettre à jour le thread
    preview = payload.body[:180] if payload.body else None
    await CORE["collab_threads"].update_one(
        {"_id": thr["_id"]},
        {
            "$set": {
                "updated_at": now,
                "last_message_preview": preview
            }
        }
    )
    
    msg["thread_id"] = str(thr["_id"])
    
    return msg


async def list_threads(
    org_id: str,
    q: Optional[Dict[str, Any]] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Liste les threads d'une organisation.
    
    Args:
        org_id: ID de l'organisation
        q: Filtres optionnels (non utilisé pour l'instant)
        limit: Limite de résultats
        
    Returns:
        Liste des threads
    """
    cursor = (
        CORE["collab_threads"]
        .find({"org_id": org_id})
        .sort("updated_at", -1)
        .limit(limit)
    )
    
    items = await cursor.to_list(length=limit)
    
    out = []
    for t in items:
        out.append({
            "id": str(t["_id"]),
            "org_id": t["org_id"],
            "title": t["title"],
            "muse_id": t.get("muse_id"),
            "tags": t.get("tags", []),
            "created_by": t.get("created_by"),
            "created_at": t["created_at"],
            "updated_at": t["updated_at"],
            "last_message_preview": t.get("last_message_preview"),
            "unread_count": t.get("unread_count", 0),
        })
    
    return out


async def list_messages(
    org_id: str,
    thread_id: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Liste les messages d'un thread.
    
    Args:
        org_id: ID de l'organisation
        thread_id: ID du thread
        limit: Limite de résultats
        
    Returns:
        Liste des messages
    """
    try:
        cursor = (
            CORE["collab_messages"]
            .find({
                "org_id": org_id,
                "thread_id": ObjectId(thread_id)
            })
            .sort("created_at", 1)
            .limit(limit)
        )
    except Exception:
        return []
    
    items = await cursor.to_list(length=limit)
    
    out = []
    for m in items:
        out.append({
            "id": str(m["_id"]),
            "thread_id": str(m["thread_id"]),
            "org_id": m["org_id"],
            "author": m["author"],
            "role": m["role"],
            "body": m["body"],
            "mentions": m.get("mentions", []),
            "attachments": m.get("attachments", []),
            "created_at": m["created_at"],
        })
    
    return out



