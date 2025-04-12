from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from core.auths import get_current_user, has_role
from schemas.users import UserResponse, UserRole
from services.database import db

router = APIRouter()

# 🔍 GET /scheduler/ : Lister les tâches planifiées (filtrage + pagination)
@router.get("/", response_model=List[dict])
async def list_scheduled_tasks(
    agency_id: Optional[str] = Query(None),
    muse_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    current_user: UserResponse = Depends(has_role(UserRole.operator))
):
    query = {}
    if agency_id:
        query["agency_id"] = agency_id
    if muse_id:
        query["muse_id"] = muse_id
    if status:
        query["status"] = status

    tasks_cursor = db["scheduled_tasks"].find(query).sort("scheduled_at", -1).skip(skip).limit(limit)
    tasks = await tasks_cursor.to_list(length=limit)

    # Transformation ObjectId -> str pour compatibilité JSON
    for task in tasks:
        task["id"] = str(task["_id"])
        del task["_id"]

    return tasks
