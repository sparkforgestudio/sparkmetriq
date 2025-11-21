from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PublicContentCreate(BaseModel):
    """
    Schéma de création d'un contenu public.
    """
    title: str = Field(..., example="Summer Teaser", description="Titre du contenu public")
    description: Optional[str] = Field(None, example="Sneak peek for the summer campaign", description="Description facultative")
    platform: str = Field(..., example="instagram", description="Plateforme de destination")
    media_url: str = Field(..., example="https://cdn.example.com/media/xyz.jpg", description="URL du média associé")
    muse_id: str = Field(..., example="muse_123", description="Identifiant de la muse")
    agency_id: str = Field(..., example="agency_456", description="Identifiant de l'agence")


class PublicContentOut(BaseModel):
    """
    Schéma de sortie d'un contenu public.
    """
    id: str = Field(..., description="Identifiant unique du contenu public")
    title: str = Field(..., description="Titre du contenu public")
    description: Optional[str] = Field(None, description="Description facultative")
    platform: str = Field(..., description="Plateforme de destination")
    media_url: str = Field(..., description="URL du média associé")
    muse_id: str = Field(..., description="Identifiant de la muse")
    agency_id: str = Field(..., description="Identifiant de l'agence")
    published: bool = Field(..., description="Statut de publication")
    created_at: datetime = Field(..., description="Date de création")

    class Config:
        orm_mode = True
