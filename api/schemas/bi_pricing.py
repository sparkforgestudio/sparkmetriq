# api/schemas/bi_pricing.py
"""
Schémas Pydantic pour l'Assistant Pricing IA.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class PricingRecommendationIn(BaseModel):
    """Schéma pour la requête de recommandation de pricing.
    
    Représente les données nécessaires pour générer une recommandation
    de prix optimisé pour un item (PPV, subscription, bundle).
    """
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    item_type: str = Field(
        ...,
        description="Type d'item (ppv, subscription, bundle)"
    )
    item_ref: str = Field(..., description="ID de l'item (PPV / plan / bundle)")
    current_price_usd: float = Field(
        ...,
        ge=0.0,
        description="Prix actuel en USD"
    )
    features: Dict[str, Any] = Field(
        default_factory=dict,
        description="Caractéristiques (duration, media_type, etc.)"
    )


class PricingRecommendationOut(PricingRecommendationIn):
    """Schéma de sortie pour une recommandation de pricing.
    
    Contient toutes les données de PricingRecommendationIn plus les résultats
    de l'analyse : prix recommandé, confiance, gain prédit, base du calcul.
    """
    
    id: str = Field(..., description="ID de la recommandation")
    recommended_price_usd: float = Field(
        ...,
        ge=0.0,
        description="Prix recommandé en USD"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Niveau de confiance (0.0-1.0)"
    )
    predicted_revenue_gain_pct: float = Field(
        ...,
        description="Gain de revenus prédit en pourcentage"
    )
    basis: str = Field(
        ...,
        description="Base de la recommandation (modèle utilisé)"
    )
    generated_at: str = Field(..., description="Date de génération (ISO format)")

