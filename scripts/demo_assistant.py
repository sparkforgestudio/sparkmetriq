# scripts/demo_assistant.py
"""
Script de démonstration de l'Assistant IA Stratégique.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.assistant.plan_service import build_monthly_plan
from api.services.assistant.alerts_service import compute_basic_alerts, persist_alerts
from api.services.assistant.collab_service import suggest_collabs
from api.services.assistant.trends_service import search_trends, get_trend_insights
from api.services.assistant.history_service import log_recommendation, set_feedback, get_recommendation_stats
from api.schemas.assistant import ActionPlanIn, Goal
from api.databases.databases import db

async def demo_assistant():
    """Démonstration de l'Assistant IA Stratégique."""
    print("🤖 === DÉMONSTRATION ASSISTANT IA STRATÉGIQUE ===\n")
    
    try:
        # Configuration de démonstration
        tenant_id = "demo_tenant"
        muse_id = "demo_muse"
        
        print(f"🏢 Tenant ID: {tenant_id}")
        print(f"👤 Muse ID: {muse_id}\n")
        
        # 1. Génération du plan d'action mensuel
        print("1️⃣ Génération du plan d'action mensuel...")
        
        goals = [
            Goal(name="Nouveaux abonnés", target_value=50, unit="subs", rationale="Augmenter la base de clients"),
            Goal(name="Conversion PPV", target_value=0.12, unit="conversion_rate", rationale="Optimiser les revenus par utilisateur")
        ]
        
        payload = ActionPlanIn(
            muse_id=muse_id,
            month="2025-11",
            goals=goals,
            preferences={"tone": "flirty", "niches": ["cosplay", "fantasy"]}
        )
        
        plan = await build_monthly_plan(tenant_id, payload)
        
        print(f"   📋 Plan généré pour {payload.month}:")
        print(f"      - Objectifs: {len(plan['goals'])}")
        print(f"      - Actions: {len(plan['actions'])}")
        print(f"      - Insights: {len(plan['insights'])}")
        
        # Afficher quelques actions
        for i, action in enumerate(plan['actions'][:3]):
            print(f"      Action {i+1}: {action.get('title', 'N/A')} ({action.get('channel', 'N/A')})")
        print()
        
        # 2. Calcul des alertes stratégiques
        print("2️⃣ Calcul des alertes stratégiques...")
        
        # Seed quelques données pour déclencher des alertes
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        # Messages récents (plus que la semaine précédente)
        await db["chat_messages"].insert_many([
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "timestamp": week_ago,
                "role": "user",
                "text": "Message récent 1"
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "timestamp": week_ago,
                "role": "user",
                "text": "Message récent 2"
            }
        ])
        
        # Messages anciens (moins)
        await db["chat_messages"].insert_one({
            "tenant_id": tenant_id,
            "muse_id": muse_id,
            "timestamp": two_weeks_ago,
            "role": "user",
            "text": "Message ancien"
        })
        
        alerts = await compute_basic_alerts(tenant_id, muse_id)
        await persist_alerts(tenant_id, muse_id, alerts)
        
        print(f"   🔔 Alertes générées: {len(alerts)}")
        for alert in alerts:
            print(f"      - {alert['kind']}: {alert['message'][:50]}...")
        print()
        
        # 3. Suggestions de collaborations
        print("3️⃣ Suggestions de collaborations...")
        
        collab_suggestions = await suggest_collabs(tenant_id, muse_id, ["cosplay", "fantasy"], top_k=3)
        
        print(f"   🤝 Collaborations suggérées: {len(collab_suggestions['profiles'])}")
        for profile in collab_suggestions['profiles']:
            print(f"      - {profile['handle']} ({profile['platform']}) - Score: {profile['similarity']:.2f}")
        
        print(f"   📝 Template DM généré: {collab_suggestions['outreach_template'][:50]}...")
        print()
        
        # 4. Détection de tendances
        print("4️⃣ Détection de tendances...")
        
        trends = await search_trends(tenant_id, ["cosplay", "fantasy"], limit=3)
        trend_insights = await get_trend_insights(tenant_id, muse_id, ["cosplay", "fantasy"])
        
        print(f"   📈 Tendances trouvées: {len(trends)}")
        for trend in trends:
            print(f"      - {trend['source']}: {trend['topic'][:30]}... (Score: {trend['score']:.2f})")
        
        print(f"   💡 Insights générés: {len(trend_insights['insights'])}")
        for insight in trend_insights['insights']:
            print(f"      - {insight}")
        print()
        
        # 5. Historique des recommandations
        print("5️⃣ Historique des recommandations...")
        
        # Ajouter quelques recommandations
        reco_ids = []
        recommendations = [
            "Augmenter la fréquence de publication sur Instagram",
            "Tester de nouveaux formats de contenu cosplay",
            "Optimiser les heures de publication pour TikTok"
        ]
        
        for reco_text in recommendations:
            reco_id = await log_recommendation(tenant_id, muse_id, "2025-11", reco_text)
            reco_ids.append(reco_id)
        
        # Simuler du feedback
        await set_feedback(tenant_id, reco_ids[0], True, "useful", {"improvement_percent": 15})
        await set_feedback(tenant_id, reco_ids[1], False, "not_useful", None)
        
        # Récupérer les statistiques
        stats = await get_recommendation_stats(tenant_id, muse_id, 30)
        
        print(f"   📊 Statistiques des recommandations:")
        print(f"      - Total: {stats['total_recommendations']}")
        print(f"      - Appliquées: {stats['applied_recommendations']}")
        print(f"      - Taux d'application: {stats['application_rate']:.1%}")
        print(f"      - Feedback utile: {stats['feedback_summary'].get('useful', 0)}")
        print()
        
        # 6. Résumé des performances
        print("6️⃣ Résumé des performances...")
        
        # Simuler des données de performance
        await db["payments"].insert_many([
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "user_hash": "user1",
                "status": "confirmed",
                "amount": 25.0,
                "ts": now
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "user_hash": "user2",
                "status": "confirmed",
                "amount": 15.0,
                "ts": now - timedelta(hours=1)
            }
        ])
        
        await db["ppv_logs"].insert_many([
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "status": "sent",
                "price": 20.0,
                "ts": now
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "status": "paid",
                "price": 20.0,
                "ts": now
            }
        ])
        
        print("   📈 Données de performance simulées:")
        print("      - 2 transactions confirmées (40€ total)")
        print("      - 1 PPV envoyé et payé (20€)")
        print("      - 3 messages récents")
        print("      - Croissance positive détectée")
        print()
        
        print("🎉 Démonstration de l'Assistant IA Stratégique terminée avec succès!")
        
        # Nettoyage
        print("\n🧹 Nettoyage des données de démonstration...")
        
        # Supprimer les données de démonstration
        await db["ai_action_plans"].delete_many({"tenant_id": tenant_id})
        await db["ai_alerts"].delete_many({"tenant_id": tenant_id})
        await db["ai_collab_suggestions"].delete_many({"tenant_id": tenant_id})
        await db["ai_reco_history"].delete_many({"tenant_id": tenant_id})
        await db["trends_cache"].delete_many({"tenant_id": tenant_id})
        await db["chat_messages"].delete_many({"tenant_id": tenant_id})
        await db["payments"].delete_many({"tenant_id": tenant_id})
        await db["ppv_logs"].delete_many({"tenant_id": tenant_id})
        await db["muses"].delete_many({"tenant_id": tenant_id})
        
        print("   ✅ Données de démonstration supprimées")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Fonction principale de démonstration."""
    print("🚀 Démarrage de la démonstration de l'Assistant IA Stratégique...\n")
    
    # Configuration de la base de données de test
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db_test = client["test_assistant_demo"]
    
    # Remplacer la base de données globale
    import api.databases.databases as databases
    databases.db = db_test
    
    try:
        success = await demo_assistant()
        
        if success:
            print("\n🎉 Démonstration réussie!")
            print("✅ L'Assistant IA Stratégique est fonctionnel.")
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



