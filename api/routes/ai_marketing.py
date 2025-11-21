# api/routes/ai_marketing.py
"""
Routes API pour le module IA Marketing & Business.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from api.services.ai_marketing.data_collector import DataCollector, PlatformType
from api.services.ai_marketing.creator_analyzer import CreatorAnalyzer, CreatorNiche
from api.services.ai_marketing.recommendation_engine import RecommendationEngine
from api.services.ai_marketing.logger import logger

router = APIRouter()

# Modèles Pydantic pour les requêtes/réponses
class CreatorAnalysisRequest(BaseModel):
    """Requête d'analyse de créateur."""
    creator_username: str = Field(..., description="Nom d'utilisateur du créateur")
    platforms: List[str] = Field(..., description="Plateformes à analyser")
    include_recommendations: bool = Field(True, description="Inclure les recommandations IA")

class ContentSuggestionRequest(BaseModel):
    """Requête de suggestion de contenu."""
    creator_username: str = Field(..., description="Nom d'utilisateur du créateur")
    platform: str = Field(..., description="Plateforme cible")
    content_type: str = Field(..., description="Type de contenu souhaité")
    niche: Optional[str] = Field(None, description="Niche du créateur")

class RecommendationRequest(BaseModel):
    """Requête de recommandations."""
    creator_username: str = Field(..., description="Nom d'utilisateur du créateur")
    platforms: List[str] = Field(..., description="Plateformes à analyser")
    categories: Optional[List[str]] = Field(None, description="Catégories de recommandations")

class WeeklyPlanRequest(BaseModel):
    """Requête de plan hebdomadaire."""
    creator_username: str = Field(..., description="Nom d'utilisateur du créateur")
    platforms: List[str] = Field(..., description="Plateformes à analyser")

# Réponses
class CreatorAnalysisResponse(BaseModel):
    """Réponse d'analyse de créateur."""
    creator_id: str
    username: str
    niche: str
    platforms: Dict[str, Any]
    followers: Dict[str, int]
    engagement_rates: Dict[str, float]
    pricing: Dict[str, float]
    performance_metrics: Dict[str, Any]
    fan_segments: Dict[str, Any]
    recommendations: Optional[List[Dict[str, Any]]] = None
    analysis_timestamp: datetime

class ContentSuggestionResponse(BaseModel):
    """Réponse de suggestion de contenu."""
    content_type: str
    platform: str
    title_suggestion: str
    description_template: str
    hashtags: List[str]
    optimal_posting_time: str
    expected_engagement: float
    cross_platform_adaptation: Dict[str, str]

class RecommendationResponse(BaseModel):
    """Réponse de recommandations."""
    creator_username: str
    total_recommendations: int
    recommendations_by_category: Dict[str, int]
    recommendations: List[Dict[str, Any]]
    generated_at: datetime

class WeeklyPlanResponse(BaseModel):
    """Réponse de plan hebdomadaire."""
    creator_username: str
    week_start: str
    total_tasks: int
    high_priority_tasks: int
    medium_priority_tasks: int
    daily_plan: Dict[str, List[Dict[str, Any]]]
    weekly_goals: List[str]

# Instance globale des services
data_collector = DataCollector()
creator_analyzer = CreatorAnalyzer()
recommendation_engine = RecommendationEngine()

@router.on_event("startup")
async def startup_event():
    """Initialise les services au démarrage."""
    try:
        await recommendation_engine.initialize()
        logger.info("Services IA Marketing initialisés")
    except Exception as e:
        logger.error(f"Erreur initialisation services: {e}")

@router.post("/analyze-creator", response_model=CreatorAnalysisResponse)
async def analyze_creator(request: CreatorAnalysisRequest):
    """
    Analyse un créateur et génère son profil complet.
    """
    try:
        logger.info(f"Début analyse créateur: {request.creator_username}")
        
        # Collecter les données
        async with data_collector:
            platforms = [PlatformType(p) for p in request.platforms if p in PlatformType.__members__.values()]
            creator_data = await data_collector.collect_all_platform_data(request.creator_username, platforms)
        
        # Analyser le créateur
        creator_profile = await creator_analyzer.analyze_creator(creator_data)
        
        # Générer les recommandations si demandé
        recommendations = None
        if request.include_recommendations:
            recommendations_data = await recommendation_engine.generate_recommendations(creator_profile, creator_data)
            recommendations = [
                {
                    "id": rec.id,
                    "category": rec.category,
                    "title": rec.title,
                    "description": rec.description,
                    "priority": rec.priority,
                    "impact_score": rec.impact_score,
                    "effort_score": rec.effort_score,
                    "timeline": rec.timeline,
                    "expected_outcome": rec.expected_outcome,
                    "implementation_steps": rec.implementation_steps,
                    "metrics_to_track": rec.metrics_to_track
                }
                for rec in recommendations_data
            ]
        
        response = CreatorAnalysisResponse(
            creator_id=creator_profile.creator_id,
            username=creator_profile.username,
            niche=creator_profile.niche.value,
            platforms=creator_profile.platforms,
            followers=creator_profile.followers,
            engagement_rates=creator_profile.engagement_rates,
            pricing=creator_profile.pricing,
            performance_metrics=creator_profile.performance_metrics,
            fan_segments=creator_profile.fan_segments,
            recommendations=recommendations,
            analysis_timestamp=utcnow()
        )
        
        logger.info(f"Analyse créateur terminée: {request.creator_username}")
        return response
        
    except Exception as e:
        logger.error(f"Erreur analyse créateur {request.creator_username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/content-suggestion", response_model=ContentSuggestionResponse)
async def get_content_suggestion(request: ContentSuggestionRequest):
    """
    Génère une suggestion de contenu personnalisée.
    """
    try:
        logger.info(f"Génération suggestion contenu pour {request.creator_username}")
        
        # Collecter les données de base
        async with data_collector:
            platforms = [PlatformType.INSTAGRAM, PlatformType.TIKTOK]  # Plateformes de base
            creator_data = await data_collector.collect_all_platform_data(request.creator_username, platforms)
        
        # Analyser le créateur
        creator_profile = await creator_analyzer.analyze_creator(creator_data)
        
        # Générer la suggestion
        suggestion = await recommendation_engine.generate_content_suggestions(
            creator_profile, 
            request.platform, 
            request.content_type
        )
        
        response = ContentSuggestionResponse(
            content_type=suggestion.content_type,
            platform=suggestion.platform,
            title_suggestion=suggestion.title_suggestion,
            description_template=suggestion.description_template,
            hashtags=suggestion.hashtags,
            optimal_posting_time=suggestion.optimal_posting_time,
            expected_engagement=suggestion.expected_engagement,
            cross_platform_adaptation=suggestion.cross_platform_adaptation
        )
        
        logger.info(f"Suggestion contenu générée pour {request.creator_username}")
        return response
        
    except Exception as e:
        logger.error(f"Erreur génération suggestion contenu: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Génère des recommandations personnalisées pour un créateur.
    """
    try:
        logger.info(f"Génération recommandations pour {request.creator_username}")
        
        # Collecter les données
        async with data_collector:
            platforms = [PlatformType(p) for p in request.platforms if p in PlatformType.__members__.values()]
            creator_data = await data_collector.collect_all_platform_data(request.creator_username, platforms)
        
        # Analyser le créateur
        creator_profile = await creator_analyzer.analyze_creator(creator_data)
        
        # Générer les recommandations
        recommendations_data = await recommendation_engine.generate_recommendations(creator_profile, creator_data)
        
        # Filtrer par catégories si spécifié
        if request.categories:
            recommendations_data = [r for r in recommendations_data if r.category in request.categories]
        
        # Organiser par catégorie
        recommendations_by_category = {}
        for rec in recommendations_data:
            category = rec.category
            if category not in recommendations_by_category:
                recommendations_by_category[category] = 0
            recommendations_by_category[category] += 1
        
        # Convertir en format de réponse
        recommendations = [
            {
                "id": rec.id,
                "category": rec.category,
                "title": rec.title,
                "description": rec.description,
                "priority": rec.priority,
                "impact_score": rec.impact_score,
                "effort_score": rec.effort_score,
                "timeline": rec.timeline,
                "expected_outcome": rec.expected_outcome,
                "implementation_steps": rec.implementation_steps,
                "metrics_to_track": rec.metrics_to_track
            }
            for rec in recommendations_data
        ]
        
        response = RecommendationResponse(
            creator_username=request.creator_username,
            total_recommendations=len(recommendations),
            recommendations_by_category=recommendations_by_category,
            recommendations=recommendations,
            generated_at=utcnow()
        )
        
        logger.info(f"Recommandations générées pour {request.creator_username}: {len(recommendations)} recommandations")
        return response
        
    except Exception as e:
        logger.error(f"Erreur génération recommandations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/weekly-plan", response_model=WeeklyPlanResponse)
async def get_weekly_plan(request: WeeklyPlanRequest):
    """
    Génère un plan d'action hebdomadaire personnalisé.
    """
    try:
        logger.info(f"Génération plan hebdomadaire pour {request.creator_username}")
        
        # Collecter les données
        async with data_collector:
            platforms = [PlatformType(p) for p in request.platforms if p in PlatformType.__members__.values()]
            creator_data = await data_collector.collect_all_platform_data(request.creator_username, platforms)
        
        # Analyser le créateur
        creator_profile = await creator_analyzer.analyze_creator(creator_data)
        
        # Générer les recommandations
        recommendations_data = await recommendation_engine.generate_recommendations(creator_profile, creator_data)
        
        # Générer le plan hebdomadaire
        weekly_plan = await recommendation_engine.generate_weekly_action_plan(creator_profile, recommendations_data)
        
        response = WeeklyPlanResponse(
            creator_username=weekly_plan.get("creator_username", request.creator_username),
            week_start=weekly_plan.get("week_start", utcnow().strftime("%Y-%m-%d")),
            total_tasks=weekly_plan.get("total_tasks", 0),
            high_priority_tasks=weekly_plan.get("high_priority_tasks", 0),
            medium_priority_tasks=weekly_plan.get("medium_priority_tasks", 0),
            daily_plan=weekly_plan.get("daily_plan", {}),
            weekly_goals=weekly_plan.get("weekly_goals", [])
        )
        
        logger.info(f"Plan hebdomadaire généré pour {request.creator_username}")
        return response
        
    except Exception as e:
        logger.error(f"Erreur génération plan hebdomadaire: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/niche-benchmarks/{niche}")
async def get_niche_benchmarks(niche: str):
    """
    Récupère les benchmarks pour une niche spécifique.
    """
    try:
        # Valider la niche
        try:
            niche_enum = CreatorNiche(niche.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Niche non supportée: {niche}")
        
        # Récupérer les benchmarks
        benchmarks = creator_analyzer.benchmarks.get(niche_enum)
        if not benchmarks:
            raise HTTPException(status_code=404, detail=f"Benchmarks non trouvés pour la niche: {niche}")
        
        return {
            "niche": benchmarks.niche.value,
            "avg_subscription_price": benchmarks.avg_subscription_price,
            "avg_ppv_conversion": benchmarks.avg_ppv_conversion,
            "optimal_posting_frequency": benchmarks.optimal_posting_frequency,
            "primary_platforms": benchmarks.primary_platforms,
            "secondary_platforms": benchmarks.secondary_platforms,
            "content_types": benchmarks.content_types,
            "engagement_thresholds": benchmarks.engagement_thresholds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-niches")
async def get_supported_niches():
    """
    Récupère la liste des niches supportées.
    """
    return {
        "niches": [niche.value for niche in CreatorNiche],
        "total_count": len(CreatorNiche)
    }

@router.get("/supported-platforms")
async def get_supported_platforms():
    """
    Récupère la liste des plateformes supportées.
    """
    return {
        "platforms": [platform.value for platform in PlatformType],
        "total_count": len(PlatformType)
    }

@router.post("/collect-data")
async def collect_platform_data(
    creator_username: str,
    platforms: List[str],
    background_tasks: BackgroundTasks
):
    """
    Lance la collecte de données en arrière-plan.
    """
    try:
        # Valider les plateformes
        valid_platforms = []
        for platform in platforms:
            if platform in PlatformType.__members__.values():
                valid_platforms.append(PlatformType(platform))
            else:
                logger.warning(f"Plateforme non supportée: {platform}")
        
        if not valid_platforms:
            raise HTTPException(status_code=400, detail="Aucune plateforme valide spécifiée")
        
        # Lancer la collecte en arrière-plan
        background_tasks.add_task(
            _collect_data_background,
            creator_username,
            valid_platforms
        )
        
        return {
            "message": "Collecte de données lancée en arrière-plan",
            "creator_username": creator_username,
            "platforms": [p.value for p in valid_platforms],
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Erreur lancement collecte données: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _collect_data_background(creator_username: str, platforms: List[PlatformType]):
    """Collecte les données en arrière-plan."""
    try:
        logger.info(f"Début collecte arrière-plan pour {creator_username}")
        
        async with data_collector:
            creator_data = await data_collector.collect_all_platform_data(creator_username, platforms)
        
        # Ici, vous pourriez sauvegarder les données dans une base de données
        # ou les traiter pour des analyses futures
        
        logger.info(f"Collecte arrière-plan terminée pour {creator_username}")
        
    except Exception as e:
        logger.error(f"Erreur collecte arrière-plan {creator_username}: {e}")

@router.get("/health")
async def health_check():
    """
    Vérifie l'état de santé du module IA Marketing.
    """
    try:
        # Vérifier les services
        services_status = {
            "data_collector": "ok",
            "creator_analyzer": "ok",
            "recommendation_engine": "ok"
        }
        
        # Vérifier les dépendances
        dependencies_status = {
            "openai_client": "ok" if recommendation_engine.openai_client else "error",
            "rag_system": "ok" if recommendation_engine.rag_system else "error",
            "embedding_model": "ok" if recommendation_engine.rag_system.embedding_model else "error"
        }
        
        return {
            "status": "healthy",
            "timestamp": utcnow().isoformat(),
            "services": services_status,
            "dependencies": dependencies_status
        }
        
    except Exception as e:
        logger.error(f"Erreur health check: {e}")
        return {
            "status": "unhealthy",
            "timestamp": utcnow().isoformat(),
            "error": str(e)
        }



