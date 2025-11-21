# api/core/rate_limit.py
"""
Rate limiter simple en mémoire pour le traducteur (MVP).
Pour la production, préférer Redis ou un système distribué.
"""

import time
from collections import defaultdict
from typing import Tuple, Dict
from api.core.settings import settings


# Compteurs en mémoire par fenêtre temporelle (MVP)
_minute_window: defaultdict[str, list] = defaultdict(list)  # org_id -> [timestamps]
_day_window: defaultdict[str, list] = defaultdict(list)     # org_id -> [timestamps]


def allow(org_id: str) -> Tuple[bool, str]:
    """
    Vérifie si une requête est autorisée selon les limites de débit.
    
    Args:
        org_id: ID de l'organisation
        
    Returns:
        Tuple (autorisé, raison)
        - (True, "ok") si autorisé
        - (False, "rate_limit_minute") si limite par minute atteinte
        - (False, "rate_limit_daily") si limite quotidienne atteinte
    """
    now = time.time()
    minute_limit = settings.translator_max_rpm
    daily_limit = settings.translator_max_rpd
    
    # Nettoyer les timestamps expirés (fenêtre glissante)
    _minute_window[org_id] = [
        t for t in _minute_window[org_id] 
        if now - t < 60  # Dernière minute
    ]
    _day_window[org_id] = [
        t for t in _day_window[org_id] 
        if now - t < 86400  # Dernières 24 heures
    ]
    
    # Vérifier les limites
    if len(_minute_window[org_id]) >= minute_limit:
        return False, "rate_limit_minute"
    
    if len(_day_window[org_id]) >= daily_limit:
        return False, "rate_limit_daily"
    
    # Enregistrer cette requête
    _minute_window[org_id].append(now)
    _day_window[org_id].append(now)
    
    return True, "ok"


def reset(org_id: str):
    """
    Réinitialise les compteurs pour une organisation (utile pour les tests).
    
    Args:
        org_id: ID de l'organisation
    """
    _minute_window[org_id] = []
    _day_window[org_id] = []


def get_stats(org_id: str) -> Dict[str, int]:
    """
    Récupère les statistiques de taux pour une organisation.
    
    Args:
        org_id: ID de l'organisation
        
    Returns:
        Dictionnaire avec les statistiques
    """
    now = time.time()
    
    # Nettoyer et compter
    minute_count = len([
        t for t in _minute_window[org_id] 
        if now - t < 60
    ])
    daily_count = len([
        t for t in _day_window[org_id] 
        if now - t < 86400
    ])
    
    return {
        "minute_count": minute_count,
        "minute_limit": settings.translator_max_rpm,
        "daily_count": daily_count,
        "daily_limit": settings.translator_max_rpd
    }
