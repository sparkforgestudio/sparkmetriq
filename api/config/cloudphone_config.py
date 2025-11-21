# api/config/cloudphone_config.py
"""
Configuration centralisée pour le module CloudPhone Management + OTP Manager.
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class CloudPhoneConfig(BaseModel):
    """Configuration CloudPhone."""
    
    # API CloudPhone
    base_url: str = Field(default="https://api.cloudphone.example.com")
    api_key: str = Field(default="demo_key")
    timeout: float = Field(default=30.0)
    
    # Limites
    max_devices_per_org: int = Field(default=100)
    max_slots_per_device: int = Field(default=10)
    max_apps_per_slot: int = Field(default=1)
    
    # Timeouts
    device_start_timeout: int = Field(default=60)  # secondes
    device_stop_timeout: int = Field(default=30)
    app_install_timeout: int = Field(default=120)
    
    # Retry policy
    max_retries: int = Field(default=3)
    retry_delay: float = Field(default=1.0)
    
    @classmethod
    def from_env(cls) -> "CloudPhoneConfig":
        """Charger la configuration depuis les variables d'environnement."""
        return cls(
            base_url=os.getenv("CLOUDPHONE_BASE_URL", "https://api.cloudphone.example.com"),
            api_key=os.getenv("CLOUDPHONE_API_KEY", "demo_key"),
            timeout=float(os.getenv("CLOUDPHONE_TIMEOUT", "30.0")),
            max_devices_per_org=int(os.getenv("CLOUDPHONE_MAX_DEVICES", "100")),
            max_slots_per_device=int(os.getenv("CLOUDPHONE_MAX_SLOTS", "10")),
            max_apps_per_slot=int(os.getenv("CLOUDPHONE_MAX_APPS", "1")),
            device_start_timeout=int(os.getenv("CLOUDPHONE_START_TIMEOUT", "60")),
            device_stop_timeout=int(os.getenv("CLOUDPHONE_STOP_TIMEOUT", "30")),
            app_install_timeout=int(os.getenv("CLOUDPHONE_INSTALL_TIMEOUT", "120")),
            max_retries=int(os.getenv("CLOUDPHONE_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("CLOUDPHONE_RETRY_DELAY", "1.0"))
        )

class OTPConfig(BaseModel):
    """Configuration OTP."""
    
    # Provider principal
    primary_provider: str = Field(default="mock")
    provider_kind: str = Field(default="http_json")
    
    # HTTP Provider
    http_base_url: Optional[str] = Field(default=None)
    http_token: Optional[str] = Field(default=None)
    
    # Webhook Provider
    webhook_url: Optional[str] = Field(default=None)
    webhook_secret: Optional[str] = Field(default=None)
    
    # Timeouts et limites
    session_timeout_minutes: int = Field(default=10)
    max_concurrent_sessions: int = Field(default=50)
    max_sessions_per_hour: int = Field(default=1000)
    
    # Budgets par défaut
    daily_budget_default: float = Field(default=100.0)
    monthly_budget_default: float = Field(default=2000.0)
    
    # Qualité
    min_success_rate: float = Field(default=0.8)
    max_response_time: int = Field(default=60)  # secondes
    
    # Sécurité
    code_mask_char: str = Field(default="*")
    code_mask_length: int = Field(default=4)
    encrypt_codes: bool = Field(default=True)
    
    @classmethod
    def from_env(cls) -> "OTPConfig":
        """Charger la configuration depuis les variables d'environnement."""
        return cls(
            primary_provider=os.getenv("OTP_PRIMARY_PROVIDER", "mock"),
            provider_kind=os.getenv("OTP_PROVIDER_KIND", "http_json"),
            http_base_url=os.getenv("OTP_HTTP_BASE_URL"),
            http_token=os.getenv("OTP_HTTP_TOKEN"),
            webhook_url=os.getenv("OTP_WEBHOOK_URL"),
            webhook_secret=os.getenv("OTP_WEBHOOK_SECRET"),
            session_timeout_minutes=int(os.getenv("OTP_SESSION_TIMEOUT", "10")),
            max_concurrent_sessions=int(os.getenv("OTP_MAX_CONCURRENT", "50")),
            max_sessions_per_hour=int(os.getenv("OTP_MAX_PER_HOUR", "1000")),
            daily_budget_default=float(os.getenv("OTP_DAILY_BUDGET", "100.0")),
            monthly_budget_default=float(os.getenv("OTP_MONTHLY_BUDGET", "2000.0")),
            min_success_rate=float(os.getenv("OTP_MIN_SUCCESS_RATE", "0.8")),
            max_response_time=int(os.getenv("OTP_MAX_RESPONSE_TIME", "60")),
            code_mask_char=os.getenv("OTP_CODE_MASK_CHAR", "*"),
            code_mask_length=int(os.getenv("OTP_CODE_MASK_LENGTH", "4")),
            encrypt_codes=os.getenv("OTP_ENCRYPT_CODES", "true").lower() == "true"
        )

class ObservabilityConfig(BaseModel):
    """Configuration observabilité."""
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    # Métriques
    enable_prometheus: bool = Field(default=True)
    prometheus_port: int = Field(default=8000)
    
    # Alertes
    enable_websockets: bool = Field(default=True)
    enable_telegram: bool = Field(default=False)
    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_chat_id: Optional[str] = Field(default=None)
    
    # Audit
    enable_audit_logs: bool = Field(default=True)
    audit_retention_days: int = Field(default=90)
    
    @classmethod
    def from_env(cls) -> "ObservabilityConfig":
        """Charger la configuration depuis les variables d'environnement."""
        return cls(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            enable_prometheus=os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true",
            prometheus_port=int(os.getenv("PROMETHEUS_PORT", "8000")),
            enable_websockets=os.getenv("ENABLE_WEBSOCKETS", "true").lower() == "true",
            enable_telegram=os.getenv("ENABLE_TELEGRAM", "false").lower() == "true",
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            enable_audit_logs=os.getenv("ENABLE_AUDIT_LOGS", "true").lower() == "true",
            audit_retention_days=int(os.getenv("AUDIT_RETENTION_DAYS", "90"))
        )

class DatabaseConfig(BaseModel):
    """Configuration base de données."""
    
    # MongoDB
    mongo_uri: str = Field(default="mongodb://localhost:27017")
    mongo_db: str = Field(default="musai_dev")
    
    # Pool de connexions
    max_pool_size: int = Field(default=100)
    min_pool_size: int = Field(default=10)
    
    # Timeouts
    server_selection_timeout: int = Field(default=5000)  # ms
    socket_timeout: int = Field(default=20000)  # ms
    
    # Index
    auto_create_indexes: bool = Field(default=True)
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Charger la configuration depuis les variables d'environnement."""
        return cls(
            mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
            mongo_db=os.getenv("MONGO_DB", "musai_dev"),
            max_pool_size=int(os.getenv("MONGO_MAX_POOL_SIZE", "100")),
            min_pool_size=int(os.getenv("MONGO_MIN_POOL_SIZE", "10")),
            server_selection_timeout=int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT", "5000")),
            socket_timeout=int(os.getenv("MONGO_SOCKET_TIMEOUT", "20000")),
            auto_create_indexes=os.getenv("MONGO_AUTO_CREATE_INDEXES", "true").lower() == "true"
        )

class CloudPhoneModuleConfig(BaseModel):
    """Configuration complète du module CloudPhone."""
    
    cloudphone: CloudPhoneConfig
    otp: OTPConfig
    observability: ObservabilityConfig
    database: DatabaseConfig
    
    @classmethod
    def from_env(cls) -> "CloudPhoneModuleConfig":
        """Charger toute la configuration depuis les variables d'environnement."""
        return cls(
            cloudphone=CloudPhoneConfig.from_env(),
            otp=OTPConfig.from_env(),
            observability=ObservabilityConfig.from_env(),
            database=DatabaseConfig.from_env()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire pour le logging."""
        return {
            "cloudphone": self.cloudphone.dict(),
            "otp": self.otp.dict(),
            "observability": self.observability.dict(),
            "database": self.database.dict()
        }

# Instance globale de configuration
config = CloudPhoneModuleConfig.from_env()



