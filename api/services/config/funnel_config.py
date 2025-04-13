# services/config/funnel_config.py
from api.schemas.funnel_config import FunnelConfig
from services.databases import db  # Adaptez l'import en fonction de votre architecture

CONFIG_COLLECTION = "funnel_configs"

async def get_config(agency_id: str, muse_id: str = None) -> FunnelConfig:
    query = {"agency_id": agency_id}
    if muse_id:
        query["muse_id"] = muse_id
    else:
        query["muse_id"] = {"$exists": False}
    
    config_data = await db[CONFIG_COLLECTION].find_one(query)
    if config_data:
        return FunnelConfig(**config_data)
    else:
        return None

async def create_or_update_config(config: FunnelConfig) -> FunnelConfig:
    query = {"agency_id": config.agency_id}
    if config.muse_id:
        query["muse_id"] = config.muse_id
    else:
        query["muse_id"] = {"$exists": False}
    
    update_data = config.dict()
    # Vous pouvez ajouter ici un champ "updated_at" si souhaité
    await db[CONFIG_COLLECTION].update_one(query, {"$set": update_data}, upsert=True)
    return config

async def delete_config(agency_id: str, muse_id: str = None) -> bool:
    query = {"agency_id": agency_id}
    if muse_id:
        query["muse_id"] = muse_id
    else:
        query["muse_id"] = {"$exists": False}
    
    result = await db[CONFIG_COLLECTION].delete_one(query)
    return result.deleted_count > 0
