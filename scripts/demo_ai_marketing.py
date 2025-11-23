# scripts/demo_ai_marketing.py
"""
Script de démonstration du module IA Marketing & Business Multi-plateformes.
"""

import asyncio
import os
import sys
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.ai_marketing.data_collector import DataCollector, PlatformType
from api.services.ai_marketing.creator_analyzer import CreatorAnalyzer, CreatorNiche
from api.services.ai_marketing.recommendation_engine import RecommendationEngine
from api.services.ai_marketing.logger import logger

async def demo_creator_analysis():
    """Démonstration de l'analyse de créateur."""
    print("🎯 === DÉMONSTRATION MODULE IA MARKETING ===\n")
    
    # Configuration de démonstration
    creator_username = "demo_creator"
    platforms = [PlatformType.INSTAGRAM, PlatformType.TIKTOK, PlatformType.REDDIT]
    
    print(f"📊 Analyse du créateur: {creator_username}")
    print(f"📱 Plateformes: {', '.join([p.value for p in platforms])}\n")
    
    try:
        # 1. Collecte de données
        print("1️⃣ Collecte des données...")
        async with DataCollector() as collector:
            # Simulation de données (en production, utiliser les vrais scrapers Apify)
            creator_data = {
                "creator_username": creator_username,
                "collection_timestamp": utcnow().isoformat(),
                "platforms": {
                    "instagram": {
                        "profile": {
                            "username": creator_username,
                            "followers": 8500,
                            "following": 1200,
                            "posts_count": 150,
                            "bio": "Cosplay creator | Fantasy & Anime | Custom content available",
                            "isVerified": True
                        },
                        "posts": [
                            {
                                "id": "post_1",
                                "caption": "New elf cosplay transformation! 🧝‍♀️✨ #cosplay #fantasy #elf #anime",
                                "likesCount": 450,
                                "commentsCount": 25,
                                "timestamp": "2024-01-15T10:30:00Z",
                                "mediaType": "image",
                                "hashtags": ["cosplay", "fantasy", "elf", "anime"],
                                "mentions": []
                            },
                            {
                                "id": "post_2", 
                                "caption": "Behind the scenes of my latest shoot! The transformation process is always magical ✨ #bts #cosplay #transformation",
                                "likesCount": 320,
                                "commentsCount": 18,
                                "timestamp": "2024-01-14T15:45:00Z",
                                "mediaType": "video",
                                "hashtags": ["bts", "cosplay", "transformation"],
                                "mentions": []
                            }
                        ]
                    },
                    "tiktok": {
                        "profile": {
                            "username": creator_username,
                            "followers": 3200,
                            "following": 450,
                            "videosCount": 45,
                            "signature": "Cosplay transformations ✨ Custom content available",
                            "verified": False
                        },
                        "videos": [
                            {
                                "id": "video_1",
                                "description": "Elf transformation in 30 seconds! ✨ #cosplay #elf #transformation #fantasy",
                                "likesCount": 1200,
                                "commentsCount": 85,
                                "sharesCount": 45,
                                "viewsCount": 15000,
                                "timestamp": "2024-01-15T12:00:00Z",
                                "hashtags": ["cosplay", "elf", "transformation", "fantasy"],
                                "audio": "Original sound"
                            }
                        ]
                    },
                    "reddit": {
                        "posts": [
                            {
                                "id": "reddit_1",
                                "title": "My latest elf cosplay - what do you think?",
                                "text": "Just finished this elf cosplay and I'm really proud of how it turned out! The ears and makeup took forever but I think it was worth it.",
                                "subreddit": "cosplay",
                                "upvotes": 125,
                                "commentsCount": 12,
                                "createdAt": "2024-01-15T08:00:00Z",
                                "author": creator_username,
                                "url": "https://reddit.com/r/cosplay/comments/example"
                            }
                        ]
                    }
                }
            }
        
        print("✅ Données collectées avec succès\n")
        
        # 2. Analyse du créateur
        print("2️⃣ Analyse du créateur...")
        analyzer = CreatorAnalyzer()
        creator_profile = await analyzer.analyze_creator(creator_data)
        
        print(f"   🎭 Niche détectée: {creator_profile.niche.value}")
        print(f"   👥 Total followers: {sum(creator_profile.followers.values())}")
        print(f"   📈 Taux d'engagement moyen: {sum(creator_profile.engagement_rates.values()) / len(creator_profile.engagement_rates):.2%}")
        print(f"   💰 Prix abonnement: {creator_profile.pricing}")
        print()
        
        # 3. Génération des recommandations
        print("3️⃣ Génération des recommandations IA...")
        recommendation_engine = RecommendationEngine()
        await recommendation_engine.initialize()
        
        recommendations = await recommendation_engine.generate_recommendations(creator_profile, creator_data)
        
        print(f"   📋 {len(recommendations)} recommandations générées:")
        for i, rec in enumerate(recommendations[:5], 1):  # Afficher les 5 premières
            print(f"      {i}. [{rec.category.upper()}] {rec.title}")
            print(f"         Priorité: {rec.priority} | Impact: {rec.impact_score:.1f} | Effort: {rec.effort_score:.1f}")
            print(f"         Timeline: {rec.timeline}")
            print()
        
        # 4. Plan d'action hebdomadaire
        print("4️⃣ Plan d'action hebdomadaire...")
        weekly_plan = await recommendation_engine.generate_weekly_action_plan(creator_profile, recommendations)
        
        print(f"   📅 Semaine du {weekly_plan.get('week_start', 'N/A')}")
        print(f"   📊 {weekly_plan.get('total_tasks', 0)} tâches au total")
        print(f"   🔥 {weekly_plan.get('high_priority_tasks', 0)} tâches prioritaires")
        print()
        
        # Afficher le plan par jour
        daily_plan = weekly_plan.get('daily_plan', {})
        for day, tasks in daily_plan.items():
            if tasks:
                print(f"   📅 {day.title()}:")
                for task in tasks:
                    print(f"      • {task['title']}")
                print()
        
        # 5. Benchmarks de niche
        print("5️⃣ Benchmarks de niche...")
        niche_benchmarks = await analyzer.get_niche_recommendations(creator_profile.niche)
        
        print(f"   💰 Prix moyen recommandé: ${niche_benchmarks.get('optimal_pricing', 0):.2f}")
        print(f"   📱 Plateformes primaires: {', '.join(niche_benchmarks.get('primary_platforms', []))}")
        print(f"   📝 Types de contenu: {', '.join(niche_benchmarks.get('content_types', []))}")
        print()
        
        print("🎉 Démonstration terminée avec succès!")
        
    except Exception as e:
        logger.error(f"Erreur démonstration: {e}")
        print(f"❌ Erreur: {e}")

async def demo_content_suggestions():
    """Démonstration des suggestions de contenu."""
    print("\n🎨 === DÉMONSTRATION SUGGESTIONS DE CONTENU ===\n")
    
    try:
        # Créer un profil de démonstration
        creator_profile = CreatorAnalyzer().benchmarks[CreatorNiche.COSPLAY]
        
        # Générer des suggestions
        recommendation_engine = RecommendationEngine()
        await recommendation_engine.initialize()
        
        suggestions = await recommendation_engine.generate_content_suggestions(
            creator_profile, 
            "instagram", 
            "transformation_video"
        )
        
        print(f"📱 Plateforme: {suggestions.platform}")
        print(f"🎬 Type de contenu: {suggestions.content_type}")
        print(f"📝 Titre suggéré: {suggestions.title_suggestion}")
        print(f"📄 Description: {suggestions.description_template}")
        print(f"🏷️ Hashtags: {', '.join(suggestions.hashtags)}")
        print(f"⏰ Timing optimal: {suggestions.optimal_posting_time}")
        print(f"📈 Engagement attendu: {suggestions.expected_engagement:.1%}")
        print()
        
    except Exception as e:
        logger.error(f"Erreur suggestions contenu: {e}")
        print(f"❌ Erreur: {e}")

async def main():
    """Fonction principale de démonstration."""
    print("🚀 Démarrage de la démonstration du module IA Marketing...\n")
    
    # Démonstration 1: Analyse complète
    await demo_creator_analysis()
    
    # Démonstration 2: Suggestions de contenu
    await demo_content_suggestions()
    
    print("\n✨ Démonstration terminée!")

if __name__ == "__main__":
    # Configuration des variables d'environnement pour la démo
    os.environ.setdefault("OPENAI_API_KEY", "demo-key")
    os.environ.setdefault("APIFY_API_KEY", "demo-key")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    # Lancer la démonstration
    asyncio.run(main())




