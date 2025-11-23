# api/schemas/calendar.py
"""
Schémas Pydantic pour la Vue Calendaire Unifiée.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime

Platform = Literal["instagram", "tiktok", "x", "reddit", "telegram", "onlyfans"]
Status = Literal["draft", "scheduled", "pending", "publishing", "published", "failed", "canceled"]


class ScheduleWindow(BaseModel):
    """Fenêtre temporelle pour la programmation."""
    
    start_at_utc: str = Field(
        ...,
        description="Date/heure de début en UTC (ISO format)"
    )
    end_at_utc: Optional[str] = Field(
        None,
        description="Date/heure de fin en UTC (ISO format, optionnel)"
    )
    tz: str = Field(
        ...,
        description="Timezone (ex: Europe/Paris)"
    )
    recurrence: Optional[str] = Field(
        None,
        description="Règle de récurrence RRULE (optionnel)"
    )


class ContentRef(BaseModel):
    """Références au contenu du post."""
    
    text: Optional[str] = Field(
        None,
        description="Texte du post (caption, tweet, etc.)"
    )
    media_ids: List[str] = Field(
        default_factory=list,
        description="IDs des médias associés"
    )
    link_refs: List[str] = Field(
        default_factory=list,
        description="Références de liens"
    )
    ppv_bundle_id: Optional[str] = Field(
        None,
        description="ID du bundle PPV (si applicable)"
    )


class ScheduledPostIn(BaseModel):
    """Requête de création/mise à jour d'un post programmé."""
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    platform: Platform = Field(..., description="Plateforme cible")
    status: Status = Field(..., description="Statut du post")
    visibility: Literal["public", "story", "ppv", "dm"] = Field(
        "public",
        description="Visibilité du post"
    )
    content_ref: ContentRef = Field(..., description="Contenu du post")
    schedule: ScheduleWindow = Field(..., description="Fenêtre de programmation")
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contraintes additionnelles"
    )
    labels: List[str] = Field(
        default_factory=list,
        description="Labels pour catégorisation"
    )
    category: Optional[str] = Field(
        None,
        description="Catégorie (appareillage muses->catégorie)"
    )


class ScheduledPostOut(BaseModel):
    """Post programmé (vue simplifiée pour le calendrier)."""
    
    id: str = Field(..., description="ID du post")
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    platform: Platform = Field(..., description="Plateforme")
    status: Status = Field(..., description="Statut")
    title: Optional[str] = Field(
        None,
        description="Titre (extrait du texte)"
    )
    start_at_utc: str = Field(..., description="Date/heure de début UTC")
    end_at_utc: Optional[str] = Field(
        None,
        description="Date/heure de fin UTC"
    )
    tz: str = Field(..., description="Timezone")
    labels: List[str] = Field(
        default_factory=list,
        description="Labels"
    )
    category: Optional[str] = Field(
        None,
        description="Catégorie"
    )
    media_preview_url: Optional[str] = Field(
        None,
        description="URL de prévisualisation média"
    )


class CalendarQuery(BaseModel):
    """Requête de requête du calendrier."""
    
    org_id: str = Field(..., description="ID de l'organisation")
    from_utc: str = Field(..., description="Date de début UTC")
    to_utc: str = Field(..., description="Date de fin UTC")
    muse_ids: Optional[List[str]] = Field(
        None,
        description="IDs des muses (filtre)"
    )
    platforms: Optional[List[Platform]] = Field(
        None,
        description="Plateformes (filtre)"
    )
    statuses: Optional[List[Status]] = Field(
        None,
        description="Statuts (filtre)"
    )
    labels: Optional[List[str]] = Field(
        None,
        description="Labels (filtre)"
    )
    category_id: Optional[str] = Field(
        None,
        description="ID de catégorie (filtre)"
    )
    page: int = Field(
        1,
        ge=1,
        description="Numéro de page"
    )
    limit: int = Field(
        200,
        ge=1,
        le=500,
        description="Nombre d'éléments par page"
    )


class RescheduleIn(BaseModel):
    """Requête de reprogrammation."""
    
    id: str = Field(..., description="ID du post à reprogrammer")
    new_start_at_utc: str = Field(
        ...,
        description="Nouvelle date/heure de début UTC"
    )
    new_tz: Optional[str] = Field(
        None,
        description="Nouveau timezone (optionnel)"
    )


class DuplicateIn(BaseModel):
    """Requête de duplication."""
    
    id: str = Field(..., description="ID du post à dupliquer")
    target_start_at_utc: str = Field(
        ...,
        description="Date/heure cible UTC"
    )
    tz: str = Field(..., description="Timezone")
    with_ai_variation: bool = Field(
        False,
        description="Appliquer une variation IA au contenu"
    )
    target_platforms: Optional[List[Platform]] = Field(
        None,
        description="Plateformes cibles (si None, utilise la plateforme source)"
    )




