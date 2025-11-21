# api/services/otp/providers/registry.py
"""
Registry des providers OTP avec configuration générique.
Adapter configurable via variables d'environnement.
"""

import os
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from api.services.otp.providers.base import BaseOTPProvider, MockOTPProvider

class AdapterConfig:
    """Configuration pour l'adapter OTP."""
    
    def __init__(self):
        self.kind = os.getenv("OTP_PRIMARY_ADAPTER", "mock")
        self.base_url = os.getenv("OTP_ADAPTER_HTTP_BASE_URL", "")
        self.token = os.getenv("OTP_ADAPTER_HTTP_TOKEN", "")
        self.timeout = int(os.getenv("OTP_ADAPTER_TIMEOUT", "30"))
        
        # Mappings app -> serviceId
        self.app_mappings = {
            "instagram": os.getenv("OTP_APP_INSTAGRAM_ID", "instagram"),
            "telegram": os.getenv("OTP_APP_TELEGRAM_ID", "telegram"),
            "tiktok": os.getenv("OTP_APP_TIKTOK_ID", "tiktok"),
            "twitter": os.getenv("OTP_APP_TWITTER_ID", "twitter"),
            "reddit": os.getenv("OTP_APP_REDDIT_ID", "reddit"),
            "onlyfans": os.getenv("OTP_APP_ONLYFANS_ID", "onlyfans")
        }
        
        # Mappings country -> serviceId
        self.country_mappings = {
            "US": os.getenv("OTP_COUNTRY_US_ID", "us"),
            "FR": os.getenv("OTP_COUNTRY_FR_ID", "fr"),
            "DE": os.getenv("OTP_COUNTRY_DE_ID", "de"),
            "GB": os.getenv("OTP_COUNTRY_GB_ID", "gb"),
            "CA": os.getenv("OTP_COUNTRY_CA_ID", "ca")
        }
        
        # Configuration des pools
        self.pool_config = {
            "max_concurrent": int(os.getenv("OTP_MAX_CONCURRENT", "10")),
            "default_timeout": int(os.getenv("OTP_DEFAULT_TIMEOUT", "300")),
            "retry_count": int(os.getenv("OTP_RETRY_COUNT", "3"))
        }

class HTTPJSONAdapter(BaseOTPProvider):
    """Adapter HTTP JSON générique pour les providers OTP."""
    
    def __init__(self, config: AdapterConfig):
        super().__init__("http_json", config.__dict__)
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json"
            }
        )
    
    async def _reserve_number_impl(self, app: str, country: str, **kwargs) -> Dict[str, Any]:
        """Réservation via API HTTP."""
        service_id = self.config.app_mappings.get(app, app)
        country_id = self.config.country_mappings.get(country, country)
        
        payload = {
            "service": service_id,
            "country": country_id,
            "timeout": kwargs.get("timeout", self.config.pool_config["default_timeout"]),
            **kwargs
        }
        
        response = await self.client.post(f"{self.config.base_url}/reserve", json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "provider_session_id": data.get("session_id"),
            "number": data.get("number"),
            "cost": data.get("cost", 0.0),
            "expires_at": data.get("expires_at")
        }
    
    async def _get_sms_impl(self, provider_session_id: str) -> Optional[str]:
        """Récupération SMS via API HTTP."""
        response = await self.client.get(f"{self.config.base_url}/sms/{provider_session_id}")
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        return data.get("sms_text")
    
    async def _cancel_impl(self, provider_session_id: str) -> None:
        """Annulation via API HTTP."""
        await self.client.post(f"{self.config.base_url}/cancel/{provider_session_id}")
    
    async def _ban_impl(self, provider_session_id: str) -> None:
        """Bannissement via API HTTP."""
        await self.client.post(f"{self.config.base_url}/ban/{provider_session_id}")
    
    async def _health_impl(self) -> Dict[str, Any]:
        """Vérification de santé via API HTTP."""
        try:
            response = await self.client.get(f"{self.config.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self):
        """Fermer le client HTTP."""
        await self.client.aclose()

class WebhookAdapter(BaseOTPProvider):
    """Adapter Webhook pour les providers OTP."""
    
    def __init__(self, config: AdapterConfig):
        super().__init__("webhook", config.__dict__)
        self.config = config
        self.webhook_url = os.getenv("OTP_WEBHOOK_URL", "")
        self.webhook_secret = os.getenv("OTP_WEBHOOK_SECRET", "")
    
    async def _reserve_number_impl(self, app: str, country: str, **kwargs) -> Dict[str, Any]:
        """Réservation via webhook."""
        # Implémentation webhook - à adapter selon le provider
        return {
            "provider_session_id": f"webhook_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "number": f"+1{country}5550000",
            "cost": 0.05,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        }
    
    async def _get_sms_impl(self, provider_session_id: str) -> Optional[str]:
        """Récupération SMS via webhook."""
        # Implémentation webhook - à adapter selon le provider
        return None
    
    async def _cancel_impl(self, provider_session_id: str) -> None:
        """Annulation via webhook."""
        pass
    
    async def _ban_impl(self, provider_session_id: str) -> None:
        """Bannissement via webhook."""
        pass
    
    async def _health_impl(self) -> Dict[str, Any]:
        """Vérification de santé webhook."""
        return {
            "status": "healthy",
            "webhook_url": self.webhook_url
        }

class ProviderRegistry:
    """Registry des providers OTP."""
    
    def __init__(self):
        self._providers: Dict[str, BaseOTPProvider] = {}
        self._primary_provider: Optional[str] = None
        self._config = AdapterConfig()
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialiser les providers disponibles."""
        # Provider mock pour les tests
        self._providers["mock"] = MockOTPProvider()
        
        # Provider HTTP JSON si configuré
        if self._config.kind == "http_json" and self._config.base_url:
            self._providers["http_json"] = HTTPJSONAdapter(self._config)
            self._primary_provider = "http_json"
        
        # Provider Webhook si configuré
        elif self._config.kind == "webhook" and self._config.webhook_url:
            self._providers["webhook"] = WebhookAdapter(self._config)
            self._primary_provider = "webhook"
        
        # Fallback sur mock
        if not self._primary_provider:
            self._primary_provider = "mock"
    
    def get_provider(self, name: Optional[str] = None) -> BaseOTPProvider:
        """Récupérer un provider par nom."""
        provider_name = name or self._primary_provider
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        return self._providers[provider_name]
    
    def get_primary_provider(self) -> BaseOTPProvider:
        """Récupérer le provider principal."""
        return self.get_provider(self._primary_provider)
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """Lister tous les providers disponibles."""
        providers = []
        for name, provider in self._providers.items():
            providers.append({
                "name": name,
                "is_primary": name == self._primary_provider,
                "config": provider.config
            })
        return providers
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Vérifier la santé de tous les providers."""
        health_results = {}
        for name, provider in self._providers.items():
            try:
                health_results[name] = await provider.health()
            except Exception as e:
                health_results[name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        return health_results
    
    async def get_provider_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques de tous les providers."""
        metrics = {}
        for name, provider in self._providers.items():
            metrics[name] = provider.get_metrics()
        return metrics
    
    def add_provider(self, name: str, provider: BaseOTPProvider):
        """Ajouter un provider personnalisé."""
        self._providers[name] = provider
    
    def remove_provider(self, name: str):
        """Supprimer un provider."""
        if name in self._providers:
            del self._providers[name]
            if self._primary_provider == name:
                self._primary_provider = "mock"  # Fallback sur mock

# Instance globale du registry
provider_registry = ProviderRegistry()

# Fonctions de convenance
def get_primary_adapter() -> BaseOTPProvider:
    """Récupérer l'adapter principal."""
    return provider_registry.get_primary_provider()

def get_adapter(name: Optional[str] = None) -> BaseOTPProvider:
    """Récupérer un adapter par nom."""
    return provider_registry.get_provider(name)

def build_primary_adapter() -> BaseOTPProvider:
    """Construire l'adapter principal (alias pour compatibilité)."""
    return get_primary_adapter()

async def health_check_adapters() -> Dict[str, Any]:
    """Vérifier la santé de tous les adapters."""
    return await provider_registry.health_check_all()

def list_available_adapters() -> List[Dict[str, Any]]:
    """Lister les adapters disponibles."""
    return provider_registry.list_providers()
