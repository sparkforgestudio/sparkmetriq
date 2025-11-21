# api/schemas/otp.py
"""
Schémas Pydantic pour le système OTP semi-manuel agnostique.
Jamais de code OTP en clair - approche sécurisée.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime

OTPState = Literal[
    "INIT", "RESERVED", "WAITING_CODE",
    "DELIVERED_TO_ADMIN",
    "APPLIED_SUCCESS", "APPLIED_FAILED",
    "CANCELLED", "FAILED", "BANNED"
]

# ---------- OTP Session Management ----------
class OTPReserveIn(BaseModel):
    org_id: str
    app: Literal["instagram", "telegram", "tiktok", "twitter", "reddit", "onlyfans"]
    country: str = Field(..., description="ISO code (ex: US, FR)")
    slot_id: str = Field(..., description="OTP ancré à un slot concret")
    constraints: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

class OTPPollOut(BaseModel):
    session_id: str
    state: OTPState
    code_masked: Optional[str] = None  # Jamais le code complet
    message_preview: Optional[str] = None
    provider: Optional[str] = None
    number: Optional[str] = None
    updated_at: datetime
    expires_at: Optional[datetime] = None

class OTPAcknowledgeIn(BaseModel):
    action: Literal["seen", "copied"]
    note: Optional[str] = None

class OTPApplyIn(BaseModel):
    outcome: Literal["success", "failed"]
    note: Optional[str] = None

class OTPApplyOut(BaseModel):
    ok: bool
    session_id: str
    state: OTPState
    details: Optional[Dict[str, Any]] = None

# ---------- OTP Session Details ----------
class OTPSessionOut(BaseModel):
    session_id: str
    org_id: str
    app: str
    country: str
    slot_id: str
    device_id: str
    state: OTPState
    provider: Optional[str] = None
    number: Optional[str] = None
    code_masked: Optional[str] = None
    message_preview: Optional[str] = None
    constraints: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None

class OTPSessionListResponse(BaseModel):
    items: List[OTPSessionOut]
    total: int
    page: int
    page_size: int

# ---------- OTP Provider Management ----------
class OTPProviderInfo(BaseModel):
    name: str
    status: Literal["active", "inactive", "maintenance"]
    health_score: float = Field(..., ge=0.0, le=1.0)
    success_rate: float = Field(..., ge=0.0, le=1.0)
    avg_response_time: Optional[float] = None
    supported_countries: List[str] = []
    supported_apps: List[str] = []
    last_health_check: Optional[datetime] = None

class OTPProviderListResponse(BaseModel):
    providers: List[OTPProviderInfo]
    primary_provider: Optional[str] = None

# ---------- OTP Pool Management ----------
class OTPPoolConfig(BaseModel):
    pool_name: str
    app: str
    country: str
    provider: str
    max_concurrent: int = Field(..., ge=1)
    daily_limit: int = Field(..., ge=1)
    cost_per_sms: float = Field(..., ge=0.0)
    quality_threshold: float = Field(..., ge=0.0, le=1.0)

class OTPPoolStats(BaseModel):
    pool_name: str
    total_reserved: int
    successful: int
    failed: int
    success_rate: float
    avg_response_time: float
    daily_usage: int
    daily_limit: int
    remaining_quota: int

class OTPPoolListResponse(BaseModel):
    pools: List[OTPPoolConfig]
    stats: List[OTPPoolStats]

# ---------- OTP Budget & Quotas ----------
class OTPBudgetConfig(BaseModel):
    org_id: str
    daily_budget: float = Field(..., ge=0.0)
    monthly_budget: float = Field(..., ge=0.0)
    per_app_limits: Dict[str, int] = Field(default_factory=dict)
    per_country_limits: Dict[str, int] = Field(default_factory=dict)
    max_concurrent_sessions: int = Field(..., ge=1)

class OTPBudgetStatus(BaseModel):
    org_id: str
    daily_spent: float
    monthly_spent: float
    daily_remaining: float
    monthly_remaining: float
    concurrent_sessions: int
    max_concurrent_sessions: int
    quota_exceeded: bool
    budget_exceeded: bool

class OTPBudgetResponse(BaseModel):
    config: OTPBudgetConfig
    status: OTPBudgetStatus

# ---------- OTP Analytics & Metrics ----------
class OTPMetrics(BaseModel):
    total_sessions: int
    successful_sessions: int
    failed_sessions: int
    success_rate: float
    avg_response_time: float
    total_cost: float
    sessions_by_app: Dict[str, int]
    sessions_by_country: Dict[str, int]
    sessions_by_provider: Dict[str, int]
    time_period: str

class OTPAnalyticsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    group_by: Optional[Literal["app", "country", "provider", "hour", "day"]] = None
    filters: Optional[Dict[str, Any]] = None

class OTPAnalyticsResponse(BaseModel):
    metrics: OTPMetrics
    trends: List[Dict[str, Any]]
    breakdown: Dict[str, Any]

# ---------- OTP Error Handling ----------
class OTPError(BaseModel):
    error_code: str
    error_message: str
    session_id: Optional[str] = None
    provider: Optional[str] = None
    retry_after: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

class OTPErrorResponse(BaseModel):
    ok: bool = False
    error: OTPError

# ---------- OTP WebSocket Events ----------
class OTPWebSocketEvent(BaseModel):
    event_type: Literal["otp_code_received", "otp_applied", "otp_failed", "otp_timeout"]
    session_id: str
    data: Dict[str, Any]
    timestamp: datetime

# ---------- OTP Search & Filters ----------
class OTPSessionSearchParams(BaseModel):
    app: Optional[str] = None
    country: Optional[str] = None
    state: Optional[OTPState] = None
    provider: Optional[str] = None
    device_id: Optional[str] = None
    slot_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)

# ---------- OTP Configuration ----------
class OTPConfig(BaseModel):
    default_timeout: int = Field(300, ge=60, le=1800)  # 5 minutes default
    max_retries: int = Field(3, ge=1, le=10)
    failover_enabled: bool = True
    geo_enforcement: bool = True
    auto_ban_threshold: float = Field(0.3, ge=0.0, le=1.0)
    session_cleanup_hours: int = Field(24, ge=1, le=168)

class OTPConfigResponse(BaseModel):
    config: OTPConfig
    last_updated: datetime
    updated_by: str



