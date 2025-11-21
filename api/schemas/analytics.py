# api/schemas/analytics.py
"""
Schémas Pydantic pour les réponses API Analytics & BI.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class ConversationKPIs(BaseModel):
    conversations: int
    messages: int
    user_msgs: int
    bot_msgs: int
    channels: List[str] = []

class ResponseTimeStats(BaseModel):
    avg_rt_sec: Optional[float] = None

class ConversationAnalyticsResponse(BaseModel):
    kpis: ConversationKPIs
    response_time: ResponseTimeStats

class FunnelOverview(BaseModel):
    contact: int = 0
    lead: int = 0
    subscriber: int = 0
    payer: int = 0
    retained: int = 0
    cr_contact_lead: Optional[float] = None
    cr_lead_subscriber: Optional[float] = None
    cr_subscriber_payer: Optional[float] = None

class RevenueKPIs(BaseModel):
    gmv: float = 0.0
    payers: int = 0
    arpu: Optional[float] = None
    ltv_mean: Optional[float] = None

class PPVKPIs(BaseModel):
    sent: int = 0
    clicked: int = 0
    paid: int = 0
    conv_rate_click: Optional[float] = None
    conv_rate_paid: Optional[float] = None
    avg_ticket: Optional[float] = None

class ForecastPoint(BaseModel):
    day: str
    yhat: float

class ForecastResponse(BaseModel):
    series: List[ForecastPoint]
    model: str = "naive-linear"


class CategoryAggFilters(BaseModel):
    """Filtres pour l'agrégation par catégorie."""
    
    date_from: str = Field(
        ...,
        description="Date de début (ISO format)"
    )
    date_to: str = Field(
        ...,
        description="Date de fin (ISO format)"
    )
    channels: Optional[List[str]] = Field(
        None,
        description="Filtrer par canaux (ex: ['instagram', 'telegram'])"
    )
    categories: Optional[List[str]] = Field(
        None,
        description="Filtrer par catégories (slugs)"
    )
    granularity: Literal["daily", "weekly", "monthly"] = Field(
        "daily",
        description="Granularité (daily|weekly|monthly)"
    )


class CategoryAggItem(BaseModel):
    """Item d'agrégation par catégorie."""
    
    category: str = Field(
        ...,
        description="Slug de la catégorie"
    )
    muses: int = Field(
        ...,
        description="Nombre de muses dans cette catégorie"
    )
    revenue_total: float = Field(
        ...,
        description="Revenus totaux"
    )
    ppv_total: float = Field(
        ...,
        description="Revenus PPV totaux"
    )
    messages_in: int = Field(
        ...,
        description="Messages entrants"
    )
    messages_out: int = Field(
        ...,
        description="Messages sortants"
    )
    new_subs: int = Field(
        ...,
        description="Nouveaux abonnements"
    )
    churns: int = Field(
        ...,
        description="Désabonnements"
    )


class CategoryAggResponse(BaseModel):
    """Réponse d'agrégation par catégorie."""
    
    items: List[CategoryAggItem] = Field(
        ...,
        description="Liste des agrégations par catégorie"
    )
    total_revenue: float = Field(
        ...,
        description="Revenu total (toutes catégories)"
    )
    total_ppv: float = Field(
        ...,
        description="PPV total"
    )
    total_messages_in: int = Field(
        ...,
        description="Messages entrants totaux"
    )
    total_messages_out: int = Field(
        ...,
        description="Messages sortants totaux"
    )
    total_new_subs: int = Field(
        ...,
        description="Nouveaux abonnements totaux"
    )
    total_churns: int = Field(
        ...,
        description="Désabonnements totaux"
    )
