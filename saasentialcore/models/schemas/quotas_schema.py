"""
Schémas Pydantic génériques pour la gestion des quotas par organisation.

Ces schémas sont conçus pour être réutilisables par plusieurs applications (multi-produits).
Ils définissent la structure des quotas d'organisation de manière générique.

Note: Ces schémas ont été extraits d'une implémentation produit historique pour être
partagés avec d'autres applications consommatrices.
"""

from datetime import date, datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class OrgLimits(BaseModel):
    """
    Limites de quotas pour une organisation.
    
    Attributes:
        max_scheduled_posts: Nombre maximum de posts planifiés au total
        max_published_per_day: Nombre maximum de posts publiés par jour
        max_platforms_per_post: Nombre maximum de plateformes par post
    """
    
    max_scheduled_posts: int = Field(
        default=500,
        description="Nombre maximum de posts planifiés au total",
        ge=1
    )
    
    max_published_per_day: int = Field(
        default=200,
        description="Nombre maximum de posts publiés par jour",
        ge=1
    )
    
    max_platforms_per_post: int = Field(
        default=5,
        description="Nombre maximum de plateformes par post",
        ge=1
    )


class OrgUsage(BaseModel):
    """
    Usage actuel des quotas pour une organisation.
    
    Attributes:
        scheduled_posts: Nombre de posts actuellement planifiés
        published_today: Nombre de posts publiés aujourd'hui
        last_reset: Date du dernier reset quotidien
    """
    
    scheduled_posts: int = Field(
        default=0,
        description="Nombre de posts actuellement planifiés",
        ge=0
    )
    
    published_today: int = Field(
        default=0,
        description="Nombre de posts publiés aujourd'hui",
        ge=0
    )
    
    last_reset: Optional[date] = Field(
        None,
        description="Date du dernier reset quotidien"
    )


class OrgQuotas(BaseModel):
    """
    Quotas complets d'une organisation (limites + usage).
    
    Attributes:
        org_id: Identifiant de l'organisation
        limits: Limites de quotas
        usage: Usage actuel
        updated_at: Date de dernière mise à jour
    """
    
    org_id: str = Field(
        ...,
        description="Identifiant de l'organisation"
    )
    
    limits: OrgLimits = Field(
        default_factory=OrgLimits,
        description="Limites de quotas"
    )
    
    usage: OrgUsage = Field(
        default_factory=OrgUsage,
        description="Usage actuel"
    )
    
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date de dernière mise à jour"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "org_id": "org_123",
                "limits": {
                    "max_scheduled_posts": 500,
                    "max_published_per_day": 200,
                    "max_platforms_per_post": 5
                },
                "usage": {
                    "scheduled_posts": 42,
                    "published_today": 15,
                    "last_reset": "2024-01-15"
                },
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class OrgQuotasRead(BaseModel):
    """
    DTO pour la lecture des quotas d'une organisation (API Admin).
    
    Utilisé pour lister et afficher les quotas dans l'interface admin.
    """
    
    org_id: str = Field(..., description="Identifiant de l'organisation")
    max_scheduled_posts: int = Field(..., description="Nombre maximum de posts planifiés")
    max_published_per_day: int = Field(..., description="Nombre maximum de posts publiés par jour")
    max_platforms_per_post: int = Field(..., description="Nombre maximum de plateformes par post")
    scheduled_posts: int = Field(..., description="Nombre de posts actuellement planifiés")
    published_today: int = Field(..., description="Nombre de posts publiés aujourd'hui")
    last_reset: Optional[date] = Field(None, description="Date du dernier reset quotidien")
    updated_at: datetime = Field(..., description="Date de dernière mise à jour")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "org_id": "org_123",
                "max_scheduled_posts": 500,
                "max_published_per_day": 200,
                "max_platforms_per_post": 5,
                "scheduled_posts": 42,
                "published_today": 15,
                "last_reset": "2024-01-15",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class OrgQuotasUpdate(BaseModel):
    """
    DTO pour la mise à jour des limites de quotas (API Admin).
    
    Tous les champs sont optionnels pour permettre des mises à jour partielles.
    """
    
    max_scheduled_posts: Optional[int] = Field(
        None,
        description="Nouveau nombre maximum de posts planifiés",
        ge=1
    )
    max_published_per_day: Optional[int] = Field(
        None,
        description="Nouveau nombre maximum de posts publiés par jour",
        ge=1
    )
    max_platforms_per_post: Optional[int] = Field(
        None,
        description="Nouveau nombre maximum de plateformes par post",
        ge=1
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "max_scheduled_posts": 1000,
                "max_published_per_day": 300,
                "max_platforms_per_post": 10
            }
        }
    )
