# api/services/cloudphone/repository.py
"""
Repository CloudPhone avec Motor/MongoDB.
Collections: profiles, devices, app_accounts, device_app_slots, bindings_appaccount_slot
Approche form-first avec index optimisés.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from bson import ObjectId
from api.databases.databases import get_core_db

# Utiliser la base Core pour CloudPhone
db = get_core_db()
from api.schemas.cloudphone import (
    ProfileCreate, ProfileUpdate, ProfileOut, ProfileListResponse,
    DeviceCreate, DeviceOut, DeviceListResponse,
    AppAccountIn, AppAccountOut, AppAccountListResponse,
    SlotCreate, SlotOut, SlotListResponse,
    ProfileSearchParams, DeviceSearchParams, SlotSearchParams
)

async def ensure_cloudphone_indexes():
    """Créer les index MongoDB pour CloudPhone."""
    # Profiles - index unique sur (org_id, name) pour éviter les doublons formulaire
    await db["profiles"].create_index([("org_id", 1), ("name", 1)], unique=True)
    await db["profiles"].create_index([("org_id", 1), ("area", 1)])
    await db["profiles"].create_index([("org_id", 1), ("tags", 1)])
    await db["profiles"].create_index([("org_id", 1), ("provider_ref", 1)], sparse=True)
    
    # Devices
    await db["devices"].create_index([("org_id", 1), ("state", 1)])
    await db["devices"].create_index([("org_id", 1), ("area", 1)])
    await db["devices"].create_index([("org_id", 1), ("provider_ref", 1)], unique=True, sparse=True)
    
    # App Accounts
    await db["app_accounts"].create_index([("org_id", 1), ("app", 1)])
    await db["app_accounts"].create_index([("org_id", 1), ("username", 1)])
    
    # Device App Slots
    await db["device_app_slots"].create_index([("org_id", 1), ("device_id", 1), ("app", 1)])
    await db["device_app_slots"].create_index([("org_id", 1), ("device_id", 1), ("slot_index", 1)], unique=True)
    await db["device_app_slots"].create_index([("org_id", 1), ("state", 1)])
    
    # Bindings
    await db["bindings_appaccount_slot"].create_index([("org_id", 1), ("slot_id", 1)], unique=True)
    await db["bindings_appaccount_slot"].create_index([("org_id", 1), ("app_account_id", 1)])

# ---------- PROFILES (FORM FIRST) ----------

async def create_profile(org_id: str, profile_data: ProfileCreate) -> ProfileOut:
    """Créer un profil depuis le formulaire."""
    now = datetime.now(timezone.utc)
    doc = {
        "org_id": org_id,
        "name": profile_data.name,
        "area": profile_data.area,
        "lang": profile_data.lang,
        "proxy_template": profile_data.proxy_template,
        "tags": profile_data.tags,
        "remark": profile_data.remark,
        "provider_ref": profile_data.provider_ref,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db["profiles"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return ProfileOut(**doc)

async def get_profile(org_id: str, profile_id: str) -> Optional[ProfileOut]:
    """Récupérer un profil par ID."""
    doc = await db["profiles"].find_one({
        "_id": ObjectId(profile_id),
        "org_id": org_id
    })
    
    if not doc:
        return None
    
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return ProfileOut(**doc)

async def update_profile(org_id: str, profile_id: str, update_data: ProfileUpdate) -> Optional[ProfileOut]:
    """Mettre à jour un profil."""
    update_fields = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if not update_fields:
        return await get_profile(org_id, profile_id)
    
    update_fields["updated_at"] = datetime.now(timezone.utc)
    
    result = await db["profiles"].update_one(
        {"_id": ObjectId(profile_id), "org_id": org_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        return None
    
    return await get_profile(org_id, profile_id)

async def delete_profile(org_id: str, profile_id: str) -> bool:
    """Supprimer un profil."""
    result = await db["profiles"].delete_one({
        "_id": ObjectId(profile_id),
        "org_id": org_id
    })
    return result.deleted_count > 0

async def list_profiles(org_id: str, params: ProfileSearchParams) -> ProfileListResponse:
    """Lister les profils avec filtres."""
    query = {"org_id": org_id}
    
    # Filtres
    if params.search:
        query["$or"] = [
            {"name": {"$regex": params.search, "$options": "i"}},
            {"remark": {"$regex": params.search, "$options": "i"}}
        ]
    
    if params.area:
        query["area"] = params.area
    
    if params.tag:
        query["tags"] = {"$in": [params.tag]}
    
    # Pagination
    skip = (params.page - 1) * params.page_size
    
    # Compter le total
    total = await db["profiles"].count_documents(query)
    
    # Récupérer les documents
    cursor = db["profiles"].find(query).sort("created_at", -1).skip(skip).limit(params.page_size)
    docs = await cursor.to_list(None)
    
    # Convertir en ProfileOut
    profiles = []
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        profiles.append(ProfileOut(**doc))
    
    return ProfileListResponse(
        items=profiles,
        total=total,
        page=params.page,
        page_size=params.page_size
    )

# ---------- DEVICES ----------

async def create_device(org_id: str, device_data: DeviceCreate, profile: Optional[ProfileOut] = None) -> DeviceOut:
    """Créer un device."""
    now = datetime.now(timezone.utc)
    
    doc = {
        "org_id": org_id,
        "provider_ref": None,  # Sera rempli par le client CloudPhone
        "state": "stopped",
        "area": profile.area if profile else None,
        "lang": profile.lang if profile else None,
        "proxy_current": None,
        "fingerprint": None,
        "slots_count": 0,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db["devices"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return DeviceOut(**doc)

async def get_device(org_id: str, device_id: str) -> Optional[DeviceOut]:
    """Récupérer un device par ID."""
    doc = await db["devices"].find_one({
        "_id": ObjectId(device_id),
        "org_id": org_id
    })
    
    if not doc:
        return None
    
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return DeviceOut(**doc)

async def update_device(org_id: str, device_id: str, update_data: Dict[str, Any]) -> Optional[DeviceOut]:
    """Mettre à jour un device."""
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db["devices"].update_one(
        {"_id": ObjectId(device_id), "org_id": org_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        return None
    
    return await get_device(org_id, device_id)

async def list_devices(org_id: str, params: DeviceSearchParams) -> DeviceListResponse:
    """Lister les devices avec filtres."""
    query = {"org_id": org_id}
    
    if params.area:
        query["area"] = params.area
    
    if params.state:
        query["state"] = params.state
    
    # Pagination
    skip = (params.page - 1) * params.page_size
    
    # Compter le total
    total = await db["devices"].count_documents(query)
    
    # Récupérer les documents
    cursor = db["devices"].find(query).sort("created_at", -1).skip(skip).limit(params.page_size)
    docs = await cursor.to_list(None)
    
    # Convertir en DeviceOut
    devices = []
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        devices.append(DeviceOut(**doc))
    
    return DeviceListResponse(
        items=devices,
        total=total,
        page=params.page,
        page_size=params.page_size
    )

# ---------- APP ACCOUNTS ----------

async def create_app_account(org_id: str, account_data: AppAccountIn) -> AppAccountOut:
    """Créer un compte d'application."""
    now = datetime.now(timezone.utc)
    doc = {
        "org_id": org_id,
        "app": account_data.app,
        "username": account_data.username,
        "status": account_data.status,
        "risk_level": account_data.risk_level,
        "last_login_at": account_data.last_login_at,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db["app_accounts"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return AppAccountOut(**doc)

async def get_app_account(org_id: str, account_id: str) -> Optional[AppAccountOut]:
    """Récupérer un compte d'application."""
    doc = await db["app_accounts"].find_one({
        "_id": ObjectId(account_id),
        "org_id": org_id
    })
    
    if not doc:
        return None
    
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return AppAccountOut(**doc)

async def list_app_accounts(org_id: str, app: Optional[str] = None) -> AppAccountListResponse:
    """Lister les comptes d'application."""
    query = {"org_id": org_id}
    
    if app:
        query["app"] = app
    
    cursor = db["app_accounts"].find(query).sort("created_at", -1)
    docs = await cursor.to_list(None)
    
    accounts = []
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        accounts.append(AppAccountOut(**doc))
    
    return AppAccountListResponse(items=accounts, total=len(accounts))

# ---------- SLOTS ----------

async def create_slot(org_id: str, slot_data: SlotCreate) -> SlotOut:
    """Créer un slot pour une app sur un device."""
    # Calculer le prochain slot_index pour cette app sur ce device
    existing_slots = await db["device_app_slots"].find({
        "org_id": org_id,
        "device_id": slot_data.device_id,
        "app": slot_data.app
    }).to_list(None)
    
    slot_index = len(existing_slots)
    
    now = datetime.now(timezone.utc)
    doc = {
        "org_id": org_id,
        "device_id": slot_data.device_id,
        "app": slot_data.app,
        "slot_index": slot_index,
        "isolation_strategy": slot_data.isolation_strategy,
        "proxy_override": slot_data.proxy_override,
        "state": "vacant",
        "bound_app_account_id": None,
        "created_at": now,
        "updated_at": now
    }
    
    result = await db["device_app_slots"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    
    # Mettre à jour le compteur de slots du device
    await db["devices"].update_one(
        {"_id": ObjectId(slot_data.device_id), "org_id": org_id},
        {"$inc": {"slots_count": 1}}
    )
    
    return SlotOut(**doc)

async def get_slot(org_id: str, slot_id: str) -> Optional[SlotOut]:
    """Récupérer un slot par ID."""
    doc = await db["device_app_slots"].find_one({
        "_id": ObjectId(slot_id),
        "org_id": org_id
    })
    
    if not doc:
        return None
    
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return SlotOut(**doc)

async def update_slot(org_id: str, slot_id: str, update_data: Dict[str, Any]) -> Optional[SlotOut]:
    """Mettre à jour un slot."""
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db["device_app_slots"].update_one(
        {"_id": ObjectId(slot_id), "org_id": org_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        return None
    
    return await get_slot(org_id, slot_id)

async def list_slots(org_id: str, params: SlotSearchParams) -> SlotListResponse:
    """Lister les slots avec filtres."""
    query = {"org_id": org_id}
    
    if params.device_id:
        query["device_id"] = params.device_id
    
    if params.app:
        query["app"] = params.app
    
    if params.state:
        query["state"] = params.state
    
    # Pagination
    skip = (params.page - 1) * params.page_size
    
    # Compter le total
    total = await db["device_app_slots"].count_documents(query)
    
    # Récupérer les documents
    cursor = db["device_app_slots"].find(query).sort("created_at", -1).skip(skip).limit(params.page_size)
    docs = await cursor.to_list(None)
    
    # Convertir en SlotOut
    slots = []
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        slots.append(SlotOut(**doc))
    
    return SlotListResponse(
        items=slots,
        total=total,
        page=params.page,
        page_size=params.page_size
    )

# ---------- BINDINGS ----------

async def bind_slot_to_account(org_id: str, slot_id: str, app_account_id: str) -> bool:
    """Lier un slot à un compte d'application."""
    # Vérifier que le slot existe et est vacant
    slot = await get_slot(org_id, slot_id)
    if not slot or slot.state != "vacant":
        return False
    
    # Vérifier que le compte existe
    account = await get_app_account(org_id, app_account_id)
    if not account:
        return False
    
    now = datetime.now(timezone.utc)
    
    # Créer le binding
    binding_doc = {
        "org_id": org_id,
        "slot_id": slot_id,
        "app_account_id": app_account_id,
        "created_at": now
    }
    
    await db["bindings_appaccount_slot"].insert_one(binding_doc)
    
    # Mettre à jour le slot
    await update_slot(org_id, slot_id, {
        "state": "bound",
        "bound_app_account_id": app_account_id
    })
    
    return True

async def unbind_slot(org_id: str, slot_id: str) -> bool:
    """Délier un slot."""
    # Supprimer le binding
    result = await db["bindings_appaccount_slot"].delete_one({
        "org_id": org_id,
        "slot_id": slot_id
    })
    
    if result.deleted_count == 0:
        return False
    
    # Mettre à jour le slot
    await update_slot(org_id, slot_id, {
        "state": "vacant",
        "bound_app_account_id": None
    })
    
    return True

async def get_slot_binding(org_id: str, slot_id: str) -> Optional[Dict[str, Any]]:
    """Récupérer le binding d'un slot."""
    binding = await db["bindings_appaccount_slot"].find_one({
        "org_id": org_id,
        "slot_id": slot_id
    })
    
    return binding

# ---------- UTILITAIRES ----------

async def get_device_metrics(org_id: str) -> Dict[str, Any]:
    """Récupérer les métriques des devices."""
    pipeline = [
        {"$match": {"org_id": org_id}},
        {"$group": {
            "_id": "$state",
            "count": {"$sum": 1}
        }}
    ]
    
    state_counts = await db["devices"].aggregate(pipeline).to_list(None)
    
    metrics = {
        "total_devices": 0,
        "running_devices": 0,
        "stopped_devices": 0,
        "error_devices": 0,
        "banned_devices": 0
    }
    
    for state_count in state_counts:
        state = state_count["_id"]
        count = state_count["count"]
        metrics["total_devices"] += count
        
        if state == "running":
            metrics["running_devices"] = count
        elif state == "stopped":
            metrics["stopped_devices"] = count
        elif state == "error":
            metrics["error_devices"] = count
        elif state == "banned":
            metrics["banned_devices"] = count
    
    # Métriques des slots
    total_slots = await db["device_app_slots"].count_documents({"org_id": org_id})
    bound_slots = await db["device_app_slots"].count_documents({
        "org_id": org_id,
        "state": "bound"
    })
    
    metrics.update({
        "total_slots": total_slots,
        "bound_slots": bound_slots,
        "vacant_slots": total_slots - bound_slots
    })
    
    return metrics

async def find_profile_by_name(org_id: str, name: str) -> Optional[ProfileOut]:
    """Trouver un profil par nom (pour éviter les doublons)."""
    doc = await db["profiles"].find_one({
        "org_id": org_id,
        "name": name
    })
    
    if not doc:
        return None
    
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return ProfileOut(**doc)
