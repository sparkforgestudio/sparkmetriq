# api/routes/publics.py
from fastapi import APIRouter, Depends, HTTPException
from services.databases import db
from core.auths import get_current_user
from schemas.users import UserResponse
from schemas.publics import PublicContentCreate, PublicContentOut
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=PublicContentOut)
async def create_public_content(content: PublicContentCreate, user: UserResponse = Depends(get_current_user)):
    doc = content.dict()
    doc.update({
        "muse_id": user.muse_id,
        "agency_id": user.agency_id,
        "published": False,
        "created_at": datetime.utcnow()
    })
    result = await db["public_contents"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc

@router.get("/", response_model=list[PublicContentOut])
async def list_public_contents(user: UserResponse = Depends(get_current_user)):
    contents = await db["public_contents"].find({"agency_id": user.agency_id}).to_list(100)
    return [{**c, "id": str(c["_id"])} for c in contents]

@router.put("/{content_id}/publish")
async def mark_as_published(content_id: str, user: UserResponse = Depends(get_current_user)):
    result = await db["public_contents"].update_one(
        {"_id": ObjectId(content_id), "agency_id": user.agency_id},
        {"$set": {"published": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": "Content marked as published"}

@router.delete("/{content_id}")
async def delete_public_content(content_id: str, user: UserResponse = Depends(get_current_user)):
    result = await db["public_contents"].delete_one({"_id": ObjectId(content_id), "agency_id": user.agency_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": "Content deleted"}
