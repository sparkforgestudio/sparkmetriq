# api/schemas/tracking.py
"""
Schémas Pydantic pour le système de suivi des liens marketing & attribution.
"""

from pydantic import BaseModel, Field, AnyUrl
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime


AttributionModel = Literal["last_touch", "first_touch"]


class LinkCreate(BaseModel):
    """Requête de création de lien traqué."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    muse_id: Optional[str] = Field(
        None,
        description="ID de la muse"
    )
    destination_url: AnyUrl = Field(
        ...,
        description="URL de destination"
    )
    utm_source: Optional[str] = Field(
        None,
        description="UTM source"
    )
    utm_medium: Optional[str] = Field(
        None,
        description="UTM medium"
    )
    utm_campaign: Optional[str] = Field(
        None,
        description="UTM campaign"
    )
    utm_content: Optional[str] = Field(
        None,
        description="UTM content"
    )
    campaign_id: Optional[str] = Field(
        None,
        description="ID de la campagne Message Builder"
    )
    promo_code: Optional[str] = Field(
        None,
        description="Code promo (pour matching offline/OF)"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Date d'expiration du lien"
    )
    max_clicks: Optional[int] = Field(
        None,
        description="Nombre maximum de clics autorisés"
    )
    meta: Optional[Dict[str, Any]] = Field(
        None,
        description="Métadonnées supplémentaires"
    )


class LinkOut(BaseModel):
    """Réponse de lien traqué."""
    
    id: str = Field(
        ...,
        description="ID du lien"
    )
    code: str = Field(
        ...,
        description="Code court du lien"
    )
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    short_url: str = Field(
        ...,
        description="URL courte (/r/{code})"
    )
    destination_url: str = Field(
        ...,
        description="URL de destination"
    )
    utm: Dict[str, str] = Field(
        default_factory=dict,
        description="Paramètres UTM"
    )
    campaign_id: Optional[str] = Field(
        None,
        description="ID de la campagne"
    )
    promo_code: Optional[str] = Field(
        None,
        description="Code promo"
    )
    created_at: datetime = Field(
        ...,
        description="Date de création"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Date d'expiration"
    )
    max_clicks: Optional[int] = Field(
        None,
        description="Limite de clics"
    )
    clicks_total: int = Field(
        0,
        description="Nombre total de clics"
    )


class LinkListOut(BaseModel):
    """Liste de liens traqués."""
    
    items: List[LinkOut] = Field(
        ...,
        description="Liste des liens"
    )


class ClickLogOut(BaseModel):
    """Log de clic."""
    
    id: str = Field(
        ...,
        description="ID du log"
    )
    code: str = Field(
        ...,
        description="Code du lien"
    )
    ts: datetime = Field(
        ...,
        description="Timestamp du clic"
    )
    ip_hash: str = Field(
        ...,
        description="Hash de l'IP (sécurité)"
    )
    ua: Optional[str] = Field(
        None,
        description="User agent"
    )
    ref: Optional[str] = Field(
        None,
        description="Referrer"
    )
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    campaign_id: Optional[str] = Field(
        None,
        description="ID de la campagne"
    )
    utm: Dict[str, str] = Field(
        default_factory=dict,
        description="Paramètres UTM"
    )
    user_ref: Optional[str] = Field(
        None,
        description="Référence utilisateur"
    )


class TrackRenderIn(BaseModel):
    """Requête de rendu de lien traqué (pour Message Builder)."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    destination_url: AnyUrl = Field(
        ...,
        description="URL de destination"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contexte (campaign_id, utm_source, user_ref, etc.)"
    )


class TrackRenderOut(BaseModel):
    """Réponse de rendu de lien traqué."""
    
    short_url: str = Field(
        ...,
        description="URL courte générée"
    )
    code: str = Field(
        ...,
        description="Code du lien"
    )


class SourceStatsOut(BaseModel):
    """Statistiques par source de trafic."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    range_from: datetime = Field(
        ...,
        description="Date de début"
    )
    range_to: datetime = Field(
        ...,
        description="Date de fin"
    )
    model: AttributionModel = Field(
        ...,
        description="Modèle d'attribution utilisé"
    )
    clicks: Optional[int] = Field(
        None,
        description="Nombre total de clics"
    )
    revenue_total: float = Field(
        ...,
        description="Revenu total"
    )
    by_source: List[Dict[str, Any]] = Field(
        ...,
        description="Détails par source/medium/campaign/content"
    )




