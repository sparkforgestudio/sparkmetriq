from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from datetime import datetime
from bson import ObjectId

from api.databases.databases import db
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.ppv import PpvCreate, PpvResponse

router = APIRouter(prefix="/ppv", tags=["ppv"])

@router.post("/", response_model=PpvResponse, status_code=status.HTTP_201_CREATED)
async def create_ppv(
    ppv: PpvCreate,
    user: UserResponse = Depends(get_current_user)
):
    """
    Crée un contenu PPV.
    """
    data = ppv.dict()
    data.update({
        "created_at": utcnow(),
        "created_by": user.email
    })
    result = await db["ppv_contents"].insert_one(data)
    data["id"] = str(result.inserted_id)
    return data

@router.get("/", response_model=List[PpvResponse])
async def list_ppv(user: UserResponse = Depends(get_current_user)):
    """
    Liste tous les contenus PPV.
    """
    records = await db["ppv_contents"].find().to_list(100)
    result = []
    for r in records:
        r["id"] = str(r.get("_id"))
        result.append(r)
    return result

@router.get("/{ppv_id}", response_model=PpvResponse)
async def get_ppv(
    ppv_id: str,
    user: UserResponse = Depends(get_current_user)
):
    """
    Récupère un contenu PPV par ID.
    """
    try:
        oid = ObjectId(ppv_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid PPV ID format")
    record = await db["ppv_contents"].find_one({"_id": oid})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PPV content not found")
    record["id"] = str(record.get("_id"))
    return record

@router.put("/{ppv_id}", response_model=PpvResponse)
async def update_ppv(
    ppv_id: str,
    ppv: PpvCreate,
    user: UserResponse = Depends(get_current_user)
):
    """
    Met à jour un contenu PPV existant.
    """
    try:
        oid = ObjectId(ppv_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid PPV ID format")
    data = ppv.dict()
    data["updated_at"] = utcnow()
    result = await db["ppv_contents"].update_one({"_id": oid}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PPV content not found")
    updated = await db["ppv_contents"].find_one({"_id": oid})
    updated["id"] = str(updated.get("_id"))
    return updated

@router.delete("/{ppv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ppv(
    ppv_id: str,
    user: UserResponse = Depends(get_current_user)
):
    """
    Supprime un contenu PPV par ID.
    """
    try:
        oid = ObjectId(ppv_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid PPV ID format")
    result = await db["ppv_contents"].delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PPV content not found")
    # Pas de contenu retourné pour DELETE 204
