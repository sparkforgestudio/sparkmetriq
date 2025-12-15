"""
Configuration globale pour saasentialcore.

Ce module centralise toute la configuration de l'application :
- Variables d'environnement
- Paramètres de base de données
- Feature flags
- Paramètres de sécurité
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class CoreSettings(BaseSettings):
    """
    Configuration principale de saasentialcore.
    
    Toutes les variables peuvent être surchargées via variables d'environnement.
    """
    
    # Application
    app_name: str = Field(default="saasentialcore", description="Nom de l'application")
    app_version: str = Field(default="0.1.0", description="Version de l'application")
    environment: str = Field(default="development", description="Environnement (development, staging, production)")
    debug: bool = Field(default=False, description="Mode debug")
    
    # Base de données
    mongo_uri: str = Field(default="mongodb://localhost:27017", description="URI MongoDB")
    db_name: str = Field(default="saasentialcore", description="Nom de la base de données")
    
    # Sécurité
    secret_key: str = Field(default="change-me-in-production", description="Clé secrète pour JWT")
    algorithm: str = Field(default="HS256", description="Algorithme JWT")
    access_token_expire_minutes: int = Field(default=60, description="Durée d'expiration du token (minutes)")
    
    # Feature flags
    enable_scheduler: bool = Field(default=True, description="Activer le scheduler")
    enable_quotas: bool = Field(default=True, description="Activer les quotas")
    enable_metrics: bool = Field(default=True, description="Activer les métriques")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Instance globale des settings
settings = CoreSettings()

