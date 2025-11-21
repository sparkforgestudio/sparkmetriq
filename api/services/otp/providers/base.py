# api/services/otp/providers/base.py
"""
Interface générique pour les providers OTP (aucun nom de provider).
Protocole agnostique pour l'intégration de différents services OTP.
"""

from typing import Protocol, Optional, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime, timezone

class OTPProvider(Protocol):
    """Protocole pour les providers OTP."""
    
    name: str
    
    async def reserve_number(self, app: str, country: str, **kwargs) -> Dict[str, Any]:
        """
        Réserver un numéro pour recevoir un SMS.
        
        Args:
            app: Application cible (instagram, telegram, etc.)
            country: Code pays ISO (US, FR, etc.)
            **kwargs: Paramètres additionnels spécifiques au provider
            
        Returns:
            Dict contenant:
            - provider_session_id: ID de session du provider
            - number: Numéro de téléphone réservé
            - cost: Coût de la réservation (optionnel)
            - expires_at: Date d'expiration (optionnel)
        """
        ...
    
    async def get_sms(self, provider_session_id: str) -> Optional[str]:
        """
        Récupérer le SMS reçu.
        
        Args:
            provider_session_id: ID de session du provider
            
        Returns:
            Texte du SMS ou None si pas encore reçu
        """
        ...
    
    async def cancel(self, provider_session_id: str) -> None:
        """
        Annuler une réservation.
        
        Args:
            provider_session_id: ID de session du provider
        """
        ...
    
    async def ban(self, provider_session_id: str) -> None:
        """
        Bannir un numéro (en cas de problème).
        
        Args:
            provider_session_id: ID de session du provider
        """
        ...
    
    async def health(self) -> Dict[str, Any]:
        """
        Vérifier la santé du provider.
        
        Returns:
            Dict contenant:
            - status: "healthy", "degraded", "unhealthy"
            - response_time: Temps de réponse en ms
            - success_rate: Taux de succès (0.0-1.0)
            - available_countries: Liste des pays disponibles
        """
        ...

class BaseOTPProvider(ABC):
    """Classe de base abstraite pour les providers OTP."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self._success_count = 0
        self._total_count = 0
        self._response_times = []
    
    @abstractmethod
    async def _reserve_number_impl(self, app: str, country: str, **kwargs) -> Dict[str, Any]:
        """Implémentation spécifique de la réservation."""
        pass
    
    @abstractmethod
    async def _get_sms_impl(self, provider_session_id: str) -> Optional[str]:
        """Implémentation spécifique de la récupération SMS."""
        pass
    
    @abstractmethod
    async def _cancel_impl(self, provider_session_id: str) -> None:
        """Implémentation spécifique de l'annulation."""
        pass
    
    @abstractmethod
    async def _ban_impl(self, provider_session_id: str) -> None:
        """Implémentation spécifique du bannissement."""
        pass
    
    async def reserve_number(self, app: str, country: str, **kwargs) -> Dict[str, Any]:
        """Réservation avec métriques."""
        import time
        start_time = time.time()
        
        try:
            result = await self._reserve_number_impl(app, country, **kwargs)
            self._success_count += 1
            self._total_count += 1
            
            response_time = (time.time() - start_time) * 1000
            self._response_times.append(response_time)
            
            # Garder seulement les 100 derniers temps de réponse
            if len(self._response_times) > 100:
                self._response_times = self._response_times[-100:]
            
            return result
            
        except Exception as e:
            self._total_count += 1
            raise e
    
    async def get_sms(self, provider_session_id: str) -> Optional[str]:
        """Récupération SMS avec métriques."""
        import time
        start_time = time.time()
        
        try:
            result = await self._get_sms_impl(provider_session_id)
            
            response_time = (time.time() - start_time) * 1000
            self._response_times.append(response_time)
            
            if len(self._response_times) > 100:
                self._response_times = self._response_times[-100:]
            
            return result
            
        except Exception as e:
            raise e
    
    async def cancel(self, provider_session_id: str) -> None:
        """Annulation."""
        await self._cancel_impl(provider_session_id)
    
    async def ban(self, provider_session_id: str) -> None:
        """Bannissement."""
        await self._ban_impl(provider_session_id)
    
    async def health(self) -> Dict[str, Any]:
        """Vérification de santé avec métriques."""
        try:
            # Test de connectivité basique
            import time
            start_time = time.time()
            
            # Appel de santé spécifique si implémenté
            if hasattr(self, '_health_impl'):
                health_data = await self._health_impl()
            else:
                health_data = {"status": "healthy"}
            
            response_time = (time.time() - start_time) * 1000
            
            # Calculer les métriques
            success_rate = self._success_count / self._total_count if self._total_count > 0 else 1.0
            avg_response_time = sum(self._response_times) / len(self._response_times) if self._response_times else 0.0
            
            return {
                "status": health_data.get("status", "healthy"),
                "response_time": response_time,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "total_requests": self._total_count,
                "successful_requests": self._success_count,
                "provider_name": self.name,
                **health_data
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider_name": self.name
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques du provider."""
        return {
            "provider_name": self.name,
            "success_count": self._success_count,
            "total_count": self._total_count,
            "success_rate": self._success_count / self._total_count if self._total_count > 0 else 0.0,
            "avg_response_time": sum(self._response_times) / len(self._response_times) if self._response_times else 0.0,
            "recent_response_times": self._response_times[-10:] if self._response_times else []
        }

class MockOTPProvider(BaseOTPProvider):
    """Provider OTP mock pour les tests."""
    
    def __init__(self, name: str = "mock", config: Dict[str, Any] = None):
        super().__init__(name, config or {})
        self._sessions = {}
        self._sms_messages = {}
    
    async def _reserve_number_impl(self, app: str, country: str, **kwargs) -> Dict[str, Any]:
        """Mock de réservation."""
        import uuid
        from datetime import datetime, timezone, timedelta
        
        session_id = str(uuid.uuid4())
        number = f"+1{country}555{str(uuid.uuid4())[:4]}"
        
        self._sessions[session_id] = {
            "app": app,
            "country": country,
            "number": number,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        
        return {
            "provider_session_id": session_id,
            "number": number,
            "cost": 0.05,
            "expires_at": self._sessions[session_id]["expires_at"].isoformat()
        }
    
    async def _get_sms_impl(self, provider_session_id: str) -> Optional[str]:
        """Mock de récupération SMS."""
        if provider_session_id not in self._sessions:
            return None
        
        # Simuler un SMS après 2 secondes
        session = self._sessions[provider_session_id]
        created_at = session["created_at"]
        now = datetime.now(timezone.utc)
        
        if (now - created_at).total_seconds() > 2:
            # Générer un code mock
            import random
            code = str(random.randint(100000, 999999))
            sms_text = f"Your verification code is: {code}"
            
            self._sms_messages[provider_session_id] = sms_text
            return sms_text
        
        return None
    
    async def _cancel_impl(self, provider_session_id: str) -> None:
        """Mock d'annulation."""
        if provider_session_id in self._sessions:
            del self._sessions[provider_session_id]
        if provider_session_id in self._sms_messages:
            del self._sms_messages[provider_session_id]
    
    async def _ban_impl(self, provider_session_id: str) -> None:
        """Mock de bannissement."""
        await self._cancel_impl(provider_session_id)
    
    async def _health_impl(self) -> Dict[str, Any]:
        """Mock de santé."""
        return {
            "status": "healthy",
            "available_countries": ["US", "FR", "DE", "GB"],
            "supported_apps": ["instagram", "telegram", "tiktok", "twitter"]
        }
