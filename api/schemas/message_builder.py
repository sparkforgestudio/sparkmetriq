# api/schemas/message_builder.py
"""
Schémas Pydantic pour le système Message Builder (Mass DM + Variables dynamiques).
"""

from pydantic import BaseModel, Field, constr
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


Platform = Literal[
    "telegram", "instagram", "twitter", "whatsapp", 
    "snapchat", "threads", "onlyfans"
]


class MessageTemplateIn(BaseModel):
    """Requête de création de template."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    name: constr(min_length=3) = Field(
        ...,
        description="Nom du template"
    )
    body: constr(min_length=1) = Field(
        ...,
        description="Corps du template avec syntaxe Jinja2 (filtres safe)"
    )
    variables_hint: Optional[List[str]] = Field(
        None,
        description="Variables disponibles (ex: ['first_name', 'avg_spend'])"
    )
    meta: Optional[Dict[str, Any]] = Field(
        None,
        description="Métadonnées supplémentaires"
    )


class MessageTemplateOut(BaseModel):
    """Réponse de template."""
    
    id: str = Field(
        ...,
        description="ID du template"
    )
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    name: str = Field(
        ...,
        description="Nom du template"
    )
    body: str = Field(
        ...,
        description="Corps du template"
    )
    variables_hint: List[str] = Field(
        default_factory=list,
        description="Variables disponibles"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées"
    )
    created_at: datetime = Field(
        ...,
        description="Date de création"
    )
    updated_at: datetime = Field(
        ...,
        description="Date de mise à jour"
    )


class SegmentationRule(BaseModel):
    """Règle de segmentation des cibles."""
    
    platforms: Optional[List[Platform]] = Field(
        None,
        description="Plateformes ciblées"
    )
    muse_id: Optional[str] = Field(
        None,
        description="ID de la muse"
    )
    min_total_spent: Optional[float] = Field(
        None,
        description="Dépense totale minimum"
    )
    has_ppv_purchase: Optional[bool] = Field(
        None,
        description="A déjà acheté du PPV"
    )
    inactive_days_gte: Optional[int] = Field(
        None,
        description="Inactif depuis X jours minimum"
    )
    language_in: Optional[List[str]] = Field(
        None,
        description="Langues (ISO codes)"
    )
    tags_any: Optional[List[str]] = Field(
        None,
        description="Tags (si système de tagging fan)"
    )
    limit: Optional[int] = Field(
        None,
        description="Limite pour preview/debug"
    )


class CampaignCreate(BaseModel):
    """Requête de création de campagne."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    name: str = Field(
        ...,
        description="Nom de la campagne"
    )
    template_id: str = Field(
        ...,
        description="ID du template à utiliser"
    )
    segmentation: SegmentationRule = Field(
        ...,
        description="Règle de segmentation"
    )
    platform: Platform = Field(
        ...,
        description="Plateforme cible"
    )
    scheduled_at: Optional[datetime] = Field(
        None,
        description="Date de planification (None = immédiat)"
    )
    tracking_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Paramètres de tracking (utm, ppv offer id, etc.)"
    )
    dry_run: bool = Field(
        False,
        description="Mode dry-run (preview uniquement)"
    )


class CampaignOut(BaseModel):
    """Réponse de campagne."""
    
    id: str = Field(
        ...,
        description="ID de la campagne"
    )
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    name: str = Field(
        ...,
        description="Nom de la campagne"
    )
    template_id: str = Field(
        ...,
        description="ID du template"
    )
    platform: Platform = Field(
        ...,
        description="Plateforme cible"
    )
    segmentation: SegmentationRule = Field(
        ...,
        description="Règle de segmentation"
    )
    status: Literal[
        "draft", "scheduled", "running", "paused", "completed", "failed"
    ] = Field(
        ...,
        description="Statut de la campagne"
    )
    totals: Dict[str, int] = Field(
        default_factory=dict,
        description="Totaux (targets, queued, sent, failed)"
    )
    scheduled_at: Optional[datetime] = Field(
        None,
        description="Date de planification"
    )
    created_at: datetime = Field(
        ...,
        description="Date de création"
    )
    updated_at: datetime = Field(
        ...,
        description="Date de mise à jour"
    )


class PreviewOutItem(BaseModel):
    """Item de preview."""
    
    user_ref: str = Field(
        ...,
        description="Référence utilisateur"
    )
    platform: Platform = Field(
        ...,
        description="Plateforme"
    )
    variables: Dict[str, Any] = Field(
        ...,
        description="Variables utilisées"
    )
    rendered: str = Field(
        ...,
        description="Message rendu"
    )


class PreviewOut(BaseModel):
    """Réponse de preview."""
    
    items: List[PreviewOutItem] = Field(
        ...,
        description="Liste des items de preview"
    )
    count_total: int = Field(
        ...,
        description="Nombre total de cibles"
    )
    truncated: bool = Field(
        ...,
        description="True si la liste a été tronquée"
    )


class SendRequest(BaseModel):
    """Requête d'envoi."""
    
    campaign_id: str = Field(
        ...,
        description="ID de la campagne"
    )
    confirm: bool = Field(
        False,
        description="Confirmation explicite requise pour envoi massif"
    )


class CampaignStatusOut(BaseModel):
    """Statut de campagne."""
    
    id: str = Field(
        ...,
        description="ID de la campagne"
    )
    status: str = Field(
        ...,
        description="Statut"
    )
    totals: Dict[str, int] = Field(
        ...,
        description="Totaux"
    )




