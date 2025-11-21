# scripts/demo_analytics.py
"""
Script de démonstration du module Analytics & BI.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.analytics.conversation_service import kpis_conversation, response_time_stats
from api.services.analytics.funnel_service import funnel_overview, revenue_kpis
from api.services.analytics.forecast_service import forecast_messages, forecast_gmv
from api.databases.databases import db

async def demo_analytics():
    """Démonstration du module Analytics & BI."""
    print("📊 === DÉMONSTRATION MODULE ANALYTICS & BI ===\n")
    
    try:
        # Configuration de démonstration
        tenant_id = "demo_tenant"
        muse_id = "demo_muse"
        date_from = utcnow() - timedelta(days=30)
        date_to = utcnow()
        
        print(f"🏢 Tenant ID: {tenant_id}")
        print(f"👤 Muse ID: {muse_id}")
        print(f"📅 Période: {date_from.strftime('%Y-%m-%d')} à {date_to.strftime('%Y-%m-%d')}\n")
        
        # 1. Seed des données de démonstration
        print("1️⃣ Création des données de démonstration...")
        
        # Messages de chat
        await db["chat_messages"].insert_many([
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "conversation_id": "conv_1",
                "role": "user",
                "text": "Bonjour, comment allez-vous?",
                "channel": "web",
                "timestamp": utcnow() - timedelta(hours=2)
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "conversation_id": "conv_1",
                "role": "bot",
                "text": "Bonjour! Je vais très bien, merci!",
                "channel": "web",
                "timestamp": utcnow() - timedelta(hours=2, minutes=1)
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "conversation_id": "conv_2",
                "role": "user",
                "text": "Pouvez-vous m'aider?",
                "channel": "telegram",
                "timestamp": utcnow() - timedelta(hours=1)
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "conversation_id": "conv_2",
                "role": "bot",
                "text": "Bien sûr! En quoi puis-je vous aider?",
                "channel": "telegram",
                "timestamp": utcnow() - timedelta(hours=1, minutes=30)
            }
        ])
        
        # Events funnel
        await db["events_funnel"].insert_many([
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "phase": "contact",
                "source": "web",
                "ts": utcnow() - timedelta(days=5)
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "phase": "lead",
                "source": "web",
                "ts": utcnow() - timedelta(days=4)
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "phase": "subscriber",
                "source": "web",
                "ts": utcnow() - timedelta(days=3)
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "phase": "payer",
                "source": "web",
                "ts": utcnow() - timedelta(days=2)
            }
        ])
        
        # Payments
        await db["payments"].insert_many([
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "user_hash": "user_1",
                "status": "confirmed",
                "amount": 25.0,
                "ts": utcnow() - timedelta(days=2)
            },
            {
                "tenant_id": tenant_id,
                "muse_id": muse_id,
                "user_hash": "user_2",
                "status": "confirmed",
                "amount": 15.0,
                "ts": utcnow() - timedelta(days=1)
            }
        ])
        
        print("✅ Données de démonstration créées\n")
        
        # 2. KPIs Conversationnels
        print("2️⃣ KPIs Conversationnels...")
        conv_kpis = await kpis_conversation(tenant_id, date_from, date_to, muse_id)
        response_time = await response_time_stats(tenant_id, date_from, date_to, muse_id)
        
        print(f"   💬 Conversations: {conv_kpis['conversations']}")
        print(f"   📝 Messages totaux: {conv_kpis['messages']}")
        print(f"   👤 Messages utilisateur: {conv_kpis['user_msgs']}")
        print(f"   🤖 Messages bot: {conv_kpis['bot_msgs']}")
        print(f"   📱 Canaux: {', '.join(conv_kpis['channels'])}")
        print(f"   ⏱️ Temps de réponse moyen: {response_time.get('avg_rt_sec', 'N/A')} sec")
        print()
        
        # 3. Funnel Overview
        print("3️⃣ Funnel Overview...")
        funnel = await funnel_overview(tenant_id, date_from, date_to, muse_id)
        
        print(f"   📞 Contacts: {funnel['contact']}")
        print(f"   🎯 Leads: {funnel['lead']}")
        print(f"   👥 Abonnés: {funnel['subscriber']}")
        print(f"   💰 Payeurs: {funnel['payer']}")
        print(f"   🔄 Retenus: {funnel['retained']}")
        print(f"   📈 CR Contact→Lead: {funnel['cr_contact_lead']:.2%}" if funnel['cr_contact_lead'] else "   📈 CR Contact→Lead: N/A")
        print(f"   📈 CR Lead→Subscriber: {funnel['cr_lead_subscriber']:.2%}" if funnel['cr_lead_subscriber'] else "   📈 CR Lead→Subscriber: N/A")
        print(f"   📈 CR Subscriber→Payer: {funnel['cr_subscriber_payer']:.2%}" if funnel['cr_subscriber_payer'] else "   📈 CR Subscriber→Payer: N/A")
        print()
        
        # 4. KPIs Revenus
        print("4️⃣ KPIs Revenus...")
        revenue = await revenue_kpis(tenant_id, date_from, date_to, muse_id)
        
        print(f"   💵 GMV: ${revenue['gmv']:.2f}")
        print(f"   👥 Payeurs: {revenue['payers']}")
        print(f"   📊 ARPU: ${revenue['arpu']:.2f}" if revenue['arpu'] else "   📊 ARPU: N/A")
        print(f"   💎 LTV moyen: ${revenue['ltv_mean']:.2f}" if revenue['ltv_mean'] else "   💎 LTV moyen: N/A")
        print()
        
        # 5. Prévisions
        print("5️⃣ Prévisions (7 jours)...")
        
        # Prévision messages
        forecast_msg = await forecast_messages(tenant_id, date_from, date_to, horizon=7, muse_id=muse_id)
        print(f"   📝 Prévision messages:")
        for point in forecast_msg['series'][:3]:  # Afficher les 3 premiers
            print(f"      Jour {point['day']}: {point['yhat']:.1f} messages")
        print(f"      ... ({len(forecast_msg['series'])} jours au total)")
        
        # Prévision GMV
        forecast_gmv_data = await forecast_gmv(tenant_id, date_from, date_to, horizon=7, muse_id=muse_id)
        print(f"   💰 Prévision GMV:")
        for point in forecast_gmv_data['series'][:3]:  # Afficher les 3 premiers
            print(f"      Jour {point['day']}: ${point['yhat']:.2f}")
        print(f"      ... ({len(forecast_gmv_data['series'])} jours au total)")
        print()
        
        print("🎉 Démonstration terminée avec succès!")
        
        # Nettoyage
        print("\n🧹 Nettoyage des données de démonstration...")
        await db["chat_messages"].delete_many({"tenant_id": tenant_id})
        await db["events_funnel"].delete_many({"tenant_id": tenant_id})
        await db["payments"].delete_many({"tenant_id": tenant_id})
        print("   ✅ Données de démonstration supprimées")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Fonction principale de démonstration."""
    print("🚀 Démarrage de la démonstration du module Analytics & BI...\n")
    
    # Configuration de la base de données de test
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db_test = client["test_analytics_demo"]
    
    # Remplacer la base de données globale
    import api.databases.databases as databases
    databases.db = db_test
    
    try:
        success = await demo_analytics()
        
        if success:
            print("\n🎉 Démonstration réussie!")
            print("✅ Le module Analytics & BI est fonctionnel.")
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



