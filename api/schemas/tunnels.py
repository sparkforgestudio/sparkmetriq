from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Requête de test/création de tunnel (pour tunnels_test)
class TunnelCreate(BaseModel):
    agency_id: str
    muse_id: str
    platform: str
    funnel_stage: str
    content_type: Optional[str] = None
    created_at: Optional[datetime] = None

# Réponse de création/test de tunnel
class TunnelResponse(BaseModel):
    success: bool
    message: Optional[str] = None

# Item pour l'aperçu du tunnel
class TunnelOverviewItem(BaseModel):
    muse_id: str
    date: str
    total: int
    success: int
    errors: int
    success_rate: float
    avg_conversion_time: Optional[float]

# Item pour les détails du tunnel
class TunnelDetailItem(BaseModel):
    agency_id: str
    muse_id: str
    platform: str
    funnel_stage: str
    content_type: str
    status: str
    content_id: str
    created_at: datetime
    converted_at: Optional[datetime]
    message: Optional[str]

# Enregistrement pour l'export CSV
class TunnelCSVRecord(BaseModel):
    agency_id: str
    muse_id: str
    platform: str
    funnel_stage: str
    content_type: str
    status: str
    content_id: str
    created_at: datetime
    converted_at: Optional[datetime]
    message: Optional[str]

# Recommandation simple issue de l'analyse
class TunnelRecommendation(BaseModel):
    muse_id: str
    recommendation: str

# Réponse aux recommandations
class TunnelRecommendationsResponse(BaseModel):
    recommendations: List[TunnelRecommendation]
