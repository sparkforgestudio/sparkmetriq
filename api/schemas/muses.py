# api/schemas/muses.py
"""
Schémas Pydantic pour la gestion des muses et catégories.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class MuseCategory(BaseModel):
    """Catégorie de muse."""
    
    id: str = Field(
        ...,
        description="Slug de catégorie (ex: cosplay)"
    )
    label: str = Field(
        ...,
        description="Libellé de la catégorie"
    )
    description: Optional[str] = Field(
        None,
        description="Description de la catégorie"
    )
    is_active: bool = Field(
        True,
        description="Catégorie active"
    )
    order: int = Field(
        0,
        description="Ordre d'affichage"
    )


class MuseCategoryList(BaseModel):
    """Liste des catégories avec compteurs."""
    
    items: List[MuseCategory] = Field(
        ...,
        description="Liste des catégories"
    )
    counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Compteur de muses par catégorie"
    )


class MuseCategoryPatch(BaseModel):
    """Requête de mise à jour des catégories d'une muse."""
    
    categories: List[str] = Field(
        ...,
        min_items=0,
        description="Liste de slugs de catégories"
    )



