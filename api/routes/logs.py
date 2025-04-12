from fastapi import APIRouter, Depends, Query
from api.services.databases import db
from core.auths import is_operator_or_admin
from schemas.users import UserResponse
from datetime import datetime

router = APIRouter()

@router.get("/")
async def list_logs(
    agency_id: str = Query(...),
    muse_id: str = Query(None),
    platform: str = Query(None),
    status: str = Query(None),
    limit: int = Query(50, ge=1, le=500),
    current_user: UserResponse = Depends(is_operator_or_admin)
):
    filters = {"agency_id": agency_id}
    if muse_id:
        filters["muse_id"] = muse_id
    if platform:
        filters["platform"] = platform
    if status:
        filters["status"] = status

    logs = await db["platform_logs"].find(filters).sort("timestamp", -1).limit(limit).to_list(None)

    return [{
        "platform": log.get("platform"),
        "muse_id": log.get("muse_id"),
        "status": log.get("status"),
        "message": log.get("message"),
        "timestamp": log.get("timestamp"),
        "metadata": log.get("metadata", {}),
    } for log in logs]
