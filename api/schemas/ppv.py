from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PpvCreate(BaseModel):
    agency_id: str = Field(..., description="ID de l'agence")
    title: str = Field(..., description="Titre du contenu PPV")
    description: Optional[str] = Field(None, description="Description du contenu")
    media_url: Optional[str] = Field(None, description="URL du média")
    price_usdt: float = Field(..., description="Prix en USDT")


class PpvResponse(PpvCreate):
    id: str = Field(..., description="Identifiant unique du contenu PPV")
    created_at: datetime = Field(..., description="Date de création")
    created_by: str = Field(..., description="Email ou ID de l'utilisateur ayant créé")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière mise à jour")
