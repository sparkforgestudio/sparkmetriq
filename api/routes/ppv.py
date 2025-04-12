from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from services.databases import db
from core.auths import get_current_user
from schemas.users import UserResponse
from schemas.ppv import PPVContentCreate, PPVContentPublic

router = APIRouter()


# 🔹 Créer un contenu PPV
@router.post("/", response_model=PPVContentPublic)
async def create_ppv_content(
    content: PPVContentCreate,
    user: UserResponse = Depends(get_current_user)
):
    doc = content.dict()
    doc["created_at"] = datetime.utcnow()
    doc["creator_id"] = user.id
    result = await db["ppv_contents"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc


# 🔹 Récupérer tous les contenus PPV d’une agence
@router.get("/", response_model=list[PPVContentPublic])
async def get_ppv_contents(
    agency_id: str,
    user: UserResponse = Depends(get_current_user)
):
    contents = await db["ppv_contents"].find({"agency_id": agency_id}).to_list(100)
    return [{**c, "id": str(c["_id"])} for c in contents]


# 🔹 Récupérer un contenu PPV par ID
@router.get("/{id}", response_model=PPVContentPublic)
async def get_ppv_by_id(
    id: str,
    user: UserResponse = Depends(get_current_user)
):
    content = await db["ppv_contents"].find_one({"_id": ObjectId(id)})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return {**content, "id": str(content["_id"])}


# 🔹 Mettre à jour un contenu PPV
@router.put("/{id}", response_model=PPVContentPublic)
async def update_ppv_content(
    id: str,
    content_update: PPVContentCreate,
    user: UserResponse = Depends(get_current_user)
):
    update_data = content_update.dict()
    result = await db["ppv_contents"].update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    content = await db["ppv_contents"].find_one({"_id": ObjectId(id)})
    return {**content, "id": str(content["_id"])}


# 🔹 Supprimer un contenu PPV
@router.delete("/{id}")
async def delete_ppv_content(
    id: str,
    user: UserResponse = Depends(get_current_user)
):
    result = await db["ppv_contents"].delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": f"Content with ID {id} deleted successfully"}
