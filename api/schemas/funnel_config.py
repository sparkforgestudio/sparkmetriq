# api/schemas/funnel_config.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class FunnelMappings(BaseModel):
    source: List[str] = Field(..., description="Liste des plateformes définies comme source")
    intermediate: List[str] = Field(..., description="Liste des plateformes définies comme intermédiaire")
    closing: List[str] = Field(..., description="Liste des plateformes définies comme closing")

class FunnelConfig(BaseModel):
    agency_id: str = Field(..., description="Identifiant de l'agence")
    muse_id: Optional[str] = Field(None, description="Identifiant de la muse (optionnel)")
    mappings: FunnelMappings = Field(..., description="Mapping des plateformes pour chaque étape du tunnel")
