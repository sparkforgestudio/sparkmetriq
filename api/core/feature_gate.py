# api/core/feature_gate.py
"""
Garde-fou pour vérifier les entitlements des fonctionnalités par organisation.
Utilisé dans les endpoints pour vérifier l'accès aux fonctionnalités.
"""

from fastapi import HTTPException, status
from typing import Dict, Any


def require_feature(entitlements: Dict[str, Any], feature_key: str) -> Dict[str, Any]:
    """
    Vérifie qu'une fonctionnalité est activée pour une organisation.
    
    Args:
        entitlements: Dictionnaire des entitlements de l'organisation
        feature_key: Clé de la fonctionnalité à vérifier (ex: "cloudphone", "otp")
        
    Returns:
        Dictionnaire de la fonctionnalité si activée
        
    Raises:
        HTTPException: 403 si la fonctionnalité n'est pas activée
    """
    features = (entitlements or {}).get("features", {})
    feat = features.get(feature_key)
    
    if not feat or not feat.get("active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Feature '{feature_key}' is not enabled for this organization."
        )
    
    return feat


def check_feature_enabled(entitlements: Dict[str, Any], feature_key: str) -> bool:
    """
    Vérifie si une fonctionnalité est activée (sans lever d'exception).
    
    Args:
        entitlements: Dictionnaire des entitlements de l'organisation
        feature_key: Clé de la fonctionnalité à vérifier
        
    Returns:
        True si la fonctionnalité est activée, False sinon
    """
    features = (entitlements or {}).get("features", {})
    feat = features.get(feature_key)
    return bool(feat and feat.get("active"))



