# scripts/demo_scheduler.py
"""
Script de démonstration du Scheduler Multicanal Intelligent.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.scheduler.planner_service import create_draft, generate_weekly_plan, get_optimal_posting_times
from api.services.scheduler.ai_copy_service import generate_preview
from api.services.scheduler.abtest_service import create_ab_test, get_ab_test_recommendations
from api.services.scheduler.recycle_service import schedule_recycle, get_recycle_analytics
from api.services.scheduler.job_runner import get_scheduler_status
from api.schemas.scheduler import DraftIn, ABTestCreate, RecyclePolicy
from api.databases.databases import db

async def demo_scheduler():
    """Démonstration du Scheduler Multicanal Intelligent."""
    print("📅 === DÉMONSTRATION SCHEDULER MULTICANAL INTELLIGENT ===\n")
    
    try:
        # Configuration de démonstration
        tenant_id = "demo_tenant"
        muse_id = "demo_muse"
        
        print(f"🏢 Tenant ID: {tenant_id}")
        print(f"👤 Muse ID: {muse_id}\n")
        
        # 1. Génération de contenu IA
        print("1️⃣ Génération de contenu IA...")
        
        platforms = ["instagram", "twitter", "reddit", "tiktok"]
        for platform in platforms:
            preview = await generate_preview(
                platform=platform,
                muse_id=muse_id,
                tone="flirty",
                objective="teasing",
                language="en",
                user_prompt="sexy evening teaser"
            )
            
            print(f"   📱 {platform.upper()}:")
            print(f"      Caption: {preview.get('caption', 'N/A')[:100]}...")
            print(f"      Hashtags: {preview.get('hashtags', [])[:3]}")
            print(f"      Emojis: {preview.get('emojis', [])}")
            print()
        
        # 2. Création de drafts programmés
        print("2️⃣ Création de drafts programmés...")
        
        draft_ids = []
        for i, platform in enumerate(platforms):
            scheduled_time = datetime.now(timezone.utc) + timedelta(hours=i+1)
            
            draft = DraftIn(
                platform=platform,
                muse_id=muse_id,
                title=f"Demo post {i+1}",
                caption=f"Contenu de démonstration pour {platform} - Post #{i+1}",
                hashtags=["#demo", "#scheduler", "#multicanal"],
                emojis=["🔥", "💋", "✨"],
                scheduled_at=scheduled_time,
                tone="flirty",
                objective="teasing"
            )
            
            draft_id = await create_draft(tenant_id, draft)
            draft_ids.append(draft_id)
            print(f"   ✅ Draft créé pour {platform} à {scheduled_time.strftime('%H:%M')}")
        
        print(f"   📊 Total: {len(draft_ids)} drafts créés\n")
        
        # 3. Plan hebdomadaire automatique
        print("3️⃣ Plan hebdomadaire automatique...")
        
        start_day = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
        weekly_ids = await generate_weekly_plan(
            tenant_id=tenant_id,
            muse_id=muse_id,
            start_day=start_day,
            persona_tone="flirty",
            objective="engagement"
        )
        
        print(f"   📅 Plan hebdomadaire généré: {len(weekly_ids)} posts")
        print(f"   🗓️ Début: {start_day.strftime('%Y-%m-%d %H:%M')}")
        print()
        
        # 4. Heures optimales de publication
        print("4️⃣ Heures optimales de publication...")
        
        for platform in platforms:
            optimal_times = await get_optimal_posting_times(platform, muse_id)
            print(f"   📱 {platform.upper()}: {', '.join(optimal_times)}")
        print()
        
        # 5. Test A/B
        print("5️⃣ Test A/B...")
        
        start_at = datetime.now(timezone.utc) + timedelta(hours=2)
        end_at = start_at + timedelta(days=7)
        
        ab_test_payload = ABTestCreate(
            campaign_id="demo_ab_test",
            platform="instagram",
            muse_id=muse_id,
            hypothesis="Test A vs B pour l'engagement",
            kpi="engagement",
            start_at=start_at,
            end_at=end_at,
            variants=[
                DraftIn(
                    platform="instagram",
                    muse_id=muse_id,
                    caption="Variant A - Approche originale",
                    scheduled_at=start_at,
                    tone="flirty",
                    objective="engagement"
                ),
                DraftIn(
                    platform="instagram",
                    muse_id=muse_id,
                    caption="Variant B - Approche alternative",
                    scheduled_at=start_at + timedelta(hours=2),
                    tone="professional",
                    objective="engagement"
                )
            ]
        )
        
        ab_result = await create_ab_test(tenant_id, ab_test_payload)
        print(f"   🧪 Test A/B créé: {ab_result['id']}")
        print(f"   📊 Drafts: {len(ab_result['draft_ids'])} variantes")
        
        # Recommandations A/B
        recommendations = await get_ab_test_recommendations(tenant_id, muse_id, "instagram")
        print(f"   💡 Recommandations: {len(recommendations)} suggestions")
        print()
        
        # 6. Recyclage de contenu
        print("6️⃣ Recyclage de contenu...")
        
        recycle_policy = RecyclePolicy(
            name="Demo Recycle Policy",
            active=True,
            selection="top_by_ctr",
            lookback_days=30,
            max_per_week=3,
            reformat=["twitter", "reddit", "instagram"],
            filters={}
        )
        
        recycle_ids = await schedule_recycle(tenant_id, muse_id, recycle_policy.model_dump())
        print(f"   🔄 Recyclage programmé: {len(recycle_ids)} posts")
        
        # Analytics de recyclage
        recycle_analytics = await get_recycle_analytics(tenant_id, muse_id, 30)
        print(f"   📈 Analytics recyclage:")
        print(f"      - Total recyclé: {recycle_analytics['total_recycled']}")
        print(f"      - Taux de succès: {recycle_analytics['success_rate']:.2%}")
        print()
        
        # 7. Statut du scheduler
        print("7️⃣ Statut du scheduler...")
        
        scheduler_status = await get_scheduler_status()
        print(f"   ⚙️ Scheduler actif: {scheduler_status['running']}")
        print(f"   📋 Jobs totaux: {scheduler_status['total_jobs']}")
        print(f"   ⏰ Prochains jobs:")
        
        for job in scheduler_status['jobs'][:3]:  # Afficher les 3 premiers
            next_run = job['next_run_time']
            if next_run:
                print(f"      - {job['id']}: {next_run}")
        print()
        
        print("🎉 Démonstration du Scheduler terminée avec succès!")
        
        # Nettoyage
        print("\n🧹 Nettoyage des données de démonstration...")
        
        # Supprimer les drafts de démonstration
        await db["scheduled_drafts"].delete_many({"tenant_id": tenant_id})
        await db["ab_tests"].delete_many({"tenant_id": tenant_id})
        await db["recycle_policies"].delete_many({"tenant_id": tenant_id})
        await db["publish_logs"].delete_many({"tenant_id": tenant_id})
        
        print("   ✅ Données de démonstration supprimées")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Fonction principale de démonstration."""
    print("🚀 Démarrage de la démonstration du Scheduler Multicanal Intelligent...\n")
    
    # Configuration de la base de données de test
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db_test = client["test_scheduler_demo"]
    
    # Remplacer la base de données globale
    import api.databases.databases as databases
    databases.db = db_test
    
    try:
        success = await demo_scheduler()
        
        if success:
            print("\n🎉 Démonstration réussie!")
            print("✅ Le Scheduler Multicanal Intelligent est fonctionnel.")
        else:
            print("\n❌ La démonstration a échoué.")
            return False
            
    finally:
        # Nettoyage
        client.close()
    
    return True

if __name__ == "__main__":
    # Configuration des variables d'environnement pour le test
    os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
    
    # Lancer la démonstration
    success = asyncio.run(main())
    sys.exit(0 if success else 1)




