# api/services/talent/assignment_service.py
"""
Service de gestion des assignations et rôles.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId
from api.databases.databases import db

async def grant_role(tenant_id: str, user_id: str, role: str):
    """Accorde un rôle à un utilisateur."""
    await db["operator_roles"].update_one(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "role": role
        },
        {
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

async def revoke_role(tenant_id: str, user_id: str, role: str):
    """Révoque un rôle d'un utilisateur."""
    await db["operator_roles"].delete_one({
        "tenant_id": tenant_id,
        "user_id": user_id,
        "role": role
    })

async def get_user_roles(tenant_id: str, user_id: str) -> List[str]:
    """Récupère les rôles d'un utilisateur."""
    cursor = db["operator_roles"].find({
        "tenant_id": tenant_id,
        "user_id": user_id
    })
    
    roles = []
    for doc in await cursor.to_list(None):
        roles.append(doc["role"])
    
    return roles

async def assign_operator(
    tenant_id: str, 
    muse_id: str, 
    platform: str, 
    operator_id: str
) -> str:
    """Assigne un opérateur à une muse pour une plateforme spécifique."""
    doc = {
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "platform": platform,
        "operator_id": operator_id,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db["muse_assignments"].update_one(
        {
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "platform": platform
        },
        {
            "$set": doc
        },
        upsert=True
    )
    
    # Récupérer l'ID de l'assignation
    assignment = await db["muse_assignments"].find_one(doc)
    return str(assignment["_id"])

async def unassign_operator(tenant_id: str, muse_id: str, platform: str):
    """Retire l'assignation d'un opérateur."""
    await db["muse_assignments"].delete_one({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "platform": platform
    })

async def list_assignments(
    tenant_id: str, 
    muse_id: Optional[str] = None,
    operator_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Liste les assignations."""
    query = {"tenant_id": tenant_id}
    
    if muse_id:
        query["muse_id"] = muse_id
    if operator_id:
        query["operator_id"] = operator_id
    
    cursor = db["muse_assignments"].find(query)
    rows = await cursor.to_list(None)
    
    for r in rows:
        r["id"] = str(r["_id"])
        del r["_id"]
    
    return rows

async def get_operator_assignments(tenant_id: str, operator_id: str) -> List[Dict[str, Any]]:
    """Récupère les assignations d'un opérateur spécifique."""
    return await list_assignments(tenant_id, operator_id=operator_id)

async def get_muse_assignments(tenant_id: str, muse_id: str) -> List[Dict[str, Any]]:
    """Récupère les assignations d'une muse spécifique."""
    return await list_assignments(tenant_id, muse_id=muse_id)

async def get_assigned_operator(
    tenant_id: str, 
    muse_id: str, 
    platform: str
) -> Optional[str]:
    """Récupère l'opérateur assigné à une muse pour une plateforme."""
    assignment = await db["muse_assignments"].find_one({
        "tenant_id": tenant_id,
        "muse_id": muse_id,
        "platform": platform
    })
    
    return assignment["operator_id"] if assignment else None

async def can_access_muse_platform(
    tenant_id: str, 
    user_id: str, 
    muse_id: str, 
    platform: str
) -> bool:
    """Vérifie si un utilisateur peut accéder à une muse sur une plateforme."""
    # Vérifier si l'utilisateur est admin
    user_roles = await get_user_roles(tenant_id, user_id)
    if "admin" in user_roles:
        return True
    
    # Vérifier l'assignation spécifique
    assigned_operator = await get_assigned_operator(tenant_id, muse_id, platform)
    return assigned_operator == user_id

async def get_operators_by_role(tenant_id: str, role: str) -> List[str]:
    """Récupère les utilisateurs ayant un rôle spécifique."""
    cursor = db["operator_roles"].find({
        "tenant_id": tenant_id,
        "role": role
    })
    
    operators = []
    for doc in await cursor.to_list(None):
        operators.append(doc["user_id"])
    
    return operators

async def get_role_hierarchy(tenant_id: str) -> Dict[str, List[str]]:
    """Récupère la hiérarchie des rôles dans le tenant."""
    cursor = db["operator_roles"].find({"tenant_id": tenant_id})
    
    hierarchy = {}
    for doc in await cursor.to_list(None):
        role = doc["role"]
        user_id = doc["user_id"]
        
        if role not in hierarchy:
            hierarchy[role] = []
        hierarchy[role].append(user_id)
    
    return hierarchy

async def transfer_assignment(
    tenant_id: str,
    muse_id: str,
    platform: str,
    from_operator_id: str,
    to_operator_id: str
) -> bool:
    """Transfère une assignation d'un opérateur à un autre."""
    result = await db["muse_assignments"].update_one(
        {
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "platform": platform,
            "operator_id": from_operator_id
        },
        {
            "$set": {
                "operator_id": to_operator_id,
                "transferred_at": datetime.now(timezone.utc),
                "transferred_from": from_operator_id
            }
        }
    )
    
    return result.modified_count == 1

async def get_assignment_stats(tenant_id: str) -> Dict[str, Any]:
    """Récupère les statistiques des assignations."""
    # Compter les assignations par opérateur
    operator_stats = await db["muse_assignments"].aggregate([
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$operator_id",
            "assignments_count": {"$sum": 1},
            "platforms": {"$addToSet": "$platform"},
            "muses": {"$addToSet": "$muse_id"}
        }}
    ]).to_list(None)
    
    # Compter les assignations par muse
    muse_stats = await db["muse_assignments"].aggregate([
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$muse_id",
            "assignments_count": {"$sum": 1},
            "platforms": {"$addToSet": "$platform"},
            "operators": {"$addToSet": "$operator_id"}
        }}
    ]).to_list(None)
    
    # Compter les assignations par plateforme
    platform_stats = await db["muse_assignments"].aggregate([
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {
            "_id": "$platform",
            "assignments_count": {"$sum": 1}
        }}
    ]).to_list(None)
    
    return {
        "total_assignments": len(operator_stats),
        "operators": operator_stats,
        "muses": muse_stats,
        "platforms": platform_stats
    }

async def bulk_assign_operators(
    tenant_id: str,
    assignments: List[Dict[str, str]]
) -> List[str]:
    """Effectue des assignations en lot."""
    assignment_ids = []
    
    for assignment in assignments:
        assignment_id = await assign_operator(
            tenant_id=tenant_id,
            muse_id=assignment["muse_id"],
            platform=assignment["platform"],
            operator_id=assignment["operator_id"]
        )
        assignment_ids.append(assignment_id)
    
    return assignment_ids

async def get_unassigned_muses(tenant_id: str) -> List[Dict[str, Any]]:
    """Récupère les muses non assignées."""
    # Récupérer toutes les muses du tenant
    muses = await db["muses"].find({"tenant_id": tenant_id}).to_list(None)
    
    # Récupérer les assignations existantes
    assignments = await db["muse_assignments"].find({"tenant_id": tenant_id}).to_list(None)
    assigned_muses = {(a["muse_id"], a["platform"]) for a in assignments}
    
    # Identifier les muses non assignées
    unassigned = []
    platforms = ["instagram", "tiktok", "reddit", "twitter", "telegram", "onlyfans", "threads"]
    
    for muse in muses:
        muse_id = muse["muse_id"]
        for platform in platforms:
            if (muse_id, platform) not in assigned_muses:
                unassigned.append({
                    "muse_id": muse_id,
                    "platform": platform,
                    "muse_name": muse.get("name", muse_id)
                })
    
    return unassigned




