"""
Schémas Pydantic pour les organisations.

Ce module définit les schémas de validation et de sérialisation
pour les requêtes et réponses liées aux organisations.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class OrgCreate(BaseModel):
    """
    Schéma pour la création d'une organisation.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Nom de l'organisation")
    slug: Optional[str] = Field(default=None, description="Slug unique (généré automatiquement si non fourni)")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Paramètres de l'organisation")


class OrgUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'une organisation.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Nouveau nom")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="Nouveaux paramètres")


class OrgResponse(BaseModel):
    """
    Schéma de réponse pour une organisation.
    """
    id: str = Field(..., description="ID de l'organisation")
    name: str = Field(..., description="Nom de l'organisation")
    slug: str = Field(..., description="Slug unique de l'organisation")
    owner_id: str = Field(..., description="ID de l'utilisateur propriétaire")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Paramètres de l'organisation")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")

