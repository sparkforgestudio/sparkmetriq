# api/services/observability/activity.py
"""
Service d'observabilité pour l'audit et les logs d'activité.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from bson import ObjectId
from api.databases.databases import db

async def log_activity(
    org_id: str,
    user_id: str,
    scope: str,
    action: str,
    status: str,
    extras: Optional[Dict[str, Any]] = None,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None
) -> str:
    """
    Enregistrer une activité dans les logs d'audit.
    
    Args:
        org_id: ID de l'organisation
        user_id: ID de l'utilisateur
        scope: Portée de l'action (cloudphone, otp, etc.)
        action: Action effectuée (create, update, delete, etc.)
        status: Statut de l'action (success, error, warning)
        extras: Données supplémentaires
        resource_id: ID de la ressource concernée
        resource_type: Type de ressource
    
    Returns:
        ID du document créé
    """
    activity_doc = {
        "org_id": org_id,
        "user_id": user_id,
        "scope": scope,
        "action": action,
        "status": status,
        "resource_id": resource_id,
        "resource_type": resource_type,
        "extras": extras or {},
        "timestamp": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db["activity_logs"].insert_one(activity_doc)
    return str(result.inserted_id)

async def get_activity_logs(
    org_id: str,
    scope: Optional[str] = None,
    action: Optional[str] = None,
    status: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50
) -> Dict[str, Any]:
    """
    Récupérer les logs d'activité avec filtres.
    
    Returns:
        Dict avec items, total, page, page_size
    """
    query = {"org_id": org_id}
    
    # Appliquer les filtres
    if scope:
        query["scope"] = scope
    if action:
        query["action"] = action
    if status:
        query["status"] = status
    if resource_type:
        query["resource_type"] = resource_type
    if user_id:
        query["user_id"] = user_id
    
    # Filtres de date
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
    
    # Pagination
    skip = (page - 1) * page_size
    
    # Compter le total
    total = await db["activity_logs"].count_documents(query)
    
    # Récupérer les documents
    cursor = db["activity_logs"].find(query).sort("timestamp", -1).skip(skip).limit(page_size)
    docs = await cursor.to_list(None)
    
    # Convertir les ObjectId en strings
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    
    return {
        "items": docs,
        "total": total,
        "page": page,
        "page_size": page_size
    }

async def get_activity_stats(
    org_id: str,
    days: int = 7,
    scope: Optional[str] = None
) -> Dict[str, Any]:
    """
    Récupérer les statistiques d'activité.
    
    Returns:
        Dict avec stats par scope, action, status, etc.
    """
    from datetime import timedelta
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = {
        "org_id": org_id,
        "timestamp": {"$gte": start_date}
    }
    
    if scope:
        query["scope"] = scope
    
    # Pipeline d'agrégation
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": None,
                "total_activities": {"$sum": 1},
                "by_scope": {"$push": "$scope"},
                "by_action": {"$push": "$action"},
                "by_status": {"$push": "$status"},
                "by_user": {"$push": "$user_id"}
            }
        }
    ]
    
    result = await db["activity_logs"].aggregate(pipeline).to_list(1)
    
    if not result:
        return {
            "total_activities": 0,
            "by_scope": {},
            "by_action": {},
            "by_status": {},
            "by_user": {},
            "period_days": days
        }
    
    data = result[0]
    
    # Compter les occurrences
    from collections import Counter
    
    return {
        "total_activities": data["total_activities"],
        "by_scope": dict(Counter(data["by_scope"])),
        "by_action": dict(Counter(data["by_action"])),
        "by_status": dict(Counter(data["by_status"])),
        "by_user": dict(Counter(data["by_user"])),
        "period_days": days
    }

async def ensure_activity_indexes():
    """Créer les index pour les logs d'activité."""
    await db["activity_logs"].create_index([("org_id", 1), ("timestamp", -1)])
    await db["activity_logs"].create_index([("org_id", 1), ("scope", 1), ("timestamp", -1)])
    await db["activity_logs"].create_index([("org_id", 1), ("user_id", 1), ("timestamp", -1)])
    await db["activity_logs"].create_index([("org_id", 1), ("resource_type", 1), ("resource_id", 1)])
    await db["activity_logs"].create_index([("org_id", 1), ("action", 1), ("status", 1)])

# Fonctions utilitaires pour les différents scopes

async def log_cloudphone_activity(
    org_id: str,
    user_id: str,
    action: str,
    status: str,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    extras: Optional[Dict[str, Any]] = None
) -> str:
    """Logger une activité CloudPhone."""
    return await log_activity(
        org_id=org_id,
        user_id=user_id,
        scope="cloudphone",
        action=action,
        status=status,
        resource_id=resource_id,
        resource_type=resource_type,
        extras=extras
    )

async def log_otp_activity(
    org_id: str,
    user_id: str,
    action: str,
    status: str,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    extras: Optional[Dict[str, Any]] = None
) -> str:
    """Logger une activité OTP."""
    return await log_activity(
        org_id=org_id,
        user_id=user_id,
        scope="otp",
        action=action,
        status=status,
        resource_id=resource_id,
        resource_type=resource_type,
        extras=extras
    )

async def log_system_activity(
    org_id: str,
    action: str,
    status: str,
    resource_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    extras: Optional[Dict[str, Any]] = None
) -> str:
    """Logger une activité système."""
    return await log_activity(
        org_id=org_id,
        user_id="system",
        scope="system",
        action=action,
        status=status,
        resource_id=resource_id,
        resource_type=resource_type,
        extras=extras
    )

async def log_translation_action(
    org_id: str,
    conversation_id: Optional[str],
    actor: str,
    length: int,
    note: Optional[str] = None
) -> str:
    """
    Logger une action de traduction.
    
    Args:
        org_id: ID de l'organisation
        conversation_id: ID de la conversation
        actor: Email ou identifiant de l'acteur
        length: Longueur du texte traduit
        note: Note supplémentaire
        
    Returns:
        ID du document créé
    """
    return await log_activity(
        org_id=org_id,
        user_id=actor,
        scope="translator",
        action="translate",
        status="success",
        resource_id=conversation_id,
        resource_type="conversation",
        extras={
            "length": length,
            "note": note
        }
    )

async def log_recap(
    org_id: str,
    conversation_id: str,
    actor: str,
    status: str,
    note: Optional[str] = None
) -> str:
    """
    Logger une action de génération de recap.
    
    Args:
        org_id: ID de l'organisation
        conversation_id: ID de la conversation
        actor: Email ou identifiant de l'acteur
        status: Statut (success|failed)
        note: Note supplémentaire (erreur, etc.)
        
    Returns:
        ID du document créé
    """
    return await log_activity(
        org_id=org_id,
        user_id=actor,
        scope="conversation_recap",
        action="generate",
        status=status,
        resource_id=conversation_id,
        resource_type="conversation",
        extras={
            "note": note
        }
    )

async def log_message_builder_action(
    org_id: str,
    actor: str,
    action: str,
    status: str,
    note: Optional[str] = None
) -> str:
    """
    Logger une action du Message Builder.
    
    Args:
        org_id: ID de l'organisation
        actor: Email ou identifiant de l'acteur
        action: Action effectuée (create_template, preview, create_campaign, etc.)
        status: Statut (success|failed)
        note: Note supplémentaire
        
    Returns:
        ID du document créé
    """
    return await log_activity(
        org_id=org_id,
        user_id=actor,
        scope="message_builder",
        action=action,
        status=status,
        resource_type="campaign",
        extras={
            "note": note
        }
    )
