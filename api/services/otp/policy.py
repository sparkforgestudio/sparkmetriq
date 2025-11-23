# api/services/otp/policy.py
"""
Politiques OTP pour la géolocalisation et la conformité.
Enforcement des règles métier pour les réservations OTP.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class OTPPolicy:
    """Politiques OTP pour la géolocalisation et la conformité."""
    
    def __init__(self):
        # Mapping pays -> zone géographique
        self.country_to_area = {
            "US": "US",
            "CA": "US",  # Canada dans la zone US
            "MX": "US",  # Mexique dans la zone US
            "FR": "EU",
            "DE": "EU",
            "GB": "EU",
            "ES": "EU",
            "IT": "EU",
            "NL": "EU",
            "BE": "EU",
            "CH": "EU",
            "AT": "EU",
            "SE": "EU",
            "NO": "EU",
            "DK": "EU",
            "FI": "EU",
            "PL": "EU",
            "CZ": "EU",
            "HU": "EU",
            "RO": "EU",
            "BG": "EU",
            "HR": "EU",
            "SI": "EU",
            "SK": "EU",
            "LT": "EU",
            "LV": "EU",
            "EE": "EU",
            "IE": "EU",
            "PT": "EU",
            "GR": "EU",
            "CY": "EU",
            "MT": "EU",
            "LU": "EU",
            "JP": "ASIA",
            "KR": "ASIA",
            "CN": "ASIA",
            "IN": "ASIA",
            "TH": "ASIA",
            "SG": "ASIA",
            "MY": "ASIA",
            "ID": "ASIA",
            "PH": "ASIA",
            "VN": "ASIA",
            "TW": "ASIA",
            "HK": "ASIA",
            "AU": "ASIA",  # Australie dans la zone ASIA
            "NZ": "ASIA",  # Nouvelle-Zélande dans la zone ASIA
            "BR": "LATAM",
            "AR": "LATAM",
            "CL": "LATAM",
            "CO": "LATAM",
            "PE": "LATAM",
            "VE": "LATAM",
            "UY": "LATAM",
            "PY": "LATAM",
            "BO": "LATAM",
            "EC": "LATAM",
            "GY": "LATAM",
            "SR": "LATAM",
            "GF": "LATAM"
        }
        
        # Restrictions par app
        self.app_restrictions = {
            "instagram": {
                "allowed_countries": ["US", "FR", "DE", "GB", "ES", "IT", "CA", "AU"],
                "blocked_countries": ["CN", "IR", "KP"],
                "min_age": 13,
                "requires_verification": True
            },
            "telegram": {
                "allowed_countries": [],  # Tous les pays autorisés
                "blocked_countries": ["CN", "IR", "RU"],  # Pays avec restrictions
                "min_age": 13,
                "requires_verification": False
            },
            "tiktok": {
                "allowed_countries": ["US", "FR", "DE", "GB", "ES", "IT", "CA", "AU", "BR"],
                "blocked_countries": ["CN", "IN"],  # TikTok interdit dans certains pays
                "min_age": 13,
                "requires_verification": True
            },
            "twitter": {
                "allowed_countries": [],  # Tous les pays autorisés
                "blocked_countries": ["CN", "IR", "KP"],
                "min_age": 13,
                "requires_verification": False
            },
            "reddit": {
                "allowed_countries": [],  # Tous les pays autorisés
                "blocked_countries": ["CN", "IR"],
                "min_age": 13,
                "requires_verification": False
            },
            "onlyfans": {
                "allowed_countries": ["US", "FR", "DE", "GB", "ES", "IT", "CA", "AU", "BR"],
                "blocked_countries": ["CN", "IR", "SA", "AE"],  # Restrictions légales
                "min_age": 18,
                "requires_verification": True
            }
        }
        
        # Limites par organisation
        self.org_limits = {
            "max_concurrent_sessions": 10,
            "max_daily_sessions": 100,
            "max_monthly_sessions": 2000,
            "max_cost_per_day": 50.0,
            "max_cost_per_month": 1000.0
        }
    
    def enforce_geo(self, country: str, device: Dict[str, Any], constraints: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Enforcer la politique de géolocalisation.
        
        Args:
            country: Code pays ISO
            device: Informations du device
            constraints: Contraintes de la réservation
            
        Returns:
            Tuple (is_valid, reason)
        """
        # Vérifier si l'enforcement géo est activé
        if not constraints.get("geo_enforce", True):
            return True, "Geo enforcement disabled"
        
        # Vérifier la cohérence pays/device
        device_area = device.get("area")
        country_area = self.country_to_area.get(country)
        
        if device_area and country_area and device_area != country_area:
            return False, f"Country {country} (area: {country_area}) doesn't match device area {device_area}"
        
        # Vérifier les restrictions par app
        app = constraints.get("app")
        if app and app in self.app_restrictions:
            restrictions = self.app_restrictions[app]
            
            # Vérifier les pays autorisés
            if restrictions["allowed_countries"] and country not in restrictions["allowed_countries"]:
                return False, f"Country {country} not allowed for app {app}"
            
            # Vérifier les pays bloqués
            if country in restrictions["blocked_countries"]:
                return False, f"Country {country} is blocked for app {app}"
        
        return True, "Geo policy passed"
    
    def check_app_restrictions(self, app: str, country: str) -> Tuple[bool, str]:
        """
        Vérifier les restrictions spécifiques à une app.
        
        Args:
            app: Application cible
            country: Code pays ISO
            
        Returns:
            Tuple (is_allowed, reason)
        """
        if app not in self.app_restrictions:
            return True, "No restrictions for this app"
        
        restrictions = self.app_restrictions[app]
        
        # Vérifier les pays autorisés
        if restrictions["allowed_countries"] and country not in restrictions["allowed_countries"]:
            return False, f"Country {country} not in allowed list for {app}"
        
        # Vérifier les pays bloqués
        if country in restrictions["blocked_countries"]:
            return False, f"Country {country} is blocked for {app}"
        
        return True, "App restrictions passed"
    
    def check_org_limits(self, org_id: str, current_usage: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Vérifier les limites de l'organisation.
        
        Args:
            org_id: ID de l'organisation
            current_usage: Usage actuel de l'organisation
            
        Returns:
            Tuple (within_limits, reason)
        """
        # Vérifier les sessions concurrentes
        concurrent = current_usage.get("concurrent_sessions", 0)
        if concurrent >= self.org_limits["max_concurrent_sessions"]:
            return False, f"Max concurrent sessions reached ({concurrent}/{self.org_limits['max_concurrent_sessions']})"
        
        # Vérifier les sessions quotidiennes
        daily = current_usage.get("daily_sessions", 0)
        if daily >= self.org_limits["max_daily_sessions"]:
            return False, f"Max daily sessions reached ({daily}/{self.org_limits['max_daily_sessions']})"
        
        # Vérifier les sessions mensuelles
        monthly = current_usage.get("monthly_sessions", 0)
        if monthly >= self.org_limits["max_monthly_sessions"]:
            return False, f"Max monthly sessions reached ({monthly}/{self.org_limits['max_monthly_sessions']})"
        
        # Vérifier le coût quotidien
        daily_cost = current_usage.get("daily_cost", 0.0)
        if daily_cost >= self.org_limits["max_cost_per_day"]:
            return False, f"Max daily cost reached (${daily_cost:.2f}/${self.org_limits['max_cost_per_day']})"
        
        # Vérifier le coût mensuel
        monthly_cost = current_usage.get("monthly_cost", 0.0)
        if monthly_cost >= self.org_limits["max_cost_per_month"]:
            return False, f"Max monthly cost reached (${monthly_cost:.2f}/${self.org_limits['max_cost_per_month']})"
        
        return True, "Organization limits passed"
    
    def get_country_area(self, country: str) -> str:
        """Récupérer la zone géographique d'un pays."""
        return self.country_to_area.get(country, "UNKNOWN")
    
    def get_supported_countries(self, app: str) -> List[str]:
        """Récupérer la liste des pays supportés pour une app."""
        if app not in self.app_restrictions:
            return list(self.country_to_area.keys())
        
        restrictions = self.app_restrictions[app]
        
        if restrictions["allowed_countries"]:
            return restrictions["allowed_countries"]
        
        # Retourner tous les pays sauf ceux bloqués
        all_countries = list(self.country_to_area.keys())
        blocked = restrictions["blocked_countries"]
        return [country for country in all_countries if country not in blocked]
    
    def get_app_requirements(self, app: str) -> Dict[str, Any]:
        """Récupérer les exigences d'une app."""
        return self.app_restrictions.get(app, {
            "allowed_countries": [],
            "blocked_countries": [],
            "min_age": 13,
            "requires_verification": False
        })
    
    def validate_session_constraints(self, constraints: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valider les contraintes d'une session OTP.
        
        Args:
            constraints: Contraintes de la session
            
        Returns:
            Tuple (is_valid, reason)
        """
        app = constraints.get("app")
        country = constraints.get("country")
        
        if not app:
            return False, "App is required"
        
        if not country:
            return False, "Country is required"
        
        # Vérifier les restrictions de l'app
        is_allowed, reason = self.check_app_restrictions(app, country)
        if not is_allowed:
            return False, reason
        
        # Vérifier l'âge minimum
        age = constraints.get("age")
        if age:
            requirements = self.get_app_requirements(app)
            if age < requirements["min_age"]:
                return False, f"Age {age} below minimum {requirements['min_age']} for {app}"
        
        return True, "Constraints validated"
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Récupérer un résumé des politiques."""
        return {
            "country_areas": self.country_to_area,
            "app_restrictions": self.app_restrictions,
            "org_limits": self.org_limits,
            "total_countries": len(self.country_to_area),
            "total_apps": len(self.app_restrictions)
        }

# Instance globale de la politique
otp_policy = OTPPolicy()

# Fonctions de convenance
def enforce_geo(country: str, device: Dict[str, Any], constraints: Dict[str, Any]) -> Tuple[bool, str]:
    """Enforcer la politique de géolocalisation."""
    return otp_policy.enforce_geo(country, device, constraints)

def check_app_restrictions(app: str, country: str) -> Tuple[bool, str]:
    """Vérifier les restrictions d'une app."""
    return otp_policy.check_app_restrictions(app, country)

def check_org_limits(org_id: str, current_usage: Dict[str, Any]) -> Tuple[bool, str]:
    """Vérifier les limites d'une organisation."""
    return otp_policy.check_org_limits(org_id, current_usage)

def get_supported_countries(app: str) -> List[str]:
    """Récupérer les pays supportés pour une app."""
    return otp_policy.get_supported_countries(app)

def validate_session_constraints(constraints: Dict[str, Any]) -> Tuple[bool, str]:
    """Valider les contraintes d'une session."""
    return otp_policy.validate_session_constraints(constraints)




