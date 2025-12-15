"""
Modèle de base de données pour les quotas d'organisation.

Ce module définit la structure des documents quotas dans MongoDB.
Les schémas utilisent OrgLimits, OrgUsage et OrgQuotas pour la compatibilité.
"""

from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

from saasentialcore.models.schemas.quotas_schema import OrgLimits, OrgUsage, OrgQuotas


class QuotasDB(BaseModel):
    """
    Modèle de document quotas en base de données.
    
    Structure MongoDB :
    {
        "_id": ObjectId (optionnel, généré par MongoDB),
        "org_id": str,
        "limits": {
            "max_scheduled_posts": int,
            "max_published_per_day": int,
            "max_platforms_per_post": int
        },
        "usage": {
            "scheduled_posts": int,
            "published_today": int,
            "last_reset": date (optionnel)
        },
        "updated_at": datetime
    }
    
    Note: Ce modèle est compatible avec OrgQuotas mais ajoute le support de _id MongoDB.
    """
    
    id: Optional[str] = Field(None, alias="_id", description="ID MongoDB des quotas")
    org_id: str = Field(..., description="ID de l'organisation")
    limits: OrgLimits = Field(default_factory=OrgLimits, description="Limites des quotas")
    usage: OrgUsage = Field(default_factory=OrgUsage, description="Utilisation actuelle des quotas")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date de mise à jour")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
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
    
    def to_org_quotas(self) -> OrgQuotas:
        """
        Convertit ce modèle DB en OrgQuotas (sans _id).
        
        Returns:
            OrgQuotas correspondant
        """
        return OrgQuotas(
            org_id=self.org_id,
            limits=self.limits,
            usage=self.usage,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_org_quotas(cls, quotas: OrgQuotas, _id: Optional[str] = None) -> "QuotasDB":
        """
        Crée un QuotasDB à partir d'un OrgQuotas.
        
        Args:
            quotas: OrgQuotas à convertir
            _id: ID MongoDB optionnel
        
        Returns:
            QuotasDB correspondant
        """
        return cls(
            _id=_id,
            org_id=quotas.org_id,
            limits=quotas.limits,
            usage=quotas.usage,
            updated_at=quotas.updated_at
        )
