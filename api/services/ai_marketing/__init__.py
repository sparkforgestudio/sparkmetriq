# api/services/ai_marketing/__init__.py
"""
Module IA - Recommandations Marketing & Business Multi-plateformes
================================================================

Ce module fournit des recommandations marketing, de contenu et business personnalisées
basées sur les données collectées via Apify et autres sources.

Fonctionnalités principales :
- Analyse de données consolidées multi-plateformes
- Segmentation des créateurs par catégorie de contenu
- Recommandations personnalisées actionnables
- Système RAG + LLM auto-hébergé
- API pour intégration frontend
"""

from .data_collector import DataCollector
from .rag_system import RAGSystem
from .creator_analyzer import CreatorAnalyzer
from .recommendation_engine import RecommendationEngine

__all__ = [
    "DataCollector",
    "RAGSystem", 
    "CreatorAnalyzer",
    "RecommendationEngine"
]
