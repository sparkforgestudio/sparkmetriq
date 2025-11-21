# api/schemas/bi_insights.py
"""
Schémas Pydantic pour l'Assistant Stratégique IA (Insights).
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List

Severity = Literal["low", "medium", "high"]
InsightType = Literal["alert", "opportunity", "trend", "collab"]


class InsightAlertIn(BaseModel):
    """Schéma pour la création d'une alerte insight stratégique.
    
    Représente une alerte, opportunité, tendance ou suggestion de collaboration
    générée par l'Assistant Stratégique IA.
    """
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: Optional[str] = Field(None, description="ID de la muse (optionnel)")
    type: InsightType = Field("alert", description="Type d'insight")
    category: str = Field(..., description="Catégorie de l'alerte")
    title: str = Field(..., description="Titre de l'alerte")
    severity: Severity = Field("medium", description="Sévérité")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contexte additionnel"
    )


class InsightAlertOut(InsightAlertIn):
    """Schéma de sortie pour une alerte insight.
    
    Contient toutes les données de InsightAlertIn plus l'ID MongoDB
    et la date de création.
    """
    
    id: str = Field(..., description="ID de l'alerte")
    created_at: str = Field(..., description="Date de création (ISO format)")


class InsightsQuery(BaseModel):
    """Schéma pour la requête de liste des insights.
    
    Paramètres de filtrage et pagination pour lister les alertes stratégiques.
    """
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: Optional[str] = Field(None, description="ID de la muse (filtre)")
    types: Optional[List[InsightType]] = Field(None, description="Types (filtre)")
    severity: Optional[List[Severity]] = Field(None, description="Sévérités (filtre)")
    from_utc: Optional[str] = Field(None, description="Date de début UTC (ISO format)")
    to_utc: Optional[str] = Field(None, description="Date de fin UTC (ISO format)")
    page: int = Field(1, ge=1, description="Numéro de page")
    limit: int = Field(100, ge=1, le=500, description="Nombre d'éléments par page")


class CollabCandidate(BaseModel):
    """Schéma pour un candidat à la collaboration.
    
    Représente une muse candidate pour une collaboration avec une autre muse,
    basée sur un score de similarité calculé par l'IA.
    """
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    candidate_muse_id: str = Field(..., description="ID de la muse candidate")
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de similarité (0.0-1.0)"
    )
    basis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Base du score (audience, hashtags, etc.)"
    )


class CollabQuery(BaseModel):
    """Requête de candidats collaboration."""
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    min_score: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="Score minimum requis"
    )
    page: int = Field(1, ge=1, description="Numéro de page")
    limit: int = Field(50, ge=1, le=200, description="Nombre d'éléments par page")

