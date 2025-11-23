# api/services/orgs.py
"""
Service de gestion des entitlements par organisation (tenant).
Gère les permissions d'accès aux fonctionnalités par org_id.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from api.databases.databases import db

ENTITLEMENTS_COLLECTION = "org_entitlements"


async def get_entitlements(org_id: str) -> Dict[str, Any]:
    """
    Récupère les entitlements d'une organisation.
    
    Args:
        org_id: ID de l'organisation
        
    Returns:
        Dictionnaire contenant les entitlements de l'organisation
        Si aucune entrée n'existe, retourne un dict par défaut avec features vide
    """
    doc = await db[ENTITLEMENTS_COLLECTION].find_one({"org_id": org_id})
    if doc:
        # Convertir ObjectId en string si présent
        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
        return doc
    
    # Retourner une structure par défaut si aucun entitlement n'existe
    return {
        "org_id": org_id,
        "features": {}
    }


async def set_entitlements(org_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Définit les entitlements d'une organisation.
    
    Args:
        org_id: ID de l'organisation
        features: Dictionnaire des fonctionnalités activées/désactivées
                 Format: {"cloudphone": {"active": True}, "otp": {"active": False}}
        
    Returns:
        Dictionnaire des entitlements mis à jour
    """
    payload = {
        "org_id": org_id,
        "features": features,
        "updated_at": datetime.now(timezone.utc),
    }
    
    # Ajouter created_at si c'est une nouvelle entrée
    existing = await db[ENTITLEMENTS_COLLECTION].find_one({"org_id": org_id})
    if not existing:
        payload["created_at"] = datetime.now(timezone.utc)
    
    await db[ENTITLEMENTS_COLLECTION].update_one(
        {"org_id": org_id},
        {"$set": payload},
        upsert=True,
    )
    
    return payload


async def ensure_entitlements_indexes():
    """Crée les index nécessaires pour la collection entitlements."""
    await db[ENTITLEMENTS_COLLECTION].create_index([("org_id", 1)], unique=True)
    await db[ENTITLEMENTS_COLLECTION].create_index([("updated_at", -1)])




