# api/services/ai_marketing/recommendation_engine.py
"""
Moteur de recommandations IA pour les créateurs.
Génère des recommandations personnalisées basées sur l'analyse des données.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import openai
from openai import AsyncOpenAI

from api.services.ai_marketing.logger import logger
from api.services.ai_marketing.rag_system import RAGSystem
from api.services.ai_marketing.creator_analyzer import CreatorAnalyzer, CreatorProfile, CreatorNiche

@dataclass
class Recommendation:
    """Recommandation générée par l'IA."""
    id: str
    category: str
    title: str
    description: str
    priority: str  # high, medium, low
    impact_score: float  # 0-1
    effort_score: float  # 0-1
    timeline: str
    expected_outcome: str
    implementation_steps: List[str]
    metrics_to_track: List[str]
    created_at: datetime

@dataclass
class ContentRecommendation:
    """Recommandation de contenu."""
    content_type: str
    platform: str
    title_suggestion: str
    description_template: str
    hashtags: List[str]
    optimal_posting_time: str
    expected_engagement: float
    cross_platform_adaptation: Dict[str, str]

@dataclass
class PricingRecommendation:
    """Recommandation de pricing."""
    platform: str
    current_price: float
    recommended_price: float
    price_change_percentage: float
    justification: str
    risk_assessment: str
    implementation_strategy: str
    expected_impact: str

@dataclass
class AcquisitionRecommendation:
    """Recommandation d'acquisition."""
    platform: str
    strategy: str
    content_suggestions: List[str]
    hashtag_strategy: List[str]
    collaboration_opportunities: List[str]
    expected_growth: str
    timeline: str
    budget_estimate: str

class RecommendationEngine:
    """Moteur de recommandations IA."""
    
    def __init__(self):
        self.rag_system = RAGSystem()
        self.creator_analyzer = CreatorAnalyzer()
        
        # Configuration OpenAI/DeepSeek
        self.openai_client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        
        self.model_name = os.getenv("AI_MODEL_NAME", "gpt-4")
        
    async def initialize(self):
        """Initialise le moteur de recommandations."""
        await self.rag_system.initialize()
        logger.info("Moteur de recommandations IA initialisé")

    async def generate_recommendations(self, creator_profile: CreatorProfile, creator_data: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations personnalisées pour un créateur."""
        try:
            recommendations = []
            
            # Générer des recommandations par catégorie
            content_recs = await self._generate_content_recommendations(creator_profile, creator_data)
            pricing_recs = await self._generate_pricing_recommendations(creator_profile, creator_data)
            acquisition_recs = await self._generate_acquisition_recommendations(creator_profile, creator_data)
            engagement_recs = await self._generate_engagement_recommendations(creator_profile, creator_data)
            optimization_recs = await self._generate_optimization_recommendations(creator_profile, creator_data)
            
            # Combiner toutes les recommandations
            recommendations.extend(content_recs)
            recommendations.extend(pricing_recs)
            recommendations.extend(acquisition_recs)
            recommendations.extend(engagement_recs)
            recommendations.extend(optimization_recs)
            
            # Trier par priorité et impact
            recommendations.sort(key=lambda x: (x.priority == "high", x.impact_score), reverse=True)
            
            logger.info(f"Généré {len(recommendations)} recommandations pour {creator_profile.username}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations: {e}")
            return []

    async def _generate_content_recommendations(self, profile: CreatorProfile, data: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations de contenu."""
        recommendations = []
        
        try:
            # Analyser les performances de contenu
            content_performance = profile.content_performance
            platforms = profile.platforms
            
            # Identifier les plateformes sous-exploitées
            niche_benchmark = self.creator_analyzer.benchmarks.get(profile.niche)
            if not niche_benchmark:
                return recommendations
            
            for platform, analysis in platforms.items():
                engagement_rate = analysis.get("engagement_rate", 0)
                benchmark_rate = niche_benchmark.engagement_thresholds.get(platform, 0.05)
                
                if engagement_rate < benchmark_rate:
                    # Recommandation pour améliorer l'engagement
                    rec = Recommendation(
                        id=f"content_engagement_{platform}",
                        category="content",
                        title=f"Améliorer l'engagement sur {platform.title()}",
                        description=f"Votre taux d'engagement sur {platform} ({engagement_rate:.2%}) est inférieur au benchmark ({benchmark_rate:.2%}).",
                        priority="high" if engagement_rate < benchmark_rate * 0.5 else "medium",
                        impact_score=0.8,
                        effort_score=0.6,
                        timeline="2-4 semaines",
                        expected_outcome=f"Augmentation de l'engagement de {benchmark_rate - engagement_rate:.2%}",
                        implementation_steps=[
                            f"Analyser les posts les plus performants sur {platform}",
                            "Adapter le format de contenu aux préférences de l'audience",
                            "Optimiser les heures de publication",
                            "Améliorer la qualité visuelle du contenu"
                        ],
                        metrics_to_track=["engagement_rate", "reach", "impressions", "saves"],
                        created_at=utcnow()
                    )
                    recommendations.append(rec)
            
            # Recommandations spécifiques au contenu
            content_recs = await self._get_ai_content_recommendations(profile, data)
            recommendations.extend(content_recs)
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations contenu: {e}")
        
        return recommendations

    async def _generate_pricing_recommendations(self, profile: CreatorProfile, data: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations de pricing."""
        recommendations = []
        
        try:
            niche_benchmark = self.creator_analyzer.benchmarks.get(profile.niche)
            if not niche_benchmark:
                return recommendations
            
            for platform, current_price in profile.pricing.items():
                if current_price > 0:
                    benchmark_price = niche_benchmark.avg_subscription_price
                    price_diff_percent = ((current_price - benchmark_price) / benchmark_price) * 100
                    
                    if price_diff_percent < -20:  # Sous-évalué
                        rec = Recommendation(
                            id=f"pricing_increase_{platform}",
                            category="pricing",
                            title=f"Augmenter le prix d'abonnement sur {platform.title()}",
                            description=f"Votre prix actuel (${current_price}) est {abs(price_diff_percent):.1f}% en dessous du benchmark de votre niche (${benchmark_price}).",
                            priority="high",
                            impact_score=0.9,
                            effort_score=0.2,
                            timeline="1 semaine",
                            expected_outcome=f"Augmentation des revenus de {abs(price_diff_percent):.1f}%",
                            implementation_steps=[
                                "Tester le nouveau prix sur 20% des nouveaux abonnés",
                                "Communiquer la valeur ajoutée du contenu",
                                "Offrir une période de transition",
                                "Monitorer les métriques de rétention"
                            ],
                            metrics_to_track=["revenue", "retention_rate", "new_subscribers", "churn_rate"],
                            created_at=utcnow()
                        )
                        recommendations.append(rec)
                    
                    elif price_diff_percent > 30:  # Sur-évalué
                        rec = Recommendation(
                            id=f"pricing_decrease_{platform}",
                            category="pricing",
                            title=f"Considérer une réduction de prix sur {platform.title()}",
                            description=f"Votre prix actuel (${current_price}) est {price_diff_percent:.1f}% au-dessus du benchmark. Cela pourrait limiter l'acquisition.",
                            priority="medium",
                            impact_score=0.6,
                            effort_score=0.3,
                            timeline="2 semaines",
                            expected_outcome="Augmentation du nombre d'abonnés",
                            implementation_steps=[
                                "Analyser les données de conversion",
                                "Tester une réduction progressive",
                                "Optimiser la valeur perçue",
                                "Améliorer la qualité du contenu"
                            ],
                            metrics_to_track=["conversion_rate", "new_subscribers", "revenue", "retention_rate"],
                            created_at=utcnow()
                        )
                        recommendations.append(rec)
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations pricing: {e}")
        
        return recommendations

    async def _generate_acquisition_recommendations(self, profile: CreatorProfile, data: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations d'acquisition."""
        recommendations = []
        
        try:
            niche_benchmark = self.creator_analyzer.benchmarks.get(profile.niche)
            if not niche_benchmark:
                return recommendations
            
            # Identifier les plateformes sous-exploitées
            current_platforms = set(profile.platforms.keys())
            primary_platforms = set(niche_benchmark.primary_platforms)
            secondary_platforms = set(niche_benchmark.secondary_platforms)
            
            missing_primary = primary_platforms - current_platforms
            missing_secondary = secondary_platforms - current_platforms
            
            for platform in missing_primary:
                rec = Recommendation(
                    id=f"acquisition_primary_{platform}",
                    category="acquisition",
                    title=f"Créer une présence sur {platform.title()}",
                    description=f"{platform.title()} est une plateforme primaire pour votre niche ({profile.niche.value}) mais vous n'y êtes pas présent.",
                    priority="high",
                    impact_score=0.8,
                    effort_score=0.7,
                    timeline="1-2 mois",
                    expected_outcome="Nouveau canal d'acquisition significatif",
                    implementation_steps=[
                        f"Créer un profil optimisé sur {platform}",
                        "Adapter le contenu existant au format de la plateforme",
                        "Développer une stratégie de contenu spécifique",
                        "Cross-promouvoir depuis les plateformes existantes"
                    ],
                    metrics_to_track=["followers", "engagement_rate", "conversion_to_of", "reach"],
                    created_at=utcnow()
                )
                recommendations.append(rec)
            
            for platform in missing_secondary:
                rec = Recommendation(
                    id=f"acquisition_secondary_{platform}",
                    category="acquisition",
                    title=f"Considérer une présence sur {platform.title()}",
                    description=f"{platform.title()} pourrait être un canal d'acquisition complémentaire pour votre niche.",
                    priority="medium",
                    impact_score=0.5,
                    effort_score=0.6,
                    timeline="2-3 mois",
                    expected_outcome="Canal d'acquisition supplémentaire",
                    implementation_steps=[
                        f"Évaluer la pertinence de {platform} pour votre audience",
                        "Créer du contenu pilote",
                        "Mesurer l'engagement initial",
                        "Décider de l'investissement à long terme"
                    ],
                    metrics_to_track=["followers", "engagement_rate", "conversion_rate"],
                    created_at=utcnow()
                )
                recommendations.append(rec)
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations acquisition: {e}")
        
        return recommendations

    async def _generate_engagement_recommendations(self, profile: CreatorProfile, data: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations d'engagement."""
        recommendations = []
        
        try:
            # Analyser les segments de fans
            fan_segments = profile.fan_segments
            
            # Recommandation pour les fans dormants
            dormant_count = fan_segments.get("dormant_fans", {}).get("count", 0)
            if dormant_count > 0:
                rec = Recommendation(
                    id="engagement_dormant_fans",
                    category="engagement",
                    title="Réactiver les fans dormants",
                    description=f"Vous avez {dormant_count} fans dormants qui pourraient être réactivés.",
                    priority="medium",
                    impact_score=0.7,
                    effort_score=0.5,
                    timeline="2-3 semaines",
                    expected_outcome="Augmentation de l'engagement et des revenus",
                    implementation_steps=[
                        "Identifier les fans inactifs depuis plus de 30 jours",
                        "Envoyer des messages personnalisés de réactivation",
                        "Offrir du contenu exclusif ou des promotions",
                        "Créer des sondages pour comprendre leurs préférences"
                    ],
                    metrics_to_track=["active_fans", "engagement_rate", "revenue", "retention_rate"],
                    created_at=utcnow()
                )
                recommendations.append(rec)
            
            # Recommandation pour les nouveaux fans
            new_count = fan_segments.get("new_fans", {}).get("count", 0)
            if new_count > 0:
                rec = Recommendation(
                    id="engagement_new_fans",
                    category="engagement",
                    title="Optimiser l'onboarding des nouveaux fans",
                    description=f"Améliorer l'expérience des {new_count} nouveaux fans pour augmenter la rétention.",
                    priority="high",
                    impact_score=0.8,
                    effort_score=0.4,
                    timeline="1 semaine",
                    expected_outcome="Amélioration de la rétention des nouveaux fans",
                    implementation_steps=[
                        "Créer une séquence d'onboarding personnalisée",
                        "Envoyer du contenu de bienvenue exclusif",
                        "Proposer des bundles découverte à prix réduit",
                        "Programmer des interactions régulières"
                    ],
                    metrics_to_track=["retention_rate", "engagement_rate", "conversion_rate", "satisfaction_score"],
                    created_at=utcnow()
                )
                recommendations.append(rec)
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations engagement: {e}")
        
        return recommendations

    async def _generate_optimization_recommendations(self, profile: CreatorProfile, data: Dict[str, Any]) -> List[Recommendation]:
        """Génère des recommandations d'optimisation."""
        recommendations = []
        
        try:
            # Analyser les métriques de performance
            performance_metrics = profile.performance_metrics
            
            # Recommandations basées sur les performances vs benchmarks
            for platform, metrics in performance_metrics.get("engagement_vs_benchmark", {}).items():
                if metrics.get("status") == "below":
                    rec = Recommendation(
                        id=f"optimization_engagement_{platform}",
                        category="optimization",
                        title=f"Optimiser les performances sur {platform.title()}",
                        description=f"Vos performances sur {platform} sont en dessous des benchmarks de votre niche.",
                        priority="medium",
                        impact_score=0.6,
                        effort_score=0.7,
                        timeline="3-4 semaines",
                        expected_outcome="Amélioration des métriques de performance",
                        implementation_steps=[
                            "Analyser les contenus les plus performants",
                            "Optimiser les heures de publication",
                            "Améliorer la qualité du contenu",
                            "Tester de nouveaux formats"
                        ],
                        metrics_to_track=["engagement_rate", "reach", "impressions", "saves"],
                        created_at=utcnow()
                    )
                    recommendations.append(rec)
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations optimisation: {e}")
        
        return recommendations

    async def _get_ai_content_recommendations(self, profile: CreatorProfile, data: Dict[str, Any]) -> List[Recommendation]:
        """Utilise l'IA pour générer des recommandations de contenu personnalisées."""
        try:
            # Construire le contexte pour l'IA
            context = await self._build_ai_context(profile, data)
            
            # Générer des recommandations avec l'IA
            prompt = f"""
            En tant qu'expert en marketing digital pour créateurs de contenu, analysez ce profil et générez 3 recommandations de contenu spécifiques et actionnables.

            Profil du créateur:
            {context}

            Génère des recommandations qui incluent:
            - Type de contenu spécifique
            - Plateforme recommandée
            - Stratégie de publication
            - Hashtags suggérés
            - Timing optimal

            Format de réponse en JSON:
            {{
                "recommendations": [
                    {{
                        "title": "Titre de la recommandation",
                        "description": "Description détaillée",
                        "content_type": "Type de contenu",
                        "platform": "Plateforme recommandée",
                        "strategy": "Stratégie détaillée",
                        "hashtags": ["hashtag1", "hashtag2"],
                        "timing": "Timing optimal",
                        "expected_impact": "Impact attendu"
                    }}
                ]
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Tu es un expert en marketing digital spécialisé dans les créateurs de contenu. Tu génères des recommandations précises et actionnables."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parser la réponse
            ai_response = response.choices[0].message.content
            recommendations_data = json.loads(ai_response)
            
            # Convertir en objets Recommendation
            ai_recommendations = []
            for i, rec_data in enumerate(recommendations_data.get("recommendations", [])):
                rec = Recommendation(
                    id=f"ai_content_{i}",
                    category="content",
                    title=rec_data.get("title", "Recommandation IA"),
                    description=rec_data.get("description", ""),
                    priority="medium",
                    impact_score=0.7,
                    effort_score=0.6,
                    timeline="1-2 semaines",
                    expected_outcome=rec_data.get("expected_impact", ""),
                    implementation_steps=[
                        f"Type de contenu: {rec_data.get('content_type', '')}",
                        f"Plateforme: {rec_data.get('platform', '')}",
                        f"Stratégie: {rec_data.get('strategy', '')}",
                        f"Hashtags: {', '.join(rec_data.get('hashtags', []))}",
                        f"Timing: {rec_data.get('timing', '')}"
                    ],
                    metrics_to_track=["engagement_rate", "reach", "impressions", "saves"],
                    created_at=utcnow()
                )
                ai_recommendations.append(rec)
            
            return ai_recommendations
            
        except Exception as e:
            logger.error(f"Erreur génération recommandations IA: {e}")
            return []

    async def _build_ai_context(self, profile: CreatorProfile, data: Dict[str, Any]) -> str:
        """Construit le contexte pour l'IA."""
        context = f"""
        Informations du créateur:
        - Username: {profile.username}
        - Niche: {profile.niche.value}
        - Plateformes: {', '.join(profile.platforms.keys())}
        - Followers: {profile.followers}
        - Prix abonnement: {profile.pricing}
        - Taux d'engagement: {profile.engagement_rates}
        
        Performances de contenu:
        - Top posts: {len(profile.content_performance.get('top_performing_posts', []))} posts analysés
        - Types de contenu: {list(profile.content_performance.get('content_types', {}).keys())}
        
        Segments de fans:
        - VIP: {profile.fan_segments.get('vip_fans', {}).get('count', 0)}
        - Actifs: {profile.fan_segments.get('active_fans', {}).get('count', 0)}
        - Dormants: {profile.fan_segments.get('dormant_fans', {}).get('count', 0)}
        - Nouveaux: {profile.fan_segments.get('new_fans', {}).get('count', 0)}
        """
        
        return context

    async def generate_content_suggestions(self, profile: CreatorProfile, platform: str, content_type: str) -> ContentRecommendation:
        """Génère des suggestions de contenu spécifiques."""
        try:
            # Utiliser l'IA pour générer des suggestions
            prompt = f"""
            Génère une suggestion de contenu spécifique pour:
            - Créateur: {profile.username}
            - Niche: {profile.niche.value}
            - Plateforme: {platform}
            - Type de contenu: {content_type}
            
            Inclus:
            - Titre accrocheur
            - Description template
            - Hashtags optimisés
            - Timing de publication
            - Adaptation cross-platform
            
            Format JSON:
            {{
                "title": "Titre suggéré",
                "description": "Template de description",
                "hashtags": ["hashtag1", "hashtag2"],
                "timing": "Timing optimal",
                "cross_platform": {{
                    "instagram": "Adaptation pour Instagram",
                    "tiktok": "Adaptation pour TikTok"
                }},
                "expected_engagement": 0.08
            }}
            """
            
            response = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Tu es un expert en création de contenu pour les réseaux sociaux."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=800
            )
            
            ai_response = response.choices[0].message.content
            suggestion_data = json.loads(ai_response)
            
            return ContentRecommendation(
                content_type=content_type,
                platform=platform,
                title_suggestion=suggestion_data.get("title", ""),
                description_template=suggestion_data.get("description", ""),
                hashtags=suggestion_data.get("hashtags", []),
                optimal_posting_time=suggestion_data.get("timing", ""),
                expected_engagement=suggestion_data.get("expected_engagement", 0.05),
                cross_platform_adaptation=suggestion_data.get("cross_platform", {})
            )
            
        except Exception as e:
            logger.error(f"Erreur génération suggestions contenu: {e}")
            return ContentRecommendation(
                content_type=content_type,
                platform=platform,
                title_suggestion="Suggestion par défaut",
                description_template="Description template",
                hashtags=[],
                optimal_posting_time="Timing optimal",
                expected_engagement=0.05,
                cross_platform_adaptation={}
            )

    async def generate_weekly_action_plan(self, profile: CreatorProfile, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Génère un plan d'action hebdomadaire basé sur les recommandations."""
        try:
            # Filtrer les recommandations prioritaires
            high_priority = [r for r in recommendations if r.priority == "high"]
            medium_priority = [r for r in recommendations if r.priority == "medium"]
            
            # Organiser par jour de la semaine
            weekly_plan = {
                "monday": [],
                "tuesday": [],
                "wednesday": [],
                "thursday": [],
                "friday": [],
                "saturday": [],
                "sunday": []
            }
            
            # Distribuer les tâches sur la semaine
            all_tasks = high_priority + medium_priority[:5]  # Limiter à 8 tâches max
            
            for i, rec in enumerate(all_tasks):
                day = list(weekly_plan.keys())[i % 7]
                weekly_plan[day].append({
                    "title": rec.title,
                    "description": rec.description,
                    "timeline": rec.timeline,
                    "effort_score": rec.effort_score,
                    "impact_score": rec.impact_score,
                    "implementation_steps": rec.implementation_steps[:3]  # Limiter à 3 étapes
                })
            
            return {
                "creator_username": profile.username,
                "week_start": utcnow().strftime("%Y-%m-%d"),
                "total_tasks": len(all_tasks),
                "high_priority_tasks": len(high_priority),
                "medium_priority_tasks": len(medium_priority),
                "daily_plan": weekly_plan,
                "weekly_goals": [
                    "Améliorer l'engagement sur les plateformes principales",
                    "Optimiser le pricing selon les benchmarks",
                    "Réactiver les fans dormants",
                    "Créer du contenu de qualité régulièrement"
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur génération plan hebdomadaire: {e}")
            return {}




