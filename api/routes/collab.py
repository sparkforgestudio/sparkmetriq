# api/routes/collab.py
"""
Routes REST pour le module de collaboration interne.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime, timezone

from api.core.settings import settings
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.collab import (
    CollabThreadCreate, CollabThreadOut,
    CollabMessageCreate, CollabMessageOut,
    CollabTaskCreate, CollabTaskOut, CollabTaskUpdate, CollabStatsOut
)
from api.services.collab.chat_service import create_thread, list_threads, post_message, list_messages
from api.services.collab.task_service import create_task, update_task, list_tasks
from api.services.collab.integrations import sync_to_clickup, sync_to_notion
from api.services.collab.ws import hub
from api.databases.databases import get_core_db

router = APIRouter(prefix="/collab", tags=["Collaboration"])


def _ensure_enabled():
    """Vérifie que le feature flag est activé."""
    if not settings.feature_collab_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Collaboration disabled"
        )


def _get_user_role(current_user: UserResponse) -> str:
    """
    Détermine le rôle de l'utilisateur pour les messages.
    
    Args:
        current_user: Utilisateur actuel
        
    Returns:
        Rôle (operator, supervisor, admin)
    """
    if getattr(current_user, "is_admin", False):
        return "admin"
    # TODO: Vérifier si supervisor dans les roles
    if hasattr(current_user, "roles") and "supervisor" in getattr(current_user, "roles", []):
        return "supervisor"
    return "operator"


# --- Threads ---

@router.post("/threads", response_model=CollabThreadOut, status_code=status.HTTP_201_CREATED)
async def collab_create_thread(
    payload: CollabThreadCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> CollabThreadOut:
    """
    Crée un thread de collaboration.
    
    Args:
        payload: Requête de création
        current_user: Utilisateur actuel
        
    Returns:
        Thread créé
    """
    _ensure_enabled()
    
    doc = await create_thread(payload, created_by=current_user.email)
    return CollabThreadOut(**doc)


@router.get("/threads", response_model=List[CollabThreadOut])
async def collab_list_threads(
    org_id: str = Query(..., description="ID de l'organisation"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[CollabThreadOut]:
    """
    Liste les threads de collaboration.
    
    Args:
        org_id: ID de l'organisation
        current_user: Utilisateur actuel
        
    Returns:
        Liste des threads
    """
    _ensure_enabled()
    
    items = await list_threads(org_id)
    return [CollabThreadOut(**it) for it in items]


# --- Messages ---

@router.post("/messages", response_model=CollabMessageOut, status_code=status.HTTP_201_CREATED)
async def collab_post_message(
    payload: CollabMessageCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> CollabMessageOut:
    """
    Poste un message dans un thread.
    
    Args:
        payload: Requête de création de message
        current_user: Utilisateur actuel
        
    Returns:
        Message créé
    """
    _ensure_enabled()
    
    user_role = _get_user_role(current_user)
    
    msg = await post_message(
        org_id=current_user.org_id,
        user_email=current_user.email,
        user_role=user_role,
        payload=payload
    )
    
    # Broadcast via WebSocket
    await hub.broadcast(
        current_user.org_id,
        {
            "type": "collab.message.new",
            "thread_id": msg["thread_id"],
            "message": msg
        }
    )
    
    return CollabMessageOut(**msg)


@router.get("/messages", response_model=List[CollabMessageOut])
async def collab_list_messages(
    org_id: str = Query(..., description="ID de l'organisation"),
    thread_id: str = Query(..., description="ID du thread"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[CollabMessageOut]:
    """
    Liste les messages d'un thread.
    
    Args:
        org_id: ID de l'organisation
        thread_id: ID du thread
        current_user: Utilisateur actuel
        
    Returns:
        Liste des messages
    """
    _ensure_enabled()
    
    items = await list_messages(org_id, thread_id)
    return [CollabMessageOut(**it) for it in items]


# --- Tasks ---

@router.post("/tasks", response_model=CollabTaskOut, status_code=status.HTTP_201_CREATED)
async def collab_create_task(
    payload: CollabTaskCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> CollabTaskOut:
    """
    Crée une tâche de collaboration.
    
    Args:
        payload: Requête de création
        current_user: Utilisateur actuel
        
    Returns:
        Tâche créée
    """
    _ensure_enabled()
    
    task = await create_task(payload, created_by=current_user.email)
    
    # Intégrations optionnelles
    if payload.external_sync == "clickup":
        try:
            external_ref = await sync_to_clickup(task)
            if external_ref.get("ok"):
                task["external_ref"] = external_ref
                # Mettre à jour en base
                from bson import ObjectId
                db = get_core_db()
                await db["collab_tasks"].update_one(
                    {"_id": ObjectId(task["id"])},
                    {"$set": {"external_ref": external_ref}}
                )
        except Exception as e:
            # Ne pas échouer la création si l'intégration échoue
            pass
    
    elif payload.external_sync == "notion":
        try:
            external_ref = await sync_to_notion(task)
            if external_ref.get("ok"):
                task["external_ref"] = external_ref
                # Mettre à jour en base
                from bson import ObjectId
                db = get_core_db()
                await db["collab_tasks"].update_one(
                    {"_id": ObjectId(task["id"])},
                    {"$set": {"external_ref": external_ref}}
                )
        except Exception as e:
            # Ne pas échouer la création si l'intégration échoue
            pass
    
    # Broadcast via WebSocket
    await hub.broadcast(
        task["org_id"],
        {
            "type": "collab.task.new",
            "task": task
        }
    )
    
    return CollabTaskOut(**task)


@router.patch("/tasks/{task_id}", response_model=CollabTaskOut)
async def collab_update_task(
    task_id: str,
    payload: CollabTaskUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> CollabTaskOut:
    """
    Met à jour une tâche.
    
    Args:
        task_id: ID de la tâche
        payload: Requête de mise à jour
        current_user: Utilisateur actuel
        
    Returns:
        Tâche mise à jour
    """
    _ensure_enabled()
    
    try:
        task = await update_task(current_user.org_id, task_id, payload)
        
        # Broadcast via WebSocket
        await hub.broadcast(
            task["org_id"],
            {
                "type": "collab.task.update",
                "task": task
            }
        )
        
        return CollabTaskOut(**task)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


@router.get("/tasks", response_model=List[CollabTaskOut])
async def collab_list_tasks(
    org_id: str = Query(..., description="ID de l'organisation"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    assignee: Optional[str] = Query(None, description="Filtrer par assigné"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[CollabTaskOut]:
    """
    Liste les tâches de collaboration.
    
    Args:
        org_id: ID de l'organisation
        status: Statut (optionnel)
        assignee: Assigné (optionnel)
        current_user: Utilisateur actuel
        
    Returns:
        Liste des tâches
    """
    _ensure_enabled()
    
    items = await list_tasks(org_id, status=status, assignee=assignee)
    return [CollabTaskOut(**it) for it in items]


# --- Stats ---

@router.get("/stats", response_model=CollabStatsOut)
async def collab_stats(
    org_id: str = Query(..., description="ID de l'organisation"),
    current_user: UserResponse = Depends(get_current_user)
) -> CollabStatsOut:
    """
    Statistiques de collaboration.
    
    Args:
        org_id: ID de l'organisation
        current_user: Utilisateur actuel
        
    Returns:
        Statistiques
    """
    _ensure_enabled()
    
    db = get_core_db()
    now = datetime.now(timezone.utc)
    
    # Tâches ouvertes
    total_open = await db["collab_tasks"].count_documents({
        "org_id": org_id,
        "status": {"$in": ["todo", "in_progress", "blocked"]}
    })
    
    # Tâches en retard
    overdue = await db["collab_tasks"].count_documents({
        "org_id": org_id,
        "status": {"$in": ["todo", "in_progress"]},
        "due_at": {"$lt": now, "$ne": None}
    })
    
    # Par statut
    agg1 = db["collab_tasks"].aggregate([
        {"$match": {"org_id": org_id}},
        {"$group": {"_id": "$status", "n": {"$sum": 1}}}
    ])
    by_status = {}
    async for it in agg1:
        by_status[it["_id"]] = it["n"]
    
    # Par assigné
    agg2 = db["collab_tasks"].aggregate([
        {"$match": {"org_id": org_id}},
        {"$unwind": "$assignees"},
        {"$group": {"_id": "$assignees", "n": {"$sum": 1}}}
    ])
    by_assignee = []
    async for it in agg2:
        by_assignee.append({"assignee": it["_id"], "count": it["n"]})
    
    # Par priorité
    agg3 = db["collab_tasks"].aggregate([
        {"$match": {"org_id": org_id}},
        {"$group": {"_id": "$priority", "n": {"$sum": 1}}}
    ])
    by_priority = {}
    async for it in agg3:
        by_priority[it["_id"]] = it["n"]
    
    return CollabStatsOut(
        org_id=org_id,
        open_tasks=total_open,
        overdue_tasks=overdue,
        by_status=by_status,
        by_assignee=by_assignee,
        by_priority=by_priority
    )



