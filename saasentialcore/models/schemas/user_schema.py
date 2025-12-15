"""
Schémas Pydantic pour les utilisateurs.

Ce module définit les schémas de validation et de sérialisation
pour les requêtes et réponses liées aux utilisateurs.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """
    Schéma pour la création d'un utilisateur.
    """
    email: EmailStr = Field(..., description="Email de l'utilisateur")
    password: str = Field(..., min_length=8, description="Mot de passe (minimum 8 caractères)")
    org_id: Optional[str] = Field(default=None, description="ID de l'organisation (optionnel)")


class UserUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'un utilisateur.
    """
    email: Optional[EmailStr] = Field(default=None, description="Nouvel email")
    password: Optional[str] = Field(default=None, min_length=8, description="Nouveau mot de passe")
    org_ids: Optional[List[str]] = Field(default=None, description="Nouvelle liste d'organisations")
    is_admin: Optional[bool] = Field(default=None, description="Statut admin")
    is_active: Optional[bool] = Field(default=None, description="Statut actif")


class UserResponse(BaseModel):
    """
    Schéma de réponse pour un utilisateur.
    """
    id: str = Field(..., description="ID de l'utilisateur")
    email: EmailStr = Field(..., description="Email de l'utilisateur")
    org_ids: List[str] = Field(default_factory=list, description="Liste des IDs d'organisations")
    is_admin: bool = Field(default=False, description="L'utilisateur est-il admin ?")
    is_active: bool = Field(default=True, description="L'utilisateur est-il actif ?")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")


class TokenResponse(BaseModel):
    """
    Schéma de réponse pour un token d'accès.
    """
    access_token: str = Field(..., description="Token JWT d'accès")
    token_type: str = Field(default="bearer", description="Type de token")

