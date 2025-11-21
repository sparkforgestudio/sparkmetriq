# api/routes/muses.py
"""
Routes REST pour la gestion des muses et catégories.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.muses import MuseCategory, MuseCategoryList, MuseCategoryPatch
from api.databases.databases import get_core_db

router = APIRouter(prefix="/muses", tags=["Muses"])


@router.get("/categories", response_model=MuseCategoryList)
async def list_categories(
    current_user: UserResponse = Depends(get_current_user)
) -> MuseCategoryList:
    """
    Liste les catégories de muses avec compteurs.
    
    Args:
        current_user: Utilisateur actuel
        
    Returns:
        Liste des catégories avec compteurs par catégorie
    """
    db = get_core_db()
    org_id = current_user.org_id
    
    # Récupérer les catégories actives
    cursor = (
        db["muse_categories"]
        .find({"is_active": True})
        .sort("order", 1)
    )
    cats = await cursor.to_list(length=None)
    
    items = []
    for c in cats:
        items.append(MuseCategory(
            id=c["_id"],
            label=c["label"],
            description=c.get("description"),
            is_active=c.get("is_active", True),
            order=c.get("order", 0)
        ))
    
    # Compter les muses par catégorie pour cette organisation
    pipeline = [
        {"$match": {"org_id": org_id}},
        {"$unwind": "$categories"},
        {"$group": {"_id": "$categories", "count": {"$sum": 1}}}
    ]
    
    counts_raw = await db["muses"].aggregate(pipeline).to_list(length=None)
    counts = {str(c["_id"]): c["count"] for c in counts_raw}
    
    return MuseCategoryList(items=items, counts=counts)


@router.patch("/{muse_id}/categories", status_code=status.HTTP_200_OK)
async def patch_muse_categories(
    muse_id: str,
    payload: MuseCategoryPatch,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Met à jour les catégories d'une muse.
    
    Args:
        muse_id: ID de la muse
        payload: Nouvelles catégories
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation de mise à jour
        
    Raises:
        HTTPException: 400 si catégories invalides, 404 si muse non trouvée
    """
    db = get_core_db()
    org_id = current_user.org_id
    
    # Vérifier que les catégories existent et sont actives
    if payload.categories:
        valid_cats = await db["muse_categories"].find({
            "_id": {"$in": payload.categories},
            "is_active": True
        }).to_list(length=None)
        
        valid_ids = {str(c["_id"]) for c in valid_cats}
        provided_ids = set(payload.categories)
        
        if valid_ids != provided_ids:
            invalid = provided_ids - valid_ids
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown or inactive category slugs: {', '.join(invalid)}"
            )
    
    # Mettre à jour la muse
    result = await db["muses"].update_one(
        {"_id": muse_id, "org_id": org_id},
        {"$set": {"categories": payload.categories}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Muse not found"
        )
    
    return {"ok": True}



