# scripts/migrate_cloudphone_module.py
"""
Script de migration pour corriger les problèmes de cohérence du module CloudPhone.
"""

import asyncio
import logging
from datetime import datetime, timezone
from api.databases.databases import db
from api.config.cloudphone_config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_collection_names():
    """Corriger les noms de collections pour la cohérence."""
    logger.info("🔧 Correction des noms de collections...")
    
    # Renommer les collections si nécessaire
    collections_to_rename = {
        "profiles": "cloudphone_profiles",
        "devices": "cloudphone_devices", 
        "app_accounts": "cloudphone_app_accounts",
        "device_app_slots": "cloudphone_device_app_slots",
        "bindings_appaccount_slot": "cloudphone_bindings_appaccount_slot"
    }
    
    for old_name, new_name in collections_to_rename.items():
        try:
            # Vérifier si l'ancienne collection existe
            if old_name in await db.list_collection_names():
                # Vérifier si la nouvelle collection existe déjà
                if new_name not in await db.list_collection_names():
                    # Renommer la collection
                    await db[old_name].rename(new_name)
                    logger.info(f"✅ Collection '{old_name}' renommée en '{new_name}'")
                else:
                    logger.warning(f"⚠️ Collection '{new_name}' existe déjà, suppression de '{old_name}'")
                    await db[old_name].drop()
        except Exception as e:
            logger.error(f"❌ Erreur lors du renommage de '{old_name}': {e}")

async def create_missing_indexes():
    """Créer les index manquants."""
    logger.info("🔧 Création des index manquants...")
    
    # Index CloudPhone
    cloudphone_indexes = [
        # Profiles
        ("cloudphone_profiles", [("org_id", 1), ("name", 1)], {"unique": True}),
        ("cloudphone_profiles", [("org_id", 1), ("area", 1)]),
        ("cloudphone_profiles", [("org_id", 1), ("tags", 1)]),
        ("cloudphone_profiles", [("org_id", 1), ("provider_ref", 1)], {"sparse": True}),
        ("cloudphone_profiles", [("org_id", 1), ("created_at", -1)]),
        
        # Devices
        ("cloudphone_devices", [("org_id", 1), ("state", 1)]),
        ("cloudphone_devices", [("org_id", 1), ("area", 1)]),
        ("cloudphone_devices", [("org_id", 1), ("provider_ref", 1)], {"unique": True, "sparse": True}),
        ("cloudphone_devices", [("org_id", 1), ("created_at", -1)]),
        
        # App Accounts
        ("cloudphone_app_accounts", [("org_id", 1), ("app", 1)]),
        ("cloudphone_app_accounts", [("org_id", 1), ("username", 1)]),
        ("cloudphone_app_accounts", [("org_id", 1), ("created_at", -1)]),
        
        # Device App Slots
        ("cloudphone_device_app_slots", [("org_id", 1), ("device_id", 1), ("app", 1)]),
        ("cloudphone_device_app_slots", [("org_id", 1), ("device_id", 1), ("slot_index", 1)], {"unique": True}),
        ("cloudphone_device_app_slots", [("org_id", 1), ("state", 1)]),
        ("cloudphone_device_app_slots", [("org_id", 1), ("created_at", -1)]),
        
        # Bindings
        ("cloudphone_bindings_appaccount_slot", [("org_id", 1), ("slot_id", 1)], {"unique": True}),
        ("cloudphone_bindings_appaccount_slot", [("org_id", 1), ("app_account_id", 1)]),
        ("cloudphone_bindings_appaccount_slot", [("org_id", 1), ("created_at", -1)]),
    ]
    
    # Index OTP
    otp_indexes = [
        ("otp_sessions", [("org_id", 1), ("state", 1)]),
        ("otp_sessions", [("org_id", 1), ("created_at", -1)]),
        ("otp_sessions", [("org_id", 1), ("app", 1), ("country", 1)]),
        ("otp_sessions", [("org_id", 1), ("provider", 1)]),
        ("otp_sessions", [("provider_session_id", 1)], {"unique": True, "sparse": True}),
        ("otp_sessions", [("slot_id", 1)]),
        ("otp_sessions", [("device_id", 1)]),
    ]
    
    # Index Observabilité
    observability_indexes = [
        ("activity_logs", [("org_id", 1), ("timestamp", -1)]),
        ("activity_logs", [("org_id", 1), ("scope", 1), ("timestamp", -1)]),
        ("activity_logs", [("org_id", 1), ("user_id", 1), ("timestamp", -1)]),
        ("activity_logs", [("org_id", 1), ("resource_type", 1), ("resource_id", 1)]),
        ("activity_logs", [("org_id", 1), ("action", 1), ("status", 1)]),
        
        ("alerts", [("org_id", 1), ("created_at", -1)]),
        ("alerts", [("org_id", 1), ("status", 1)]),
        ("alerts", [("org_id", 1), ("alert_type", 1)]),
        ("alerts", [("org_id", 1), ("severity", 1)]),
        ("alerts", [("org_id", 1), ("resource_type", 1), ("resource_id", 1)]),
    ]
    
    all_indexes = cloudphone_indexes + otp_indexes + observability_indexes
    
    for collection_name, index_spec, options in all_indexes:
        try:
            await db[collection_name].create_index(index_spec, **options)
            logger.info(f"✅ Index créé: {collection_name}.{index_spec}")
        except Exception as e:
            logger.error(f"❌ Erreur création index {collection_name}.{index_spec}: {e}")

async def fix_data_consistency():
    """Corriger la cohérence des données."""
    logger.info("🔧 Correction de la cohérence des données...")
    
    # Ajouter des champs manquants aux profils
    await db["cloudphone_profiles"].update_many(
        {"org_id": {"$exists": False}},
        {"$set": {"org_id": "default_org"}}
    )
    
    # Ajouter des timestamps manquants
    await db["cloudphone_profiles"].update_many(
        {"created_at": {"$exists": False}},
        {"$set": {"created_at": datetime.now(timezone.utc)}}
    )
    
    await db["cloudphone_profiles"].update_many(
        {"updated_at": {"$exists": False}},
        {"$set": {"updated_at": datetime.now(timezone.utc)}}
    )
    
    # Corriger les types de données
    await db["cloudphone_profiles"].update_many(
        {"tags": {"$type": "string"}},
        {"$set": {"tags": []}}
    )
    
    logger.info("✅ Cohérence des données corrigée")

async def create_sample_data():
    """Créer des données d'exemple pour les tests."""
    logger.info("🔧 Création des données d'exemple...")
    
    # Profils d'exemple
    sample_profiles = [
        {
            "org_id": "demo_org",
            "name": "Profil EU Production",
            "area": "EU",
            "lang": "fr-FR",
            "proxy_template": "residential_fixed_eu_01",
            "tags": ["production", "eu"],
            "remark": "Profil de production pour l'Europe",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "org_id": "demo_org",
            "name": "Profil US Test",
            "area": "US",
            "lang": "en-US",
            "proxy_template": "residential_fixed_us_01",
            "tags": ["test", "us"],
            "remark": "Profil de test pour les États-Unis",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    # Vérifier si les profils existent déjà
    existing_profiles = await db["cloudphone_profiles"].find({"org_id": "demo_org"}).to_list(None)
    if not existing_profiles:
        await db["cloudphone_profiles"].insert_many(sample_profiles)
        logger.info("✅ Profils d'exemple créés")
    else:
        logger.info("ℹ️ Profils d'exemple déjà existants")
    
    # Configuration OTP d'exemple
    sample_otp_config = {
        "org_id": "demo_org",
        "daily_budget": 100.0,
        "monthly_budget": 2000.0,
        "max_concurrent_sessions": 10,
        "per_app_limits": {
            "instagram": 50,
            "telegram": 100,
            "tiktok": 30
        },
        "per_country_limits": {
            "US": 30,
            "FR": 20,
            "DE": 15
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    existing_config = await db["otp_budgets"].find_one({"org_id": "demo_org"})
    if not existing_config:
        await db["otp_budgets"].insert_one(sample_otp_config)
        logger.info("✅ Configuration OTP d'exemple créée")
    else:
        logger.info("ℹ️ Configuration OTP d'exemple déjà existante")

async def validate_migration():
    """Valider la migration."""
    logger.info("🔍 Validation de la migration...")
    
    # Vérifier les collections
    collections = await db.list_collection_names()
    expected_collections = [
        "cloudphone_profiles",
        "cloudphone_devices",
        "cloudphone_app_accounts",
        "cloudphone_device_app_slots",
        "cloudphone_bindings_appaccount_slot",
        "otp_sessions",
        "otp_providers",
        "otp_pools",
        "otp_budgets",
        "activity_logs",
        "alerts"
    ]
    
    missing_collections = [col for col in expected_collections if col not in collections]
    if missing_collections:
        logger.warning(f"⚠️ Collections manquantes: {missing_collections}")
    else:
        logger.info("✅ Toutes les collections sont présentes")
    
    # Vérifier les index
    for collection_name in expected_collections:
        if collection_name in collections:
            indexes = await db[collection_name].list_indexes().to_list(None)
            logger.info(f"📊 {collection_name}: {len(indexes)} index")
    
    # Vérifier les données
    profile_count = await db["cloudphone_profiles"].count_documents({})
    logger.info(f"📊 Profils: {profile_count}")
    
    session_count = await db["otp_sessions"].count_documents({})
    logger.info(f"📊 Sessions OTP: {session_count}")

async def main():
    """Fonction principale de migration."""
    logger.info("🚀 Début de la migration du module CloudPhone...")
    
    try:
        await fix_collection_names()
        await create_missing_indexes()
        await fix_data_consistency()
        await create_sample_data()
        await validate_migration()
        
        logger.info("✅ Migration terminée avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la migration: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())



