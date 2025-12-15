"""
Modèle de base de données pour les organisations.

Ce module définit la structure des documents organisation dans MongoDB.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class OrgDB(BaseModel):
    """
    Modèle de document organisation en base de données.
    
    Structure MongoDB :
    {
        "_id": ObjectId,
        "name": str,
        "slug": str,
        "owner_id": str,
        "settings": dict,
        "created_at": datetime,
        "updated_at": datetime
    }
    """
    
    id: str = Field(..., alias="_id", description="ID MongoDB de l'organisation")
    name: str = Field(..., description="Nom de l'organisation")
    slug: str = Field(..., description="Slug unique de l'organisation")
    owner_id: str = Field(..., description="ID de l'utilisateur propriétaire")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Paramètres de l'organisation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date de création")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date de mise à jour")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "My Organization",
                "slug": "my-org",
                "owner_id": "user_123",
                "settings": {},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )

