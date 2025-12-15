"""
Modèle de base de données pour les utilisateurs.

Ce module définit la structure des documents utilisateur dans MongoDB.
"""

from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserDB(BaseModel):
    """
    Modèle de document utilisateur en base de données.
    
    Structure MongoDB :
    {
        "_id": ObjectId,
        "email": str,
        "password_hash": str,
        "org_ids": [str],
        "is_admin": bool,
        "is_active": bool,
        "created_at": datetime,
        "updated_at": datetime
    }
    """
    
    id: str = Field(..., alias="_id", description="ID MongoDB de l'utilisateur")
    email: EmailStr = Field(..., description="Email de l'utilisateur")
    password_hash: str = Field(..., description="Hash du mot de passe")
    org_ids: List[str] = Field(default_factory=list, description="Liste des IDs d'organisations")
    is_admin: bool = Field(default=False, description="L'utilisateur est-il admin ?")
    is_active: bool = Field(default=True, description="L'utilisateur est-il actif ?")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date de création")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date de mise à jour")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "email": "user@example.com",
                "password_hash": "$2b$12$...",
                "org_ids": ["org_123", "org_456"],
                "is_admin": False,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )

