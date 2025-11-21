from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from bson import ObjectId

from api.databases.databases import db
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.publics import PublicContentCreate, PublicContentOut

router = APIRouter(prefix="/publics", tags=["publics"])

@router.post("/", response_model=PublicContentOut, status_code=status.HTTP_201_CREATED)
async def create_public_content(
    content: PublicContentCreate,
    user: UserResponse = Depends(get_current_user)
):
    """
    Crée un contenu public lié à la muse et à l'agence de l'utilisateur.
    """
    doc = content.dict()
    doc.update({
        "muse_id": user.email,  # ou un champ muse_id dans UserResponse
        "agency_id": user.email,  # ou user.agency_id si présent
        "published": False,
        "created_at": utcnow()
    })
    result = await db["public_contents"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc

@router.get("/", response_model=List[PublicContentOut])
async def list_public_contents(
    user: UserResponse = Depends(get_current_user)
):
    """
    Liste les contenus publics de l'agence de l'utilisateur.
    """
    records = await db["public_contents"].find({"agency_id": user.email}).to_list(100)
    return [{**r, "id": str(r["_id"])} for r in records]

@router.put("/{content_id}/publish")
async def mark_as_published(
    content_id: str,
    user: UserResponse = Depends(get_current_user)
):
    """
    Marque un contenu public comme publié.
    """
    try:
        oid = ObjectId(content_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid content ID format")
    result = await db["public_contents"].update_one(
        {"_id": oid, "agency_id": user.email},
        {"$set": {"published": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return {"message": "Content marked as published"}

@router.delete("/{content_id}")
async def delete_public_content(
    content_id: str,
    user: UserResponse = Depends(get_current_user)
):
    """
    Supprime un contenu public.
    """
    try:
        oid = ObjectId(content_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid content ID format")
    result = await db["public_contents"].delete_one({"_id": oid, "agency_id": user.email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return {"message": "Content deleted"}