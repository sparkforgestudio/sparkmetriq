# api/services/intent/validator.py
"""
Validateur de messages pour le Moteur d'Intentions.
Vérifie la conformité et les règles de sécurité.
"""

import logging
from typing import Dict, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class MessageValidator:
    """Validateur de messages."""
    
    # Longueurs max par plateforme (caractères)
    MAX_LENGTH_BY_PLATFORM = {
        "instagram": 1000,
        "tiktok": 2200,
        "telegram": 4096,
        "onlyfans": 1000,
        "reddit": 10000,
        "x": 280
    }
    
    def __init__(
        self,
        forbidden_words: Optional[Set[str]] = None,
        max_length: Optional[int] = None,
        platform: str = "instagram"
    ):
        """
        Initialise le validateur.
        
        Args:
            forbidden_words: Mots interdits
            max_length: Longueur maximale (si None, utilise la valeur par défaut de la plateforme)
            platform: Plateforme pour déterminer la longueur max
        """
        self.forbidden_words = set(forbidden_words or [])
        self.platform = platform
        
        if max_length is None:
            self.max_length = self.MAX_LENGTH_BY_PLATFORM.get(platform, 1000)
        else:
            self.max_length = max_length
    
    def validate(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Valide un texte.
        
        Args:
            text: Texte à valider
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Le texte ne peut pas être vide"
        
        # Vérifier la longueur
        if len(text) > self.max_length:
            return False, f"Texte trop long ({len(text)} > {self.max_length} caractères)"
        
        # Vérifier les mots interdits
        text_lower = text.lower()
        for word in self.forbidden_words:
            if word.lower() in text_lower:
                logger.warning(
                    f"Message rejeté: mot interdit '{word}' détecté "
                    f"(platform={self.platform})"
                )
                return False, f"Mot interdit détecté: '{word}'"
        
        return True, None
    
    def update_policies(self, policies: Dict[str, Any]):
        """
        Met à jour les règles depuis les politiques.
        
        Args:
            policies: Dictionnaire de politiques (compliance, etc.)
        """
        compliance = policies.get("compliance", {})
        
        # Mettre à jour les mots interdits
        if "forbidden_words" in compliance:
            self.forbidden_words = set(compliance["forbidden_words"])
        
        # Mettre à jour la longueur max si spécifiée
        if "max_length" in compliance:
            self.max_length = compliance["max_length"]
        
        logger.debug(
            f"Validator policies updated: forbidden_words={len(self.forbidden_words)}, "
            f"max_length={self.max_length}"
        )
