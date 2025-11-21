# api/core/settings.py
"""
Configuration centralisée de l'application musAI Platform.
Compatible Pydantic v2 + pydantic-settings.
- 2 bases Mongo: CORE (musai_core) & BI (musai_bi)
- Feature flags MAJUSCULES (ENABLE_BI, ENABLE_SCHEDULER, ENABLE_CLOUDPHONE, ENABLE_OTP)
"""

from __future__ import annotations

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


# ------------------------------
# Sous-configurations
# ------------------------------
class DatabaseSettings(BaseSettings):
    """Configuration générique MongoDB (non utilisée pour CORE/BI, conservée si besoin d'un 3e DSN)."""

    mongo_uri: str = Field(
        default="mongodb://localhost:27017",
        description="URI MongoDB (générique)"
    )
    mongo_db: str = Field(
        default="musai_dev",
        description="Nom de la base générique"
    )
    max_pool_size: int = Field(100, description="Taille maximale du pool")
    min_pool_size: int = Field(10, description="Taille minimale du pool")
    server_selection_timeout: int = Field(5000, description="Timeout sélection serveur (ms)")
    socket_timeout: int = Field(20000, description="Timeout socket (ms)")
    auto_create_indexes: bool = Field(True, description="Création auto des index")

    model_config = ConfigDict(env_prefix="MONGO_")


class SecuritySettings(BaseSettings):
    """Sécurité & RGPD."""
    secret_key: str = Field("your-secret-key-change-in-production", description="Clé JWT")
    algorithm: str = Field("HS256", description="Algorithme JWT")
    access_token_expire_minutes: int = Field(30, description="Expiration token d'accès (min)")
    refresh_token_expire_days: int = Field(7, description="Expiration token refresh (jours)")

    encrypt_pii: bool = Field(True, description="Chiffrement données PII")
    pii_retention_days: int = Field(90, description="Rétention PII (jours)")
    anonymize_logs: bool = Field(True, description="Anonymisation des logs")

    model_config = ConfigDict(env_prefix="SECURITY_")


class CloudPhoneSettings(BaseSettings):
    """CloudPhone Management (monolith-plugin activable)."""
    base_url: str = Field("https://api.cloudphone.example.com", description="URL API CloudPhone")
    api_key: str = Field("demo_key", description="Clé API CloudPhone")
    timeout: float = Field(30.0, description="Timeout requêtes (s)")
    max_devices_per_org: int = Field(100, description="Max devices / organisation")
    max_slots_per_device: int = Field(10, description="Max slots / device")
    max_apps_per_slot: int = Field(1, description="Max apps / slot")
    device_start_timeout: int = Field(60, description="Timeout start device (s)")
    device_stop_timeout: int = Field(30, description="Timeout stop device (s)")
    app_install_timeout: int = Field(120, description="Timeout install app (s)")
    max_retries: int = Field(3, description="Nombre de retries")
    retry_delay: float = Field(1.0, description="Délai entre retries (s)")

    model_config = ConfigDict(env_prefix="CLOUDPHONE_")


class OTPSettings(BaseSettings):
    """OTP Manager (abstraction provider)."""
    primary_provider: str = Field("mock", description="Provider principal")
    provider_kind: str = Field("http_json", description="Type de provider OTP")

    http_base_url: Optional[str] = Field(None, description="Base URL provider HTTP")
    http_token: Optional[str] = Field(None, description="Token provider HTTP")

    webhook_url: Optional[str] = Field(None, description="URL webhook OTP")
    webhook_secret: Optional[str] = Field(None, description="Secret webhook OTP")

    session_timeout_minutes: int = Field(10, description="Timeout session OTP (min)")
    max_concurrent_sessions: int = Field(50, description="Max sessions concurrentes")
    max_sessions_per_hour: int = Field(1000, description="Max sessions / heure")

    daily_budget_default: float = Field(100.0, description="Budget quotidien par défaut")
    monthly_budget_default: float = Field(2000.0, description="Budget mensuel par défaut")

    min_success_rate: float = Field(0.8, description="Taux de succès minimum")
    max_response_time: int = Field(60, description="Temps de réponse max (s)")

    code_mask_char: str = Field("*", description="Caractère de masquage code")
    code_mask_length: int = Field(4, description="Longueur de masquage code")
    encrypt_codes: bool = Field(True, description="Chiffrer les codes OTP en base")

    model_config = ConfigDict(env_prefix="OTP_")


class ObservabilitySettings(BaseSettings):
    """Observabilité (logs / métriques / alertes)."""
    log_level: str = Field("INFO", description="Niveau de logs")
    log_format: str = Field("json", description="Format de logs (json|plain)")
    enable_prometheus: bool = Field(True, description="Activer métriques Prometheus")
    prometheus_port: int = Field(8000, description="Port Prometheus")
    enable_websockets: bool = Field(True, description="Activer WebSockets")
    enable_telegram: bool = Field(False, description="Activer notifications Telegram")
    telegram_bot_token: Optional[str] = Field(None, description="Token bot Telegram")
    telegram_chat_id: Optional[str] = Field(None, description="Chat ID Telegram")
    enable_audit_logs: bool = Field(True, description="Activer logs d'audit")
    audit_retention_days: int = Field(90, description="Rétention logs d'audit (jours)")

    model_config = ConfigDict(env_prefix="OBSERVABILITY_")


class ChatSettings(BaseSettings):
    """Chat omnicanal + RAG (messages)."""
    collection_name: str = Field("chat_messages", description="Collection Mongo des messages")
    max_history_messages: int = Field(50, description="Max messages retournés (historique)")

    enable_rag: bool = Field(True, description="Activer RAG (chat)")
    rag_model: str = Field("text-embedding-ada-002", description="Modèle d'embedding")
    rag_top_k: int = Field(5, description="Top K similarités")
    rag_threshold: float = Field(0.7, description="Seuil de similarité")

    model_config = ConfigDict(env_prefix="CHAT_")


# ------------------------------
# Settings principale
# ------------------------------
class Settings(BaseSettings):
    """Configuration principale musAI."""

    # --- Infos app ---
    APP_NAME: str = Field("    APP_NAME: str = Field("Sparkmetriq", description="Nom de l'application")
", description="Nom de l'application")
    APP_VERSION: str = Field("1.0.0", description="Version")
    DEBUG: bool = Field(False, description="Mode debug")
    ENVIRONMENT: str = Field("development", description="Environment (development|staging|production)")

    # --- Feature flags (MAJUSCULES car référencés dans le code) ---
    ENABLE_BI: bool = Field(True, description="Activer le module BI (Insights & Pricing)")
    ENABLE_SCHEDULER: bool = Field(True, description="Activer le Scheduler de publication")
    ENABLE_CLOUDPHONE: bool = Field(False, description="Activer le module CloudPhone")
    ENABLE_OTP: bool = Field(False, description="Activer le module OTP")
    FEATURE_TRANSLATOR_ENABLED: bool = Field(True, description="Activer Traducteur IA")
    FEATURE_CONVO_RECAP_ENABLED: bool = Field(True, description="Activer Recap IA des conversations")
    FEATURE_MESSAGE_BUILDER_ENABLED: bool = Field(True, description="Activer Message Builder")
    FEATURE_LINK_TRACKING_ENABLED: bool = Field(True, description="Activer tracking liens marketing")
    FEATURE_COLLAB_ENABLED: bool = Field(True, description="Activer collaboration interne")
    FEATURE_COLLAB_INTEGRATIONS: bool = Field(True, description="Activer intégrations ClickUp/Notion")

    # --- Bases de données (2 DSN explicites) ---
    MONGO_URI: str = Field("mongodb://localhost:27017", description="URI MongoDB (CORE)")
    DB_NAME_CORE: str = Field("musai_core", description="Nom DB CORE")

    MONGO_URI_BI: str = Field("mongodb://localhost:27017", description="URI MongoDB (BI)")
    DB_NAME_BI: str = Field("musai_bi", description="Nom DB BI")

    # --- LLM & modules IA (extraits nécessaires) ---
    TRANSLATOR_LLM_BASE_URL: Optional[str] = Field(None, description="Base URL LLM (translator)")
    TRANSLATOR_LLM_MODEL: str = Field("deepseek-chat", description="Modèle LLM pour traduction")
    LANG_DETECT_BACKEND: str = Field("langdetect", description="Backend détection langue")
    TRANSLATOR_MAX_CHARS: int = Field(2000, description="Max caractères / traduction")
    TRANSLATOR_DEFAULT_TONE: str = Field("neutral", description="Ton par défaut")
    TRANSLATOR_DEFAULT_EMOJI: str = Field("medium", description="Niveau d'emojis")
    TRANSLATOR_DEFAULT_FORMALITY: str = Field("standard", description="Formalité")

    RECAP_LLM_BASE_URL: Optional[str] = Field(None, description="Base URL LLM (recap)")
    RECAP_LLM_MODEL: str = Field("deepseek-chat", description="Modèle LLM recap")
    RECAP_MAX_MESSAGES_PER_CALL: int = Field(200, description="Max messages par recap")
    RECAP_MAX_CHARS: int = Field(12000, description="Max chars transcript recap")
    RECAP_AUTO_ENABLED: bool = Field(False, description="Recap auto")
    RECAP_IDLE_MINUTES: int = Field(30, description="Minutes d'inactivité avant recap auto")
    RECAP_MIN_NEW_MSG: int = Field(20, description="Min nouveaux messages avant recap auto")

    # --- Message Builder ---
    MB_MAX_TARGETS_PREVIEW: int = Field(50, description="Max cibles en preview")
    MB_MAX_TARGETS_SEND: int = Field(20000, description="Max cibles par envoi")
    MB_RATE_PER_MINUTE: int = Field(600, description="Débit global/min (outbox)")
    MB_TEMPLATE_MAX_CHARS: int = Field(4000, description="Max caractères template")
    MB_ALLOW_LINKS: bool = Field(True, description="Autoriser http/https dans template")
    MB_ENABLE_SCHEDULER: bool = Field(True, description="Scheduler d'envoi activé")

    # --- Link Tracking & Attribution ---
    TRACKING_DOMAIN_BASE: str = Field("http://localhost:8000", description="Domaine base /r/{code}")
    ATTRIBUTION_MODEL: str = Field("last_touch", description="Modèle d'attribution (last_touch|first_touch)")
    CLICK_IP_HASH_SALT: str = Field("change-me", description="Salt pour hash IP de clic")
    TRACK_MAX_REDIRECTS_PER_MIN: int = Field(5000, description="Max redirections / min")
    TRACK_CODE_LENGTH: int = Field(8, description="Longueur codes de liens courts")

    # --- Collaboration ---
    COLLAB_WS_PATH: str = Field("/ws/collab", description="Path WebSocket collaboration")
    COLLAB_REMINDER_INTERVAL_SEC: int = Field(60, description="Intervalle vérification rappels (s)")
    CLICKUP_API_TOKEN: Optional[str] = Field(None, description="Token ClickUp")
    NOTION_API_TOKEN: Optional[str] = Field(None, description="Token Notion")

    # --- Évolution microservice (désactivée par défaut) ---
    USE_REMOTE_CLOUDPHONE: bool = Field(False, description="Utiliser CloudPhone distant")
    USE_REMOTE_OTP: bool = Field(False, description="Utiliser OTP distant")
    CLOUDPHONE_BASE_URL: Optional[str] = Field(None, description="URL CloudPhone externe")
    CLOUDPHONE_S2S_TOKEN: Optional[str] = Field(None, description="S2S CloudPhone")
    OTP_BASE_URL: Optional[str] = Field(None, description="URL OTP externe")
    OTP_S2S_TOKEN: Optional[str] = Field(None, description="S2S OTP")

    # Sous-blocs
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cloudphone: CloudPhoneSettings = Field(default_factory=CloudPhoneSettings)
    otp: OTPSettings = Field(default_factory=OTPSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    chat: ChatSettings = Field(default_factory=ChatSettings)

    # Config Pydantic v2
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="",               # pas de préfixe global
        populate_by_name=True,       # accepte alias/nom champ
        validate_assignment=True,
    )

    # ---- Validators ----
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @field_validator("DEBUG")
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        data = getattr(info, "data", {}) or {}
        if data.get("ENVIRONMENT") == "production" and v:
            raise ValueError("DEBUG cannot be enabled in production")
        return v

    # ---- Helpers ----
    @property
    def is_prod(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def app_version(self) -> str:
        """Alias pour APP_VERSION (compatibilité avec code existant)."""
        return self.APP_VERSION

    @property
    def environment(self) -> str:
        """Alias pour ENVIRONMENT (compatibilité avec code existant)."""
        return self.ENVIRONMENT

    @property
    def core_dsn(self) -> str:
        return f"{self.MONGO_URI}/{self.DB_NAME_CORE}"

    @property
    def bi_dsn(self) -> str:
        return f"{self.MONGO_URI_BI}/{self.DB_NAME_BI}"


# Instance globale + getter
settings = Settings()


def get_settings() -> Settings:
    return settings
