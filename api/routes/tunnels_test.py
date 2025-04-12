from fastapi import APIRouter, HTTPException, Depends
from schemas.tunnels import TunnelCreate, TunnelResponse
from api.services.databases import db
from core.auths import get_current_user
from schemas.users import UserResponse
from datetime import datetime
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=TunnelResponse)
async def create_tunnel(tunnel: TunnelCreate, user: UserResponse = Depends(get_current_user)):
    data = tunnel.dict()
    data["created_at"] = datetime.utcnow()
    result = await db["tunnels"].insert_one(data)
    data["id"] = str(result.inserted_id)
    return data

@router.get("/by-muse/{muse_id}", response_model=List[TunnelResponse])
async def get_tunnels_by_muse(muse_id: str, user: UserResponse = Depends(get_current_user)):
    tunnels = await db["tunnels"].find({"muse_id": muse_id}).to_list(100)
    for tunnel in tunnels:
        tunnel["id"] = str(tunnel["_id"])
    return tunnels

@router.put("/{tunnel_id}/activate")
async def activate_tunnel(tunnel_id: str, user: UserResponse = Depends(get_current_user)):
    result = await db["tunnels"].update_many(
        {"muse_id": user.muse_id}, {"$set": {"is_active": False}}
    )
    updated = await db["tunnels"].update_one(
        {"_id": ObjectId(tunnel_id)}, {"$set": {"is_active": True}}
    )
    if updated.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tunnel not found")
    return {"message": "Tunnel activé avec succès"}
