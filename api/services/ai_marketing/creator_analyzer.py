# api/services/ai_marketing/creator_analyzer.py
"""
Analyseur de créateurs et système de segmentation par catégorie de contenu.
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from api.services.ai_marketing.logger import logger

class CreatorNiche(str, Enum):
    """Catégories de créateurs."""
    COSPLAY = "cosplay"
    FITNESS = "fitness"
    DOMINATRIX = "dominatrix"
    COUPLES = "couples"
    FOOT = "foot"
    ASMR = "asmr"
    GAMING = "gaming"
    COOKING = "cooking"
    TRAVEL = "travel"
    GENERAL = "general"

class PlatformPriority(str, Enum):
    """Priorité des plateformes par niche."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"

@dataclass
class CreatorProfile:
    """Profil complet d'un créateur."""
    creator_id: str
    username: str
    niche: CreatorNiche
    platforms: Dict[str, Dict[str, Any]]
    followers: Dict[str, int]
    engagement_rates: Dict[str, float]
    pricing: Dict[str, float]
    content_performance: Dict[str, Any]
    fan_segments: Dict[str, Any]
    demographics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

@dataclass
class NicheBenchmark:
    """Benchmarks par niche."""
    niche: CreatorNiche
    avg_subscription_price: float
    avg_ppv_conversion: float
    optimal_posting_frequency: Dict[str, int]
    primary_platforms: List[str]
    secondary_platforms: List[str]
    content_types: List[str]
    engagement_thresholds: Dict[str, float]

class CreatorAnalyzer:
    """Analyseur de créateurs et système de segmentation."""
    
    def __init__(self):
        self.niche_keywords = self._initialize_niche_keywords()
        self.benchmarks = self._initialize_benchmarks()
        
    def _initialize_niche_keywords(self) -> Dict[CreatorNiche, List[str]]:
        """Initialise les mots-clés par niche."""
        return {
            CreatorNiche.COSPLAY: [
                "cosplay", "costume", "character", "anime", "manga", "fantasy",
                "elf", "warrior", "princess", "superhero", "transformation",
                "convention", "comic", "nerd", "geek", "fandom"
            ],
            CreatorNiche.FITNESS: [
                "fitness", "workout", "gym", "exercise", "muscle", "strength",
                "cardio", "yoga", "pilates", "weight", "training", "body",
                "health", "nutrition", "diet", "protein", "supplements"
            ],
            CreatorNiche.DOMINATRIX: [
                "dominatrix", "domme", "mistress", "submissive", "bdsm",
                "fetish", "leather", "whip", "chain", "control", "power",
                "kink", "fetish", "dungeon", "slave", "master"
            ],
            CreatorNiche.COUPLES: [
                "couple", "relationship", "partner", "boyfriend", "girlfriend",
                "husband", "wife", "marriage", "love", "romance", "intimacy",
                "together", "duo", "pair", "relationship goals"
            ],
            CreatorNiche.FOOT: [
                "foot", "feet", "toes", "sole", "heel", "pedicure",
                "footjob", "foot worship", "barefoot", "shoes", "socks",
                "foot fetish", "foot massage", "foot care"
            ],
            CreatorNiche.ASMR: [
                "asmr", "whisper", "soft", "gentle", "relaxing", "sleep",
                "trigger", "tingles", "calm", "peaceful", "meditation",
                "sounds", "audio", "microphone", "binaural"
            ],
            CreatorNiche.GAMING: [
                "gaming", "gamer", "stream", "twitch", "youtube", "gameplay",
                "esports", "tournament", "console", "pc", "mobile", "indie",
                "rpg", "fps", "strategy", "multiplayer"
            ],
            CreatorNiche.COOKING: [
                "cooking", "recipe", "food", "kitchen", "chef", "baking",
                "ingredients", "meal", "dinner", "breakfast", "lunch",
                "healthy", "vegetarian", "vegan", "dessert"
            ],
            CreatorNiche.TRAVEL: [
                "travel", "trip", "vacation", "destination", "hotel", "flight",
                "adventure", "explore", "wanderlust", "backpack", "suitcase",
                "beach", "mountain", "city", "culture"
            ]
        }

    def _initialize_benchmarks(self) -> Dict[CreatorNiche, NicheBenchmark]:
        """Initialise les benchmarks par niche."""
        return {
            CreatorNiche.COSPLAY: NicheBenchmark(
                niche=CreatorNiche.COSPLAY,
                avg_subscription_price=19.99,
                avg_ppv_conversion=0.10,
                optimal_posting_frequency={"instagram": 2, "tiktok": 1, "reddit": 3, "twitter": 1},
                primary_platforms=["reddit", "twitter", "tiktok"],
                secondary_platforms=["instagram", "threads"],
                content_types=["transformations", "bts", "tutorials", "convention_content"],
                engagement_thresholds={"instagram": 0.05, "tiktok": 0.08, "reddit": 0.12}
            ),
            CreatorNiche.FITNESS: NicheBenchmark(
                niche=CreatorNiche.FITNESS,
                avg_subscription_price=24.99,
                avg_ppv_conversion=0.12,
                optimal_posting_frequency={"instagram": 2, "tiktok": 4, "youtube": 1},
                primary_platforms=["instagram", "tiktok"],
                secondary_platforms=["youtube", "twitter"],
                content_types=["workouts", "progress_pics", "nutrition_tips", "motivation"],
                engagement_thresholds={"instagram": 0.06, "tiktok": 0.10}
            ),
            CreatorNiche.DOMINATRIX: NicheBenchmark(
                niche=CreatorNiche.DOMINATRIX,
                avg_subscription_price=29.99,
                avg_ppv_conversion=0.15,
                optimal_posting_frequency={"reddit": 2, "twitter": 2, "fansly": 1},
                primary_platforms=["reddit", "twitter", "fansly"],
                secondary_platforms=["instagram", "tiktok"],
                content_types=["teasing", "commands", "custom_content", "fetish_content"],
                engagement_thresholds={"reddit": 0.15, "twitter": 0.08}
            ),
            CreatorNiche.COUPLES: NicheBenchmark(
                niche=CreatorNiche.COUPLES,
                avg_subscription_price=22.99,
                avg_ppv_conversion=0.11,
                optimal_posting_frequency={"instagram": 1, "tiktok": 2, "twitter": 1},
                primary_platforms=["instagram", "tiktok"],
                secondary_platforms=["twitter", "reddit"],
                content_types=["couple_content", "relationship_tips", "intimate_moments"],
                engagement_thresholds={"instagram": 0.07, "tiktok": 0.09}
            ),
            CreatorNiche.FOOT: NicheBenchmark(
                niche=CreatorNiche.FOOT,
                avg_subscription_price=17.99,
                avg_ppv_conversion=0.13,
                optimal_posting_frequency={"reddit": 2, "twitter": 1, "instagram": 1},
                primary_platforms=["reddit", "twitter"],
                secondary_platforms=["instagram", "fansly"],
                content_types=["foot_content", "pedicure", "foot_care", "shoes"],
                engagement_thresholds={"reddit": 0.14, "twitter": 0.09}
            ),
            CreatorNiche.ASMR: NicheBenchmark(
                niche=CreatorNiche.ASMR,
                avg_subscription_price=15.99,
                avg_ppv_conversion=0.09,
                optimal_posting_frequency={"youtube": 2, "tiktok": 1, "instagram": 1},
                primary_platforms=["youtube", "tiktok"],
                secondary_platforms=["instagram", "twitter"],
                content_types=["whisper_videos", "sound_content", "relaxation"],
                engagement_thresholds={"youtube": 0.05, "tiktok": 0.07}
            ),
            CreatorNiche.GAMING: NicheBenchmark(
                niche=CreatorNiche.GAMING,
                avg_subscription_price=12.99,
                avg_ppv_conversion=0.08,
                optimal_posting_frequency={"twitch": 3, "youtube": 2, "tiktok": 2},
                primary_platforms=["twitch", "youtube"],
                secondary_platforms=["tiktok", "twitter"],
                content_types=["gameplay", "streams", "reviews", "tips"],
                engagement_thresholds={"twitch": 0.03, "youtube": 0.04}
            ),
            CreatorNiche.COOKING: NicheBenchmark(
                niche=CreatorNiche.COOKING,
                avg_subscription_price=14.99,
                avg_ppv_conversion=0.07,
                optimal_posting_frequency={"instagram": 2, "tiktok": 3, "youtube": 1},
                primary_platforms=["instagram", "tiktok"],
                secondary_platforms=["youtube", "twitter"],
                content_types=["recipes", "cooking_tips", "food_photos", "tutorials"],
                engagement_thresholds={"instagram": 0.06, "tiktok": 0.08}
            ),
            CreatorNiche.TRAVEL: NicheBenchmark(
                niche=CreatorNiche.TRAVEL,
                avg_subscription_price=16.99,
                avg_ppv_conversion=0.06,
                optimal_posting_frequency={"instagram": 2, "tiktok": 2, "youtube": 1},
                primary_platforms=["instagram", "tiktok"],
                secondary_platforms=["youtube", "twitter"],
                content_types=["travel_photos", "destination_guides", "travel_tips"],
                engagement_thresholds={"instagram": 0.05, "tiktok": 0.07}
            )
        }

    async def analyze_creator(self, creator_data: Dict[str, Any]) -> CreatorProfile:
        """Analyse un créateur et génère son profil."""
        try:
            # Détecter la niche
            niche = await self._detect_niche(creator_data)
            
            # Analyser les plateformes
            platforms_analysis = await self._analyze_platforms(creator_data)
            
            # Calculer les métriques de performance
            performance_metrics = await self._calculate_performance_metrics(creator_data, niche)
            
            # Segmenter les fans
            fan_segments = await self._segment_fans(creator_data)
            
            # Analyser les démographiques
            demographics = await self._analyze_demographics(creator_data)
            
            # Créer le profil
            profile = CreatorProfile(
                creator_id=creator_data.get("creator_username", "unknown"),
                username=creator_data.get("creator_username", "unknown"),
                niche=niche,
                platforms=platforms_analysis,
                followers=self._extract_followers(creator_data),
                engagement_rates=self._calculate_engagement_rates(creator_data),
                pricing=self._extract_pricing(creator_data),
                content_performance=self._analyze_content_performance(creator_data),
                fan_segments=fan_segments,
                demographics=demographics,
                performance_metrics=performance_metrics,
                created_at=utcnow(),
                updated_at=utcnow()
            )
            
            logger.info(f"Profil créateur analysé: {profile.username} - Niche: {niche.value}")
            return profile
            
        except Exception as e:
            logger.error(f"Erreur analyse créateur: {e}")
            raise

    async def _detect_niche(self, creator_data: Dict[str, Any]) -> CreatorNiche:
        """Détecte la niche du créateur basée sur le contenu."""
        try:
            # Collecter tous les textes du créateur
            all_texts = []
            
            platforms = creator_data.get("platforms", {})
            for platform, data in platforms.items():
                if "posts" in data:
                    for post in data["posts"]:
                        if post.get("title"):
                            all_texts.append(post["title"])
                        if post.get("description"):
                            all_texts.append(post["description"])
                        if post.get("caption"):
                            all_texts.append(post["caption"])
                        if post.get("content"):
                            all_texts.append(post["content"])
            
            # Analyser les mots-clés
            niche_scores = {}
            combined_text = " ".join(all_texts).lower()
            
            for niche, keywords in self.niche_keywords.items():
                score = 0
                for keyword in keywords:
                    score += combined_text.count(keyword)
                
                # Normaliser le score par la longueur du texte
                if len(combined_text) > 0:
                    niche_scores[niche] = score / len(combined_text.split())
                else:
                    niche_scores[niche] = 0
            
            # Retourner la niche avec le score le plus élevé
            if niche_scores:
                best_niche = max(niche_scores.items(), key=lambda x: x[1])
                if best_niche[1] > 0.01:  # Seuil minimum
                    return best_niche[0]
            
            return CreatorNiche.GENERAL
            
        except Exception as e:
            logger.error(f"Erreur détection niche: {e}")
            return CreatorNiche.GENERAL

    async def _analyze_platforms(self, creator_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyse les performances par plateforme."""
        platforms_analysis = {}
        
        platforms = creator_data.get("platforms", {})
        for platform, data in platforms.items():
            analysis = {
                "followers": data.get("profile", {}).get("followers", 0),
                "engagement_rate": 0.0,
                "posting_frequency": 0.0,
                "content_performance": {},
                "optimal_posting_times": [],
                "hashtag_performance": {},
                "audience_demographics": {}
            }
            
            # Calculer le taux d'engagement
            posts = data.get("posts", [])
            if posts:
                total_engagement = 0
                total_followers = analysis["followers"]
                
                for post in posts:
                    likes = post.get("likes", 0)
                    comments = post.get("comments", 0)
                    shares = post.get("shares", 0)
                    post_engagement = likes + comments + shares
                    total_engagement += post_engagement
                
                if total_followers > 0 and len(posts) > 0:
                    analysis["engagement_rate"] = total_engagement / (total_followers * len(posts))
            
            # Analyser les performances de contenu
            content_types = {}
            for post in posts:
                content_type = post.get("media_type", "unknown")
                if content_type not in content_types:
                    content_types[content_type] = []
                
                engagement = post.get("likes", 0) + post.get("comments", 0)
                content_types[content_type].append(engagement)
            
            # Calculer les moyennes par type de contenu
            for content_type, engagements in content_types.items():
                analysis["content_performance"][content_type] = {
                    "avg_engagement": sum(engagements) / len(engagements),
                    "count": len(engagements),
                    "max_engagement": max(engagements)
                }
            
            platforms_analysis[platform] = analysis
        
        return platforms_analysis

    async def _calculate_performance_metrics(self, creator_data: Dict[str, Any], niche: CreatorNiche) -> Dict[str, Any]:
        """Calcule les métriques de performance."""
        benchmark = self.benchmarks.get(niche)
        if not benchmark:
            return {}
        
        metrics = {
            "pricing_vs_benchmark": {},
            "engagement_vs_benchmark": {},
            "platform_performance": {},
            "growth_potential": {},
            "optimization_opportunities": []
        }
        
        # Analyser le pricing
        platforms = creator_data.get("platforms", {})
        for platform, data in platforms.items():
            profile = data.get("profile", {})
            subscription_price = profile.get("subscription_price", 0)
            
            if subscription_price > 0:
                pricing_diff = subscription_price - benchmark.avg_subscription_price
                pricing_percent = (pricing_diff / benchmark.avg_subscription_price) * 100
                
                metrics["pricing_vs_benchmark"][platform] = {
                    "current_price": subscription_price,
                    "benchmark_price": benchmark.avg_subscription_price,
                    "difference": pricing_diff,
                    "percentage": pricing_percent,
                    "recommendation": "increase" if pricing_percent < -20 else "optimal" if pricing_percent < 20 else "decrease"
                }
        
        # Analyser l'engagement
        for platform, data in platforms.items():
            posts = data.get("posts", [])
            if posts:
                total_engagement = 0
                followers = data.get("profile", {}).get("followers", 0)
                
                for post in posts:
                    engagement = post.get("likes", 0) + post.get("comments", 0)
                    total_engagement += engagement
                
                if followers > 0 and len(posts) > 0:
                    engagement_rate = total_engagement / (followers * len(posts))
                    benchmark_rate = benchmark.engagement_thresholds.get(platform, 0.05)
                    
                    engagement_diff = engagement_rate - benchmark_rate
                    engagement_percent = (engagement_diff / benchmark_rate) * 100
                    
                    metrics["engagement_vs_benchmark"][platform] = {
                        "current_rate": engagement_rate,
                        "benchmark_rate": benchmark_rate,
                        "difference": engagement_diff,
                        "percentage": engagement_percent,
                        "status": "above" if engagement_percent > 0 else "below"
                    }
        
        return metrics

    async def _segment_fans(self, creator_data: Dict[str, Any]) -> Dict[str, Any]:
        """Segmente les fans par comportement."""
        segments = {
            "vip_fans": {"count": 0, "characteristics": []},
            "active_fans": {"count": 0, "characteristics": []},
            "dormant_fans": {"count": 0, "characteristics": []},
            "new_fans": {"count": 0, "characteristics": []},
            "at_risk_fans": {"count": 0, "characteristics": []}
        }
        
        # Simulation basée sur les données disponibles
        platforms = creator_data.get("platforms", {})
        total_followers = 0
        
        for platform, data in platforms.items():
            followers = data.get("profile", {}).get("followers", 0)
            total_followers += followers
        
        if total_followers > 0:
            # Estimation des segments (basée sur des moyennes de l'industrie)
            segments["vip_fans"]["count"] = int(total_followers * 0.05)  # 5%
            segments["active_fans"]["count"] = int(total_followers * 0.25)  # 25%
            segments["dormant_fans"]["count"] = int(total_followers * 0.40)  # 40%
            segments["new_fans"]["count"] = int(total_followers * 0.20)  # 20%
            segments["at_risk_fans"]["count"] = int(total_followers * 0.10)  # 10%
        
        return segments

    async def _analyze_demographics(self, creator_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les démographiques de l'audience."""
        demographics = {
            "age_groups": {},
            "gender_distribution": {},
            "geographic_distribution": {},
            "interests": [],
            "engagement_patterns": {}
        }
        
        # Analyse basée sur les commentaires et interactions
        platforms = creator_data.get("platforms", {})
        all_comments = []
        
        for platform, data in platforms.items():
            posts = data.get("posts", [])
            for post in posts:
                comments = post.get("comments", [])
                all_comments.extend(comments)
        
        # Analyse des intérêts basée sur les mots-clés dans les commentaires
        if all_comments:
            combined_comments = " ".join(all_comments).lower()
            
            # Mots-clés d'intérêt par niche
            interest_keywords = {
                "cosplay": ["love", "amazing", "perfect", "beautiful", "stunning"],
                "fitness": ["motivation", "inspiration", "goals", "workout", "strong"],
                "general": ["hot", "sexy", "gorgeous", "cute", "beautiful"]
            }
            
            for niche, keywords in interest_keywords.items():
                score = sum(combined_comments.count(keyword) for keyword in keywords)
                if score > 0:
                    demographics["interests"].append({"niche": niche, "score": score})
        
        return demographics

    def _extract_followers(self, creator_data: Dict[str, Any]) -> Dict[str, int]:
        """Extrait le nombre de followers par plateforme."""
        followers = {}
        
        platforms = creator_data.get("platforms", {})
        for platform, data in platforms.items():
            profile = data.get("profile", {})
            followers[platform] = profile.get("followers", 0)
        
        return followers

    def _calculate_engagement_rates(self, creator_data: Dict[str, Any]) -> Dict[str, float]:
        """Calcule les taux d'engagement par plateforme."""
        engagement_rates = {}
        
        platforms = creator_data.get("platforms", {})
        for platform, data in platforms.items():
            posts = data.get("posts", [])
            followers = data.get("profile", {}).get("followers", 0)
            
            if posts and followers > 0:
                total_engagement = 0
                for post in posts:
                    engagement = post.get("likes", 0) + post.get("comments", 0)
                    total_engagement += engagement
                
                engagement_rates[platform] = total_engagement / (followers * len(posts))
            else:
                engagement_rates[platform] = 0.0
        
        return engagement_rates

    def _extract_pricing(self, creator_data: Dict[str, Any]) -> Dict[str, float]:
        """Extrait les prix par plateforme."""
        pricing = {}
        
        platforms = creator_data.get("platforms", {})
        for platform, data in platforms.items():
            profile = data.get("profile", {})
            pricing[platform] = profile.get("subscription_price", 0.0)
        
        return pricing

    def _analyze_content_performance(self, creator_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les performances de contenu."""
        content_performance = {
            "top_performing_posts": [],
            "content_types": {},
            "posting_patterns": {},
            "engagement_trends": {}
        }
        
        platforms = creator_data.get("platforms", {})
        all_posts = []
        
        for platform, data in platforms.items():
            posts = data.get("posts", [])
            for post in posts:
                post["platform"] = platform
                all_posts.append(post)
        
        # Trier par engagement
        all_posts.sort(key=lambda x: x.get("likes", 0) + x.get("comments", 0), reverse=True)
        content_performance["top_performing_posts"] = all_posts[:10]
        
        return content_performance

    async def get_niche_recommendations(self, niche: CreatorNiche) -> Dict[str, Any]:
        """Récupère les recommandations spécifiques à une niche."""
        benchmark = self.benchmarks.get(niche)
        if not benchmark:
            return {}
        
        return {
            "optimal_pricing": benchmark.avg_subscription_price,
            "primary_platforms": benchmark.primary_platforms,
            "secondary_platforms": benchmark.secondary_platforms,
            "content_types": benchmark.content_types,
            "posting_frequency": benchmark.optimal_posting_frequency,
            "engagement_thresholds": benchmark.engagement_thresholds,
            "growth_strategies": await self._get_growth_strategies(niche)
        }

    async def _get_growth_strategies(self, niche: CreatorNiche) -> List[str]:
        """Génère des stratégies de croissance par niche."""
        strategies = {
            CreatorNiche.COSPLAY: [
                "Participer aux conventions et événements cosplay",
                "Collaborer avec d'autres cosplayers",
                "Créer du contenu éducatif sur les techniques de cosplay",
                "Utiliser les tendances anime/manga populaires"
            ],
            CreatorNiche.FITNESS: [
                "Partager des transformations avant/après",
                "Créer des programmes d'entraînement",
                "Collaborer avec des marques de fitness",
                "Participer aux défis fitness populaires"
            ],
            CreatorNiche.DOMINATRIX: [
                "Créer du contenu éducatif sur le BDSM",
                "Participer aux communautés Reddit spécialisées",
                "Offrir des sessions personnalisées",
                "Développer une présence sur les plateformes spécialisées"
            ]
        }
        
        return strategies.get(niche, [
            "Créer du contenu de qualité régulièrement",
            "Interagir avec l'audience",
            "Utiliser les tendances populaires",
            "Collaborer avec d'autres créateurs"
        ])



