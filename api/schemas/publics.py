# 📁 schemas/publics.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PublicContentCreate(BaseModel):
    title: str = Field(..., example="Summer Teaser")
    description: Optional[str] = Field(None, example="Sneak peek for the summer campaign")
    platform: str = Field(..., example="instagram")
    media_url: str = Field(..., example="https://cdn.example.com/media/xyz.jpg")
    muse_id: str = Field(..., example="muse_123")
    agency_id: str = Field(..., example="agency_456")

class PublicContentResponse(PublicContentCreate):
    id: str
    created_at: datetime


# 📁 routes/publics.py
from fastapi import APIRouter, Depends, HTTPException
from services.databases import db
from core.auths import get_current_user
from schemas.publics import PublicContentCreate, PublicContentResponse
from schemas.users import UserResponse
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=PublicContentResponse)
async def create_public_content(content: PublicContentCreate, user: UserResponse = Depends(get_current_user)):
    doc = content.dict()
    doc["created_at"] = datetime.utcnow()
    result = await db["public_contents"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return PublicContentResponse(**doc)


@router.get("/", response_model=list[PublicContentResponse])
async def get_public_contents(agency_id: str, user: UserResponse = Depends(get_current_user)):
    contents = await db["public_contents"].find({"agency_id": agency_id}).to_list(100)
    return [PublicContentResponse(id=str(c["_id"]), **{k: v for k, v in c.items() if k != "_id"}) for c in contents]
