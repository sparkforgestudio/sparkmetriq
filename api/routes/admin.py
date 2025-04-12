from fastapi import APIRouter, Depends
from core.dependencies import is_admin
from services.database import db

router = APIRouter()

@router.get("/dashboard")
async def admin_dashboard(admin: dict = Depends(is_admin)):
    users_count = await db["users"].count_documents({})
    return {"message": "Bienvenue Admin", "users_count": users_count}
