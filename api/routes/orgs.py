# api/routes/orgs.py
"""
Routes pour la gestion des entitlements par organisation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.services.orgs import get_entitlements, set_entitlements

router = APIRouter(prefix="/api/org", tags=["Organizations"])


class EntitlementsOut(BaseModel):
    """Schéma de sortie pour les entitlements."""
    org_id: str
    features: Dict[str, Any]
    updated_at: str = None
    created_at: str = None


class EntitlementsUpdate(BaseModel):
    """Schéma pour mettre à jour les entitlements."""
    features: Dict[str, Any]


@router.get("/entitlements", response_model=EntitlementsOut)
async def get_org_entitlements(
    current_user: UserResponse = Depends(get_current_user)
) -> EntitlementsOut:
    """
    Récupère les entitlements de l'organisation de l'utilisateur actuel.
    
    Returns:
        EntitlementsOut: Entitlements de l'organisation
    """
    entitlements = await get_entitlements(current_user.org_id)
    
    # Convertir les datetime en string pour la sérialisation
    result = {
        "org_id": entitlements.get("org_id", current_user.org_id),
        "features": entitlements.get("features", {})
    }
    
    if "updated_at" in entitlements:
        result["updated_at"] = entitlements["updated_at"].isoformat() if hasattr(entitlements["updated_at"], "isoformat") else str(entitlements["updated_at"])
    
    if "created_at" in entitlements:
        result["created_at"] = entitlements["created_at"].isoformat() if hasattr(entitlements["created_at"], "isoformat") else str(entitlements["created_at"])
    
    return EntitlementsOut(**result)


@router.put("/entitlements", response_model=EntitlementsOut)
async def update_org_entitlements(
    payload: EntitlementsUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> EntitlementsOut:
    """
    Met à jour les entitlements de l'organisation (admin uniquement).
    
    Args:
        payload: Nouvelles entitlements
        
    Returns:
        EntitlementsOut: Entitlements mis à jour
        
    Raises:
        HTTPException: 403 si l'utilisateur n'est pas admin
    """
    # Vérifier que l'utilisateur est admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update entitlements"
        )
    
    updated = await set_entitlements(current_user.org_id, payload.features)
    
    # Convertir les datetime en string
    result = {
        "org_id": updated.get("org_id", current_user.org_id),
        "features": updated.get("features", {})
    }
    
    if "updated_at" in updated:
        result["updated_at"] = updated["updated_at"].isoformat() if hasattr(updated["updated_at"], "isoformat") else str(updated["updated_at"])
    
    if "created_at" in updated:
        result["created_at"] = updated["created_at"].isoformat() if hasattr(updated["created_at"], "isoformat") else str(updated["created_at"])
    
    return EntitlementsOut(**result)




