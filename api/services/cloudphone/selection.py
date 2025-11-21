# api/services/cloudphone/selection.py
"""
Service de sélection et création de devices/slots.
Logique de sélection intelligente basée sur les contraintes.
"""

from typing import Dict, Any, List, Optional, Tuple
from api.databases.databases import db
from api.services.cloudphone.repository import get_device, create_device, get_profile
from api.services.cloudphone.cloudphone_client import create_device_from_profile
from api.schemas.cloudphone import DeviceOut, SlotOut, ProfileOut

async def select_or_create_device_from_profile(
    org_id: str, 
    constraints: Dict[str, Any]
) -> Tuple[DeviceOut, bool]:
    """
    Sélectionner ou créer un device basé sur les contraintes.
    Retourne (device, was_created)
    """
    # Contraintes de sélection
    area = constraints.get("area")
    lang = constraints.get("lang")
    proxy_template = constraints.get("proxy_template")
    tags = constraints.get("tags", [])
    
    # Chercher un device existant qui matche les contraintes
    query = {"org_id": org_id, "state": {"$in": ["running", "stopped"]}}
    
    if area:
        query["area"] = area
    
    if lang:
        query["lang"] = lang
    
    # Chercher d'abord les devices avec le proxy_template exact
    if proxy_template:
        query["proxy_current"] = {"$regex": proxy_template, "$options": "i"}
    
    existing_device = await db["devices"].find_one(query)
    
    if existing_device:
        existing_device["id"] = str(existing_device["_id"])
        del existing_device["_id"]
        return DeviceOut(**existing_device), False
    
    # Aucun device existant trouvé, créer un nouveau depuis un profil template
    profile = await _find_best_profile_template(org_id, constraints)
    
    if not profile:
        # Créer un device par défaut si aucun profil template
        device_data = {
            "area": area,
            "lang": lang,
            "proxy_template": proxy_template
        }
        device = await create_device(org_id, device_data)
    else:
        # Créer depuis le profil template
        device = await create_device(org_id, None, profile)
    
    # Configurer le device via le client CloudPhone
    try:
        profile_dict = {
            "name": profile.name if profile else "Default Device",
            "area": area or profile.area if profile else None,
            "lang": lang or profile.lang if profile else None,
            "proxy_template": proxy_template or profile.proxy_template if profile else None,
            "tags": tags or profile.tags if profile else []
        }
        
        cloudphone_result = await create_device_from_profile(profile_dict)
        
        # Mettre à jour le device avec les infos du CloudPhone
        await db["devices"].update_one(
            {"_id": device.id, "org_id": org_id},
            {"$set": {
                "provider_ref": cloudphone_result.get("provider_ref"),
                "fingerprint": cloudphone_result.get("fingerprint"),
                "area": cloudphone_result.get("area"),
                "lang": cloudphone_result.get("lang"),
                "proxy_current": cloudphone_result.get("proxy_current")
            }}
        )
        
        # Récupérer le device mis à jour
        updated_device = await get_device(org_id, device.id)
        return updated_device, True
        
    except Exception as e:
        # En cas d'erreur, retourner le device créé localement
        return device, True

async def _find_best_profile_template(
    org_id: str, 
    constraints: Dict[str, Any]
) -> Optional[ProfileOut]:
    """Trouver le meilleur profil template basé sur les contraintes."""
    area = constraints.get("area")
    lang = constraints.get("lang")
    tags = constraints.get("tags", [])
    
    # Chercher un profil qui matche le mieux les contraintes
    query = {"org_id": org_id}
    
    # Priorité 1: Profil avec area + lang + tags exacts
    if area and lang and tags:
        profile = await db["profiles"].find_one({
            **query,
            "area": area,
            "lang": lang,
            "tags": {"$all": tags}
        })
        if profile:
            profile["id"] = str(profile["_id"])
            del profile["_id"]
            return ProfileOut(**profile)
    
    # Priorité 2: Profil avec area + lang
    if area and lang:
        profile = await db["profiles"].find_one({
            **query,
            "area": area,
            "lang": lang
        })
        if profile:
            profile["id"] = str(profile["_id"])
            del profile["_id"]
            return ProfileOut(**profile)
    
    # Priorité 3: Profil avec area seulement
    if area:
        profile = await db["profiles"].find_one({
            **query,
            "area": area
        })
        if profile:
            profile["id"] = str(profile["_id"])
            del profile["_id"]
            return ProfileOut(**profile)
    
    # Priorité 4: Profil avec tags
    if tags:
        profile = await db["profiles"].find_one({
            **query,
            "tags": {"$in": tags}
        })
        if profile:
            profile["id"] = str(profile["_id"])
            del profile["_id"]
            return ProfileOut(**profile)
    
    # Priorité 5: Premier profil disponible
    profile = await db["profiles"].find_one(query)
    if profile:
        profile["id"] = str(profile["_id"])
        del profile["_id"]
        return ProfileOut(**profile)
    
    return None

async def ensure_slot(org_id: str, device: DeviceOut, app: str) -> SlotOut:
    """
    S'assurer qu'un slot existe pour l'app sur le device.
    Crée un slot si nécessaire.
    """
    # Chercher un slot vacant pour cette app
    existing_slot = await db["device_app_slots"].find_one({
        "org_id": org_id,
        "device_id": device.id,
        "app": app,
        "state": "vacant"
    })
    
    if existing_slot:
        existing_slot["id"] = str(existing_slot["_id"])
        del existing_slot["_id"]
        return SlotOut(**existing_slot)
    
    # Vérifier la limite de slots par app/device
    max_slots_per_app = await _get_max_slots_per_app(app)
    current_slots_count = await db["device_app_slots"].count_documents({
        "org_id": org_id,
        "device_id": device.id,
        "app": app
    })
    
    if current_slots_count >= max_slots_per_app:
        raise ValueError(f"Maximum slots limit reached for app {app} on device {device.id}")
    
    # Créer un nouveau slot
    from api.services.cloudphone.repository import create_slot
    from api.schemas.cloudphone import SlotCreate
    
    slot_data = SlotCreate(
        device_id=device.id,
        app=app,
        isolation_strategy="android_user"  # Stratégie par défaut
    )
    
    return await create_slot(org_id, slot_data)

async def _get_max_slots_per_app(app: str) -> int:
    """Récupérer la limite maximale de slots par app."""
    limits = {
        "instagram": 3,
        "telegram": 5,
        "tiktok": 2,
        "twitter": 3,
        "reddit": 4,
        "onlyfans": 2
    }
    return limits.get(app, 2)  # Limite par défaut

async def find_best_device_for_app(
    org_id: str, 
    app: str, 
    constraints: Optional[Dict[str, Any]] = None
) -> Optional[DeviceOut]:
    """Trouver le meilleur device pour une app donnée."""
    if not constraints:
        constraints = {}
    
    # Chercher un device running avec des slots disponibles
    query = {
        "org_id": org_id,
        "state": "running"
    }
    
    if constraints.get("area"):
        query["area"] = constraints["area"]
    
    devices = await db["devices"].find(query).to_list(None)
    
    for device in devices:
        # Vérifier s'il y a des slots disponibles pour cette app
        vacant_slots = await db["device_app_slots"].count_documents({
            "org_id": org_id,
            "device_id": str(device["_id"]),
            "app": app,
            "state": "vacant"
        })
        
        if vacant_slots > 0:
            device["id"] = str(device["_id"])
            del device["_id"]
            return DeviceOut(**device)
    
    return None

async def get_device_utilization(org_id: str, device_id: str) -> Dict[str, Any]:
    """Récupérer l'utilisation d'un device."""
    # Compter les slots par app
    pipeline = [
        {"$match": {"org_id": org_id, "device_id": device_id}},
        {"$group": {
            "_id": "$app",
            "total_slots": {"$sum": 1},
            "bound_slots": {
                "$sum": {"$cond": [{"$eq": ["$state", "bound"]}, 1, 0]}
            },
            "vacant_slots": {
                "$sum": {"$cond": [{"$eq": ["$state", "vacant"]}, 1, 0]}
            }
        }}
    ]
    
    slots_by_app = await db["device_app_slots"].aggregate(pipeline).to_list(None)
    
    utilization = {
        "device_id": device_id,
        "apps": {},
        "total_slots": 0,
        "bound_slots": 0,
        "vacant_slots": 0,
        "utilization_rate": 0.0
    }
    
    for app_data in slots_by_app:
        app = app_data["_id"]
        utilization["apps"][app] = {
            "total_slots": app_data["total_slots"],
            "bound_slots": app_data["bound_slots"],
            "vacant_slots": app_data["vacant_slots"],
            "utilization_rate": app_data["bound_slots"] / app_data["total_slots"] if app_data["total_slots"] > 0 else 0.0
        }
        
        utilization["total_slots"] += app_data["total_slots"]
        utilization["bound_slots"] += app_data["bound_slots"]
        utilization["vacant_slots"] += app_data["vacant_slots"]
    
    if utilization["total_slots"] > 0:
        utilization["utilization_rate"] = utilization["bound_slots"] / utilization["total_slots"]
    
    return utilization

async def recommend_device_for_new_app(
    org_id: str, 
    app: str, 
    constraints: Optional[Dict[str, Any]] = None
) -> Optional[DeviceOut]:
    """Recommander un device pour une nouvelle app."""
    if not constraints:
        constraints = {}
    
    # Chercher les devices running avec le moins d'utilisation
    devices = await db["devices"].find({
        "org_id": org_id,
        "state": "running"
    }).to_list(None)
    
    best_device = None
    best_score = float('inf')
    
    for device in devices:
        device_id = str(device["_id"])
        
        # Calculer le score d'utilisation
        utilization = await get_device_utilization(org_id, device_id)
        score = utilization["utilization_rate"]
        
        # Bonus pour les contraintes matching
        if constraints.get("area") and device.get("area") == constraints["area"]:
            score -= 0.1
        
        if constraints.get("lang") and device.get("lang") == constraints["lang"]:
            score -= 0.1
        
        # Vérifier s'il y a des slots disponibles
        vacant_slots = await db["device_app_slots"].count_documents({
            "org_id": org_id,
            "device_id": device_id,
            "app": app,
            "state": "vacant"
        })
        
        if vacant_slots > 0 and score < best_score:
            best_score = score
            best_device = device
    
    if best_device:
        best_device["id"] = str(best_device["_id"])
        del best_device["_id"]
        return DeviceOut(**best_device)
    
    return None



