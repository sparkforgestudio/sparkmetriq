# scripts/test_database_separation.py
"""
Script de test pour vérifier la séparation des bases de données.
"""

import asyncio
import os
from datetime import datetime
from api.databases.databases import (
    get_core_db, get_bi_db, get_db_for_collection,
    ensure_all_indexes, cleanup_test_data
)


async def test_database_separation():
    """Test la séparation des bases de données."""
    print("🧪 Test de séparation des bases de données...")
    
    # Récupérer les bases
    db_core = get_core_db()
    db_bi = get_bi_db()
    
    print(f"📦 Base Core: {db_core.name}")
    print(f"📊 Base BI: {db_bi.name}")
    
    # Test 1: Collections Core
    print("\n🔍 Test collections Core...")
    core_collections = ['users', 'profiles', 'devices', 'otp_sessions', 'chat_messages']
    for collection in core_collections:
        db = get_db_for_collection(collection)
        if db.name == db_core.name:
            print(f"✅ {collection} -> Core")
        else:
            print(f"❌ {collection} -> BI (ERREUR)")
    
    # Test 2: Collections BI
    print("\n🔍 Test collections BI...")
    bi_collections = ['ai_action_plans', 'rag_documents', 'events_funnel', 'scraped_contents']
    for collection in bi_collections:
        db = get_db_for_collection(collection)
        if db.name == db_bi.name:
            print(f"✅ {collection} -> BI")
        else:
            print(f"❌ {collection} -> Core (ERREUR)")
    
    # Test 3: Insertion de données de test
    print("\n📝 Test insertion de données...")
    
    # Données Core
    test_user = {
        "email": "test@example.com",
        "org_id": "test_org",
        "created_at": datetime.now()
    }
    await db_core["users"].insert_one(test_user)
    print("✅ Utilisateur inséré dans Core")
    
    # Données BI
    test_ai_plan = {
        "tenant_id": "test_org",
        "muse_id": "test_muse",
        "month": "2024-01",
        "created_at": datetime.now()
    }
    await db_bi["ai_action_plans"].insert_one(test_ai_plan)
    print("✅ Plan IA inséré dans BI")
    
    # Test 4: Vérification des données
    print("\n🔍 Vérification des données...")
    
    user_count = await db_core["users"].count_documents({"email": "test@example.com"})
    print(f"📦 Utilisateurs dans Core: {user_count}")
    
    plan_count = await db_bi["ai_action_plans"].count_documents({"tenant_id": "test_org"})
    print(f"📊 Plans IA dans BI: {plan_count}")
    
    # Test 5: Index
    print("\n📊 Test des index...")
    try:
        await ensure_all_indexes()
        print("✅ Index créés avec succès")
    except Exception as e:
        print(f"❌ Erreur création index: {e}")
    
    # Test 6: Nettoyage
    print("\n🧹 Nettoyage des données de test...")
    await cleanup_test_data()
    print("✅ Données de test nettoyées")
    
    print("\n🎉 Tests terminés!")


async def test_rag_databases():
    """Test spécifique pour les systèmes RAG."""
    print("\n🤖 Test des systèmes RAG...")
    
    # RAG Chat (Core)
    from api.services.chat_omnichannel.manager import CHAT_COLLECTION
    print(f"💬 RAG Chat utilise: {CHAT_COLLECTION.database.name}")
    
    # RAG Marketing (BI)
    from api.services.ai_marketing.rag_system import RAGSystem
    rag_system = RAGSystem()
    print(f"📈 RAG Marketing utilise: {rag_system.db.name}")
    
    # Vérifier que c'est correct
    if CHAT_COLLECTION.database.name.endswith('_core'):
        print("✅ RAG Chat utilise la base Core")
    else:
        print("❌ RAG Chat n'utilise pas la base Core")
    
    if rag_system.db.name.endswith('_bi'):
        print("✅ RAG Marketing utilise la base BI")
    else:
        print("❌ RAG Marketing n'utilise pas la base BI")


async def main():
    """Fonction principale."""
    print("=" * 60)
    print("🧪 TEST SÉPARATION BASES DE DONNÉES")
    print("=" * 60)
    
    try:
        await test_database_separation()
        await test_rag_databases()
        
        print("\n✅ Tous les tests sont passés!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())




