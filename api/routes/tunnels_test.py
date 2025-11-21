from fastapi import APIRouter, HTTPException, Depends
from typing import List
from api.schemas.tunnels import TunnelCreate, TunnelResponse
from api.databases.databases import db
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter()


@router.post("/", response_model=TunnelResponse)
async def create_tunnel(tunnel: TunnelCreate, user: UserResponse = Depends(get_current_user)):
    """
    Crée un nouveau tunnel en enregistrant les données dans la collection "tunnels".
    La date de création est fixée à l'heure UTC et l'ID généré est converti en chaîne.
    """
    data = tunnel.model_dump()
    data["created_at"] = datetime.now(timezone.utc)
    result = await db["tunnels"].insert_one(data)
    data["id"] = str(result.inserted_id)
    return data


@router.get("/by-muse/{muse_id}", response_model=List[TunnelResponse])
async def get_tunnels_by_muse(muse_id: str, user: UserResponse = Depends(get_current_user)):
    """
    Récupère les tunnels associés à une muse spécifique.
    Pour chaque tunnel, l'ID Mongo est converti en chaîne.
    """
    tunnels = await db["tunnels"].find({"muse_id": muse_id}).to_list(100)
    for tunnel in tunnels:
        tunnel["id"] = str(tunnel["_id"])
    return tunnels


@router.put("/{tunnel_id}/activate")
async def activate_tunnel(tunnel_id: str, user: UserResponse = Depends(get_current_user)):
    """
    Active un tunnel en désactivant d'abord tous les tunnels de la muse,
    puis en activant le tunnel correspondant à l'ID fourni.
    Si aucun tunnel n'est trouvé, une erreur 404 est renvoyée.
    """
    # Désactiver tous les tunnels de la muse de l'utilisateur
    await db["tunnels"].update_many(
        {"muse_id": user.muse_id},
        {"$set": {"is_active": False}}
    )
    
    # Activer le tunnel ciblé
    updated = await db["tunnels"].update_one(
        {"_id": ObjectId(tunnel_id)},
        {"$set": {"is_active": True}}
    )
    if updated.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tunnel not found")
    return {"message": "Tunnel activé avec succès"}
