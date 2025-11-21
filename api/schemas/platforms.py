# api/schemas/platforms.py
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    """Types de plateformes supportées."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TELEGRAM = "telegram"
    THREADS = "threads"
    SNAPCHAT = "snapchat"
    REDDIT = "reddit"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    ONLYFANS = "onlyfans"
    FANVUE = "fanvue"
    WHATSAPP = "whatsapp"
    FANSLY = "fansly"
    LOYALFANS = "loyalfans"
    PATREON = "patreon"
    DISCORD = "discord"
    MYMFANS = "mymfans"
    MANYVIDS = "manyvids"

class PrivacyLevel(str, Enum):
    """Niveaux de confidentialité TikTok."""
    PUBLIC_TO_EVERYONE = "PUBLIC_TO_EVERYONE"
    MUTUAL_FOLLOW_FRIEND = "MUTUAL_FOLLOW_FRIEND"
    SELF_ONLY = "SELF_ONLY"

class MediaType(str, Enum):
    """Types de médias supportés."""
    IMAGE = "image"
    VIDEO = "video"
    PHOTO = "photo"

class ContentType(str, Enum):
    """Types de contenu."""
    POST = "post"
    STORY = "story"
    REEL = "reel"
    MESSAGE = "message"
    PREMIUM_CONTENT = "premium_content"

# === TikTok Schemas ===
class TikTokContentRequest(BaseModel):
    """Schéma pour le contenu TikTok."""
    video_url: HttpUrl = Field(..., description="URL de la vidéo à publier")
    title: str = Field(..., min_length=1, max_length=150, description="Titre de la vidéo")
    description: Optional[str] = Field(None, max_length=2200, description="Description de la vidéo")
    privacy_level: PrivacyLevel = Field(PrivacyLevel.PUBLIC_TO_EVERYONE, description="Niveau de confidentialité")
    disable_duet: bool = Field(False, description="Désactiver les duos")
    disable_comment: bool = Field(False, description="Désactiver les commentaires")
    disable_stitch: bool = Field(False, description="Désactiver les stitches")
    video_cover_timestamp_ms: int = Field(1000, ge=0, description="Timestamp pour la miniature (ms)")
    tags: Optional[List[str]] = Field(None, description="Tags de la vidéo")

class TikTokAuthRequest(BaseModel):
    """Schéma pour l'authentification TikTok."""
    access_token: str = Field(..., description="Token d'accès TikTok")
    refresh_token: Optional[str] = Field(None, description="Token de rafraîchissement")
    expires_at: Optional[datetime] = Field(None, description="Date d'expiration du token")

class TikTokAnalyticsResponse(BaseModel):
    """Schéma pour les analytics TikTok."""
    video_id: str
    views: int
    likes: int
    comments: int
    shares: int
    play_time: Optional[int] = None
    completion_rate: Optional[float] = None
    timestamp: datetime

# === Fanvue Schemas ===
class FanvueContentRequest(BaseModel):
    """Schéma pour le contenu Fanvue."""
    title: str = Field(..., min_length=1, max_length=200, description="Titre du contenu")
    description: Optional[str] = Field(None, max_length=5000, description="Description du contenu")
    media_urls: List[HttpUrl] = Field(..., min_items=1, description="URLs des médias")
    price: float = Field(0, ge=0, description="Prix du contenu")
    is_premium: bool = Field(False, description="Contenu premium")
    tags: Optional[List[str]] = Field(None, description="Tags du contenu")
    category: str = Field("general", description="Catégorie du contenu")
    scheduled_at: Optional[datetime] = Field(None, description="Date de publication programmée")

class FanvueAuthRequest(BaseModel):
    """Schéma pour l'authentification Fanvue."""
    api_key: str = Field(..., description="Clé API Fanvue")
    api_secret: str = Field(..., description="Secret API Fanvue")

class FanvueEarningsResponse(BaseModel):
    """Schéma pour les revenus Fanvue."""
    total_earnings: float
    subscription_earnings: float
    post_earnings: float
    tips_earnings: float
    period_start: datetime
    period_end: datetime
    currency: str = "USD"

class FanvueSubscriberResponse(BaseModel):
    """Schéma pour un abonné Fanvue."""
    subscriber_id: str
    username: str
    subscription_date: datetime
    plan_type: str
    monthly_amount: float
    is_active: bool

# === OnlyFans Schemas ===
class OnlyFansContentRequest(BaseModel):
    """Schéma pour le contenu OnlyFans."""
    media_url: HttpUrl = Field(..., description="URL du média")
    caption: str = Field(..., min_length=1, max_length=2000, description="Légende du contenu")
    price: float = Field(0, ge=0, description="Prix du contenu")
    is_premium: bool = Field(False, description="Contenu premium")
    tags: Optional[List[str]] = Field(None, description="Tags du contenu")
    scheduled_at: Optional[datetime] = Field(None, description="Date de publication programmée")

class OnlyFansAuthRequest(BaseModel):
    """Schéma pour l'authentification OnlyFans."""
    api_key: str = Field(..., description="Clé API OnlyFans")
    api_secret: str = Field(..., description="Secret API OnlyFans")

class OnlyFansAnalyticsResponse(BaseModel):
    """Schéma pour les analytics OnlyFans."""
    total_earnings: float
    subscription_count: int
    post_count: int
    message_count: int
    period_start: datetime
    period_end: datetime
    currency: str = "USD"

# === Generic Platform Schemas ===
class PlatformCredentials(BaseModel):
    """Schéma générique pour les credentials des plateformes."""
    platform: PlatformType
    credentials: Dict[str, Any] = Field(..., description="Credentials spécifiques à la plateforme")
    is_active: bool = Field(True, description="Plateforme active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContentRequest(BaseModel):
    """Schéma générique pour les requêtes de contenu."""
    platform: PlatformType
    content_type: ContentType
    title: Optional[str] = Field(None, description="Titre du contenu")
    text: Optional[str] = Field(None, description="Texte du contenu")
    media_urls: Optional[List[HttpUrl]] = Field(None, description="URLs des médias")
    price: Optional[float] = Field(None, ge=0, description="Prix du contenu")
    tags: Optional[List[str]] = Field(None, description="Tags")
    scheduled_at: Optional[datetime] = Field(None, description="Date de publication programmée")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées supplémentaires")

class ContentResponse(BaseModel):
    """Schéma générique pour les réponses de contenu."""
    platform: PlatformType
    content_id: str
    status: Literal["success", "error", "pending"]
    message: str
    platform_response: Optional[Dict[str, Any]] = None
    published_at: Optional[datetime] = None
    error_details: Optional[str] = None

class PlatformAnalytics(BaseModel):
    """Schéma générique pour les analytics des plateformes."""
    platform: PlatformType
    period_start: datetime
    period_end: datetime
    total_earnings: float
    total_posts: int
    total_views: int
    total_likes: int
    total_comments: int
    total_shares: int
    engagement_rate: float
    currency: str = "USD"

class WebhookEvent(BaseModel):
    """Schéma générique pour les événements webhook."""
    platform: PlatformType
    event_type: str
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None

# === Multi-Platform Schemas ===
class MultiPlatformContentRequest(BaseModel):
    """Schéma pour publier sur plusieurs plateformes."""
    platforms: List[PlatformType] = Field(..., min_items=1, description="Plateformes cibles")
    content: ContentRequest
    agency_id: str = Field(..., description="ID de l'agence")
    muse_id: str = Field(..., description="ID de la muse")

class MultiPlatformContentResponse(BaseModel):
    """Schéma pour les réponses multi-plateformes."""
    request_id: str
    results: Dict[PlatformType, ContentResponse]
    total_success: int
    total_errors: int
    completed_at: datetime
