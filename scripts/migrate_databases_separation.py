# scripts/migrate_databases_separation.py
"""
Script de migration pour séparer les données entre base Core et base BI.
À exécuter une seule fois pour migrer les données existantes.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any

from api.databases.databases import (
    client_core, client_bi, db_core, db_bi,
    get_core_db, get_bi_db, ensure_all_indexes
)


async def migrate_data():
    """Migre les données de l'ancienne base vers les nouvelles bases Core et BI."""
    print("🚀 Début de la migration des bases de données...")
    
    # Vérifier que les bases existent
    try:
        await client_core.admin.command('ping')
        await client_bi.admin.command('ping')
        print("✅ Connexions aux bases de données OK")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return
    
    # Créer les index
    print("📊 Création des index...")
    await ensure_all_indexes()
    
    # Migration des collections Core
    await migrate_core_collections()
    
    # Migration des collections BI
    await migrate_bi_collections()
    
    print("✅ Migration terminée avec succès!")


async def migrate_core_collections():
    """Migre les collections vers la base Core."""
    print("📦 Migration des collections Core...")
    
    # Collections à migrer vers Core
    core_collections = [
        'users', 'profiles', 'devices', 'device_app_slots', 'bindings_appaccount_slot',
        'otp_sessions', 'org_entitlements', 'chat_messages', 'payments',
        'tunnels', 'ppv_logs', 'conversation_daily', 'revenue_daily', 'ppv_daily'
    ]
    
    # Source: ancienne base (musemgmtdb)
    source_db = client_core['musemgmtdb']  # ou l'ancienne base
    
    for collection_name in core_collections:
        try:
            # Vérifier si la collection existe dans la source
            if collection_name not in await source_db.list_collection_names():
                print(f"⚠️ Collection {collection_name} n'existe pas dans la source")
                continue
            
            # Compter les documents
            count = await source_db[collection_name].count_documents({})
            if count == 0:
                print(f"ℹ️ Collection {collection_name} vide, ignorée")
                continue
            
            print(f"📋 Migration de {collection_name} ({count} documents)...")
            
            # Migrer par batch pour éviter les timeouts
            batch_size = 1000
            total_migrated = 0
            
            async for batch in source_db[collection_name].find().batch_size(batch_size):
                if batch:
                    await db_core[collection_name].insert_many(batch)
                    total_migrated += len(batch)
                    print(f"  ✅ {total_migrated}/{count} documents migrés")
            
            print(f"✅ {collection_name} migrée: {total_migrated} documents")
            
        except Exception as e:
            print(f"❌ Erreur migration {collection_name}: {e}")


async def migrate_bi_collections():
    """Migre les collections vers la base BI."""
    print("📊 Migration des collections BI...")
    
    # Collections à migrer vers BI
    bi_collections = [
        'events_funnel', 'scheduled_drafts', 'scheduled_jobs', 'publish_logs',
        'ab_tests', 'recycle_policies', 'ai_action_plans', 'ai_alerts',
        'ai_collab_suggestions', 'ai_reco_history', 'trends_cache',
        'chat_threads', 'fan_tags', 'fan_notes', 'operator_roles',
        'muse_assignments', 'audit_events', 'muse_metrics_daily',
        'integration_hooks', 'rag_documents', 'rag_embeddings',
        'scraped_contents', 'creator_analytics', 'platform_metrics'
    ]
    
    # Source: ancienne base
    source_db = client_core['musemgmtdb']
    
    for collection_name in bi_collections:
        try:
            # Vérifier si la collection existe dans la source
            if collection_name not in await source_db.list_collection_names():
                print(f"⚠️ Collection {collection_name} n'existe pas dans la source")
                continue
            
            # Compter les documents
            count = await source_db[collection_name].count_documents({})
            if count == 0:
                print(f"ℹ️ Collection {collection_name} vide, ignorée")
                continue
            
            print(f"📋 Migration de {collection_name} ({count} documents)...")
            
            # Migrer par batch
            batch_size = 1000
            total_migrated = 0
            
            async for batch in source_db[collection_name].find().batch_size(batch_size):
                if batch:
                    await db_bi[collection_name].insert_many(batch)
                    total_migrated += len(batch)
                    print(f"  ✅ {total_migrated}/{count} documents migrés")
            
            print(f"✅ {collection_name} migrée: {total_migrated} documents")
            
        except Exception as e:
            print(f"❌ Erreur migration {collection_name}: {e}")


async def verify_migration():
    """Vérifie que la migration s'est bien passée."""
    print("🔍 Vérification de la migration...")
    
    # Collections Core
    core_collections = ['users', 'profiles', 'devices', 'otp_sessions', 'chat_messages']
    for collection in core_collections:
        count = await db_core[collection].count_documents({})
        print(f"📦 Core.{collection}: {count} documents")
    
    # Collections BI
    bi_collections = ['events_funnel', 'ai_action_plans', 'rag_documents']
    for collection in bi_collections:
        count = await db_bi[collection].count_documents({})
        print(f"📊 BI.{collection}: {count} documents")


async def cleanup_old_data():
    """Nettoie les données de l'ancienne base (optionnel)."""
    print("🧹 Nettoyage de l'ancienne base...")
    
    # ATTENTION: Ne pas exécuter en production sans sauvegarde!
    response = input("⚠️ Voulez-vous supprimer les données de l'ancienne base? (oui/non): ")
    if response.lower() != 'oui':
        print("ℹ️ Nettoyage annulé")
        return
    
    # Supprimer les collections migrées
    source_db = client_core['musemgmtdb']
    
    collections_to_clean = [
        'users', 'profiles', 'devices', 'otp_sessions', 'chat_messages',
        'events_funnel', 'ai_action_plans', 'rag_documents'
    ]
    
    for collection in collections_to_clean:
        try:
            await source_db[collection].drop()
            print(f"🗑️ Collection {collection} supprimée")
        except Exception as e:
            print(f"⚠️ Erreur suppression {collection}: {e}")


async def main():
    """Fonction principale."""
    print("=" * 60)
    print("🔄 MIGRATION BASES DE DONNÉES - musAI Platform")
    print("=" * 60)
    
    # Vérifier les variables d'environnement
    print("🔧 Configuration:")
    print(f"  Core DB: {os.getenv('DB_NAME_CORE', 'musai_core')}")
    print(f"  BI DB: {os.getenv('DB_NAME_BI', 'musai_bi')}")
    print(f"  URI Core: {os.getenv('MONGO_URI', 'mongodb://localhost:27017')}")
    print(f"  URI BI: {os.getenv('MONGO_URI_BI', 'mongodb://localhost:27017')}")
    print()
    
    # Confirmation
    response = input("Continuer la migration? (oui/non): ")
    if response.lower() != 'oui':
        print("❌ Migration annulée")
        return
    
    # Exécuter la migration
    await migrate_data()
    
    # Vérifier
    await verify_migration()
    
    # Nettoyage optionnel
    await cleanup_old_data()
    
    print("🎉 Migration terminée!")


if __name__ == "__main__":
    asyncio.run(main())



