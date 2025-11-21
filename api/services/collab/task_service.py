# api/services/collab/task_service.py
"""
Service de gestion des tâches de collaboration.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId

from api.databases.databases import get_core_db

CORE = get_core_db()


async def create_task(payload, created_by: str) -> Dict[str, Any]:
    """
    Crée une tâche de collaboration.
    
    Args:
        payload: Requête de création de tâche
        created_by: Email du créateur
        
    Returns:
        Tâche créée
    """
    now = datetime.now(timezone.utc)
    doc = {
        "org_id": payload.org_id,
        "title": payload.title,
        "description": payload.description,
        "assignees": payload.assignees or [],
        "status": payload.status,
        "priority": payload.priority,
        "due_at": payload.due_at,
        "related_muse_id": payload.related_muse_id,
        "related_thread_id": payload.related_thread_id,
        "tags": payload.tags or [],
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
        "external_ref": None
    }
    
    result = await CORE["collab_tasks"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc["_id"] = result.inserted_id
    
    return doc


async def update_task(
    org_id: str,
    task_id: str,
    payload
) -> Dict[str, Any]:
    """
    Met à jour une tâche.
    
    Args:
        org_id: ID de l'organisation
        task_id: ID de la tâche
        payload: Requête de mise à jour
        
    Returns:
        Tâche mise à jour
        
    Raises:
        LookupError: Si tâche non trouvée
    """
    now = datetime.now(timezone.utc)
    
    # Construire le patch
    patch = {}
    if payload.title is not None:
        patch["title"] = payload.title
    if payload.description is not None:
        patch["description"] = payload.description
    if payload.assignees is not None:
        patch["assignees"] = payload.assignees
    if payload.status is not None:
        patch["status"] = payload.status
    if payload.priority is not None:
        patch["priority"] = payload.priority
    if payload.due_at is not None:
        patch["due_at"] = payload.due_at
    if payload.tags is not None:
        patch["tags"] = payload.tags
    
    patch["updated_at"] = now
    
    try:
        res = await CORE["collab_tasks"].find_one_and_update(
            {"_id": ObjectId(task_id), "org_id": org_id},
            {"$set": patch},
            return_document=True
        )
    except Exception:
        res = None
    
    if not res:
        raise LookupError("Task not found")
    
    res["id"] = str(res["_id"])
    
    return res


async def list_tasks(
    org_id: str,
    status: Optional[str] = None,
    assignee: Optional[str] = None,
    limit: int = 200
) -> List[Dict[str, Any]]:
    """
    Liste les tâches d'une organisation.
    
    Args:
        org_id: ID de l'organisation
        status: Filtrer par statut (optionnel)
        assignee: Filtrer par assigné (optionnel)
        limit: Limite de résultats
        
    Returns:
        Liste des tâches
    """
    query = {"org_id": org_id}
    
    if status:
        query["status"] = status
    
    if assignee:
        query["assignees"] = assignee
    
    cursor = (
        CORE["collab_tasks"]
        .find(query)
        .sort("updated_at", -1)
        .limit(limit)
    )
    
    items = await cursor.to_list(length=limit)
    
    for it in items:
        it["id"] = str(it["_id"])
    
    return items



