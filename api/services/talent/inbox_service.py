# api/services/talent/inbox_service.py
"""
Service Inbox+ pour la gestion centralisée des conversations.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from bson import ObjectId
from api.databases.databases import db

def _kw(q: Optional[str]) -> Dict[str, Any]:
    """Génère une requête de recherche textuelle."""
    return {"$text": {"$search": q}} if q else {}

async def ensure_thread(tenant_id: str, muse_id: str, platform: str, user_hash: str):
    """Crée ou met à jour un thread de conversation."""
    await db["chat_threads"].update_one(
        {"tenant_id": tenant_id, "muse_id": muse_id, "user_hash": user_hash},
        {
            "$setOnInsert": {
                "platform": platform,
                "last_message": None,
                "last_ts": datetime.now(timezone.utc),
                "unseen_count": 0,
                "priority": 0,
                "tags": []
            }
        },
        upsert=True
    )

async def update_thread_from_message(
    tenant_id: str,
    muse_id: str,
    user_hash: str,
    message_text: str,
    platform: str,
    role: str
):
    """Met à jour un thread à partir d'un nouveau message."""
    now = datetime.now(timezone.utc)
    
    # Mettre à jour le thread
    update_fields = {
        "last_message": message_text,
        "last_ts": now,
        "platform": platform
    }
    
    # Incrémenter le compteur de messages non vus si c'est un message utilisateur
    if role == "user":
        update_fields["unseen_count"] = 1
    
    await db["chat_threads"].update_one(
        {"tenant_id": tenant_id, "muse_id": muse_id, "user_hash": user_hash},
        {
            "$set": update_fields,
            "$inc": {"unseen_count": 1} if role == "user" else {}
        },
        upsert=True
    )

async def list_threads(
    tenant_id: str, 
    filters: Dict[str, Any], 
    page: int, 
    page_size: int
) -> Tuple[int, List[Dict[str, Any]]]:
    """Liste les threads avec filtres et pagination."""
    q = {"tenant_id": tenant_id}
    
    if filters.get("muse_id"):
        q["muse_id"] = filters["muse_id"]
    if filters.get("platform"):
        q["platform"] = filters["platform"]
    
    # Filtres par statut
    status = filters.get("status")
    if status == "vip":
        q["tags"] = {"$in": ["vip"]}
    elif status == "ppv_sent":
        q["tags"] = {"$in": ["ppv_sent"]}
    elif status == "escalated":
        q["priority"] = {"$gt": 0}
    elif status == "new":
        q["unseen_count"] = {"$gt": 0}
    elif status == "replied":
        q["unseen_count"] = 0
    
    # Recherche textuelle
    if filters.get("q"):
        q["last_message"] = {"$regex": filters["q"], "$options": "i"}
    
    total = await db["chat_threads"].count_documents(q)
    
    cursor = db["chat_threads"].find(q).sort([
        ("priority", -1),
        ("last_ts", -1)
    ]).skip((page - 1) * page_size).limit(page_size)
    
    rows = await cursor.to_list(None)
    for r in rows:
        r["id"] = str(r["_id"])
        del r["_id"]
    
    return total, rows

async def get_thread_details(tenant_id: str, muse_id: str, user_hash: str) -> Optional[Dict[str, Any]]:
    """Récupère les détails d'un thread spécifique."""
    thread = await db["chat_threads"].find_one({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "user_hash": user_hash
    })
    
    if not thread:
        return None
    
    thread["id"] = str(thread["_id"])
    del thread["_id"]
    
    # Récupérer les messages récents
    messages = await db["chat_messages"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "user_id": user_hash
    }).sort("timestamp", -1).limit(50).to_list(None)
    
    # Récupérer les notes
    notes = await db["fan_notes"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "user_hash": user_hash
    }).sort("ts", -1).limit(10).to_list(None)
    
    # Récupérer les tags
    tags = await db["fan_tags"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "user_hash": user_hash
    }).to_list(None)
    
    thread["messages"] = messages
    thread["notes"] = notes
    thread["tags"] = [tag["tag"] for tag in tags]
    
    return thread

async def tag_fan(tenant_id: str, muse_id: str, user_hash: str, tag: str):
    """Ajoute un tag à un fan."""
    # Ajouter le tag dans la collection fan_tags
    await db["fan_tags"].update_one(
        {
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "user_hash": user_hash,
            "tag": tag
        },
        {
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    # Ajouter le tag au thread
    await db["chat_threads"].update_one(
        {
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "user_hash": user_hash
        },
        {
            "$addToSet": {"tags": tag}
        }
    )

async def remove_tag(tenant_id: str, muse_id: str, user_hash: str, tag: str):
    """Retire un tag d'un fan."""
    # Retirer le tag de la collection fan_tags
    await db["fan_tags"].delete_one({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "user_hash": user_hash,
        "tag": tag
    })
    
    # Retirer le tag du thread
    await db["chat_threads"].update_one(
        {
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "user_hash": user_hash
        },
        {
            "$pull": {"tags": tag}
        }
    )

async def add_note(
    tenant_id: str, 
    author_id: str, 
    muse_id: str, 
    user_hash: str, 
    text: str
) -> str:
    """Ajoute une note à un fan."""
    doc = {
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "user_hash": user_hash,
        "text": text,
        "author_id": author_id,
        "ts": datetime.now(timezone.utc)
    }
    result = await db["fan_notes"].insert_one(doc)
    return str(result.inserted_id)

async def list_notes(
    tenant_id: str, 
    muse_id: str, 
    user_hash: str
) -> List[Dict[str, Any]]:
    """Liste les notes d'un fan."""
    cursor = db["fan_notes"].find({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "user_hash": user_hash
    }).sort("ts", -1)
    
    rows = await cursor.to_list(None)
    for r in rows:
        r["id"] = str(r["_id"])
        del r["_id"]
    
    return rows

async def escalate_thread(
    tenant_id: str, 
    muse_id: str, 
    user_hash: str, 
    level: int = 1,
    reason: Optional[str] = None
):
    """Escalade un thread en augmentant sa priorité."""
    await db["chat_threads"].update_one(
        {
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "user_hash": user_hash
        },
        {
            "$max": {"priority": level},
            "$set": {
                "escalated_at": datetime.now(timezone.utc),
                "escalation_reason": reason
            }
        }
    )

async def mark_thread_as_read(tenant_id: str, muse_id: str, user_hash: str):
    """Marque un thread comme lu."""
    await db["chat_threads"].update_one(
        {
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "user_hash": user_hash
        },
        {
            "$set": {"unseen_count": 0}
        }
    )

async def get_thread_stats(tenant_id: str, muse_id: Optional[str] = None) -> Dict[str, Any]:
    """Récupère les statistiques des threads."""
    query = {"tenant_id": tenant_id}
    if muse_id:
        query["muse_id"] = muse_id
    
    # Compter les threads par statut
    total_threads = await db["chat_threads"].count_documents(query)
    unseen_threads = await db["chat_threads"].count_documents({**query, "unseen_count": {"$gt": 0}})
    escalated_threads = await db["chat_threads"].count_documents({**query, "priority": {"$gt": 0}})
    vip_threads = await db["chat_threads"].count_documents({**query, "tags": {"$in": ["vip"]}})
    
    # Compter par plateforme
    platform_stats = await db["chat_threads"].aggregate([
        {"$match": query},
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}}
    ]).to_list(None)
    
    platform_counts = {item["_id"]: item["count"] for item in platform_stats}
    
    return {
        "total_threads": total_threads,
        "unseen_threads": unseen_threads,
        "escalated_threads": escalated_threads,
        "vip_threads": vip_threads,
        "platform_counts": platform_counts
    }

async def search_threads(
    tenant_id: str,
    query: str,
    muse_id: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Recherche dans les threads."""
    search_query = {
        "tenant_id": tenant_id,
        "last_message": {"$regex": query, "$options": "i"}
    }
    
    if muse_id:
        search_query["muse_id"] = muse_id
    if platform:
        search_query["platform"] = platform
    
    cursor = db["chat_threads"].find(search_query).sort("last_ts", -1).limit(limit)
    threads = await cursor.to_list(None)
    
    for thread in threads:
        thread["id"] = str(thread["_id"])
        del thread["_id"]
    
    return threads

async def bulk_tag_fans(
    tenant_id: str,
    muse_id: str,
    user_hashes: List[str],
    tag: str
):
    """Applique un tag à plusieurs fans en une seule opération."""
    # Ajouter les tags dans fan_tags
    docs = []
    for user_hash in user_hashes:
        docs.append({
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "user_hash": user_hash,
            "tag": tag,
            "created_at": datetime.now(timezone.utc)
        })
    
    if docs:
        await db["fan_tags"].insert_many(docs, ordered=False)
    
    # Mettre à jour les threads
    await db["chat_threads"].update_many(
        {
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "user_hash": {"$in": user_hashes}
        },
        {
            "$addToSet": {"tags": tag}
        }
    )



