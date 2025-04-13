# api/routes/funnel_config.py
from fastapi import APIRouter, Depends, HTTPException
from api.schemas.funnel_config import FunnelConfig
from services.config.funnel_config import get_config, create_or_update_config, delete_config
from api.core.auths import get_current_user
from api.schemas.users import UserResponse

router = APIRouter()

@router.get("/funnel_config", response_model=FunnelConfig)
async def read_funnel_config(
    agency_id: str,
    muse_id: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Récupère la configuration dynamique du tunnel pour une agence (et optionnellement pour une muse).
    """
    config = await get_config(agency_id, muse_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration non trouvée")
    return config

@router.post("/funnel_config", response_model=FunnelConfig)
async def upsert_funnel_config(
    config: FunnelConfig,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Crée ou met à jour la configuration dynamique du tunnel.
    """
    updated_config = await create_or_update_config(config)
    return updated_config

@router.delete("/funnel_config")
async def remove_funnel_config(
    agency_id: str,
    muse_id: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Supprime la configuration dynamique du tunnel pour une agence (et optionnellement pour une muse).
    """
    success = await delete_config(agency_id, muse_id)
    if not success:
        raise HTTPException(status_code=404, detail="Configuration non trouvée pour suppression")
    return {"detail": "Configuration supprimée avec succès"}
