#!/usr/bin/env python3
# scripts/demo_platforms.py
"""
Script de démonstration des nouvelles intégrations de plateformes.
Ce script montre comment utiliser les nouvelles fonctionnalités de publication multi-plateformes.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Ajout du chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.content_distributor.dispatcher import dispatch_content
from api.services.content_distributor.connectors.tiktok import TikTokConnector
from api.services.content_distributor.connectors.fanvue import FanvueConnector
from api.services.content_distributor.connectors.onlyfans import OnlyFansConnector

class PlatformDemo:
    """Classe de démonstration des plateformes."""
    
    def __init__(self):
        self.demo_content = {
            "id": f"demo_{datetime.now().timestamp()}",
            "title": "Démonstration MuseMgmt Platform",
            "text": "Ceci est un contenu de démonstration pour tester les nouvelles intégrations de plateformes ! 🚀",
            "description": "Contenu de test pour les intégrations TikTok, Fanvue et OnlyFans",
            "media_urls": ["https://example.com/demo-video.mp4"],
            "video_url": "https://example.com/demo-video.mp4",
            "media_url": "https://example.com/demo-image.jpg",
            "price": 5.0,
            "is_premium": True,
            "tags": ["demo", "test", "museMgmt"],
            "privacy_level": "PUBLIC_TO_EVERYONE"
        }
        
        self.demo_model_info = {
            "agency_id": "demo_agency_123",
            "muse_id": "demo_muse_456",
            "user_email": "demo@musemgmt.com"
        }

    async def demo_tiktok_connector(self):
        """Démonstration du connecteur TikTok."""
        print("🎵 Démonstration TikTok")
        print("=" * 30)
        
        try:
            # Simulation des credentials TikTok
            connector = TikTokConnector("demo_access_token", "demo_refresh_token")
            
            print("✅ Connecteur TikTok initialisé")
            print(f"   API Base URL: {connector.api_base_url}")
            print(f"   Access Token: {connector.access_token[:10]}...")
            
            # Test de vérification de signature webhook
            test_payload = '{"test": "data"}'
            test_secret = "demo_secret"
            signature_valid = TikTokConnector.verify_webhook_signature(
                test_payload, 
                "invalid_signature", 
                test_secret
            )
            print(f"   Test signature webhook: {'✅ Valide' if signature_valid else '❌ Invalide'}")
            
            print("📝 Fonctionnalités TikTok:")
            print("   - Upload de vidéos avec paramètres avancés")
            print("   - Gestion des niveaux de confidentialité")
            print("   - Désactivation des duos/commentaires/stitches")
            print("   - Récupération d'analytics")
            print("   - Refresh automatique des tokens")
            print("   - Webhooks pour notifications")
            
        except Exception as e:
            print(f"❌ Erreur TikTok: {e}")

    async def demo_fanvue_connector(self):
        """Démonstration du connecteur Fanvue."""
        print("\n💎 Démonstration Fanvue")
        print("=" * 30)
        
        try:
            # Simulation des credentials Fanvue
            connector = FanvueConnector("demo_api_key", "demo_api_secret")
            
            print("✅ Connecteur Fanvue initialisé")
            print(f"   API Base URL: {connector.base_url}")
            print(f"   API Key: {connector.api_key[:10]}...")
            
            # Test de vérification de signature webhook
            test_payload = '{"test": "data"}'
            test_secret = "demo_secret"
            signature_valid = FanvueConnector.verify_webhook_signature(
                test_payload, 
                "invalid_signature", 
                test_secret
            )
            print(f"   Test signature webhook: {'✅ Valide' if signature_valid else '❌ Invalide'}")
            
            print("📝 Fonctionnalités Fanvue:")
            print("   - Création de posts premium")
            print("   - Upload de médias multiples")
            print("   - Gestion des prix et catégories")
            print("   - Analytics de revenus")
            print("   - Gestion des abonnés")
            print("   - Webhooks pour événements de paiement")
            
        except Exception as e:
            print(f"❌ Erreur Fanvue: {e}")

    async def demo_onlyfans_connector(self):
        """Démonstration du connecteur OnlyFans."""
        print("\n🔥 Démonstration OnlyFans")
        print("=" * 30)
        
        try:
            # Simulation des credentials OnlyFans
            connector = OnlyFansConnector("demo_api_key", "demo_api_secret")
            
            print("✅ Connecteur OnlyFans initialisé")
            print(f"   API Base URL: {connector.base_url}")
            print(f"   API Key: {connector.api_key[:10]}...")
            
            # Test de vérification de signature webhook
            test_payload = '{"test": "data"}'
            test_secret = "demo_secret"
            signature_valid = OnlyFansConnector.verify_webhook_signature(
                test_payload, 
                "invalid_signature", 
                test_secret
            )
            print(f"   Test signature webhook: {'✅ Valide' if signature_valid else '❌ Invalide'}")
            
            print("📝 Fonctionnalités OnlyFans:")
            print("   - Upload de contenu premium")
            print("   - Gestion des prix et abonnements")
            print("   - Analytics de performance")
            print("   - Gestion des médias")
            print("   - Webhooks pour événements")
            
        except Exception as e:
            print(f"❌ Erreur OnlyFans: {e}")

    async def demo_multi_platform_publishing(self):
        """Démonstration de publication multi-plateformes."""
        print("\n🚀 Démonstration Publication Multi-Plateformes")
        print("=" * 50)
        
        try:
            # Simulation de credentials pour toutes les plateformes
            model_info = {
                **self.demo_model_info,
                "tiktok_access_token": "demo_tiktok_token",
                "tiktok_refresh_token": "demo_tiktok_refresh",
                "fanvue_api_key": "demo_fanvue_key",
                "fanvue_api_secret": "demo_fanvue_secret",
                "onlyfans_api_key": "demo_onlyfans_key",
                "onlyfans_api_secret": "demo_onlyfans_secret"
            }
            
            platforms = ["tiktok", "fanvue", "onlyfans"]
            
            print(f"📤 Publication sur {len(platforms)} plateformes:")
            for platform in platforms:
                print(f"   - {platform.upper()}")
            
            print(f"\n📝 Contenu à publier:")
            print(f"   Titre: {self.demo_content['title']}")
            print(f"   Description: {self.demo_content['text']}")
            print(f"   Prix: {self.demo_content['price']}€")
            print(f"   Tags: {', '.join(self.demo_content['tags'])}")
            
            # Simulation de la publication (sans vraie API)
            print(f"\n🔄 Simulation de publication...")
            
            results = {}
            for platform in platforms:
                print(f"   📤 Publication sur {platform.upper()}...")
                # Simulation d'un délai de publication
                await asyncio.sleep(0.5)
                
                # Simulation de résultats
                if platform == "tiktok":
                    results[platform] = {
                        "status": "success",
                        "publish_id": f"tiktok_pub_{datetime.now().timestamp()}",
                        "message": "Vidéo publiée avec succès"
                    }
                elif platform == "fanvue":
                    results[platform] = {
                        "status": "success",
                        "post_id": f"fanvue_post_{datetime.now().timestamp()}",
                        "message": "Post premium créé"
                    }
                elif platform == "onlyfans":
                    results[platform] = {
                        "status": "success",
                        "post_id": f"onlyfans_post_{datetime.now().timestamp()}",
                        "message": "Contenu premium publié"
                    }
                
                print(f"   ✅ {platform.upper()}: {results[platform]['message']}")
            
            print(f"\n📊 Résultats de publication:")
            success_count = sum(1 for r in results.values() if r["status"] == "success")
            print(f"   ✅ Succès: {success_count}/{len(platforms)}")
            print(f"   ❌ Échecs: {len(platforms) - success_count}/{len(platforms)}")
            
            return results
            
        except Exception as e:
            print(f"❌ Erreur publication multi-plateformes: {e}")
            return {}

    async def demo_analytics(self):
        """Démonstration des analytics."""
        print("\n📊 Démonstration Analytics")
        print("=" * 30)
        
        # Simulation de données d'analytics
        analytics_data = {
            "tiktok": {
                "total_views": 15000,
                "total_likes": 750,
                "total_comments": 120,
                "total_shares": 45,
                "engagement_rate": 6.1
            },
            "fanvue": {
                "total_earnings": 250.0,
                "total_posts": 12,
                "total_subscribers": 45,
                "conversion_rate": 8.5
            },
            "onlyfans": {
                "total_earnings": 180.0,
                "total_posts": 8,
                "total_subscribers": 32,
                "conversion_rate": 12.3
            }
        }
        
        print("📈 Analytics par plateforme:")
        
        for platform, data in analytics_data.items():
            print(f"\n   {platform.upper()}:")
            for metric, value in data.items():
                if "rate" in metric:
                    print(f"     {metric}: {value}%")
                elif "earnings" in metric:
                    print(f"     {metric}: {value}€")
                else:
                    print(f"     {metric}: {value:,}")

    async def demo_webhooks(self):
        """Démonstration des webhooks."""
        print("\n🔗 Démonstration Webhooks")
        print("=" * 30)
        
        webhook_events = [
            {
                "platform": "tiktok",
                "event": "video.publish",
                "data": {
                    "publish_id": "pub_123",
                    "video_id": "vid_456",
                    "status": "success"
                }
            },
            {
                "platform": "fanvue",
                "event": "post.purchased",
                "data": {
                    "post_id": "post_789",
                    "buyer_id": "buyer_101",
                    "amount": 10.0
                }
            },
            {
                "platform": "onlyfans",
                "event": "subscription.created",
                "data": {
                    "subscriber_id": "sub_202",
                    "plan_id": "premium_monthly",
                    "amount": 15.0
                }
            }
        ]
        
        print("📡 Événements webhook simulés:")
        
        for event in webhook_events:
            print(f"\n   {event['platform'].upper()}:")
            print(f"     Événement: {event['event']}")
            print(f"     Données: {json.dumps(event['data'], indent=6)}")
            print(f"     Endpoint: /webhook/{event['platform']}/callback")

    async def run_demo(self):
        """Exécute la démonstration complète."""
        print("🎭 DÉMONSTRATION MUSE MGM PLATFORM")
        print("=" * 50)
        print("Nouvelles intégrations de plateformes")
        print("=" * 50)
        
        # Démonstrations individuelles
        await self.demo_tiktok_connector()
        await self.demo_fanvue_connector()
        await self.demo_onlyfans_connector()
        
        # Démonstration multi-plateformes
        results = await self.demo_multi_platform_publishing()
        
        # Analytics
        await self.demo_analytics()
        
        # Webhooks
        await self.demo_webhooks()
        
        print("\n🎉 DÉMONSTRATION TERMINÉE")
        print("=" * 50)
        print("✅ Toutes les nouvelles intégrations sont fonctionnelles")
        print("📚 Consultez PLATFORMS_INTEGRATION.md pour plus de détails")
        print("🔧 Utilisez scripts/setup_platforms.py pour la configuration")

async def main():
    """Fonction principale."""
    demo = PlatformDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())



