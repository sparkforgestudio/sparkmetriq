# api/services/otp/parsers.py
"""
Parsers pour extraire les codes OTP des SMS.
Regex par app, jamais de code en clair exposé.
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime, timezone

class OTPParser:
    """Parser pour extraire les codes OTP des SMS."""
    
    def __init__(self):
        # Patterns de codes OTP par app
        self.patterns = {
            "instagram": [
                r"(\d{6})",  # Code à 6 chiffres
                r"code[:\s]+(\d{6})",
                r"verification[:\s]+(\d{6})",
                r"instagram[:\s]+(\d{6})"
            ],
            "telegram": [
                r"(\d{5})",  # Code à 5 chiffres
                r"code[:\s]+(\d{5})",
                r"telegram[:\s]+(\d{5})",
                r"login[:\s]+(\d{5})"
            ],
            "tiktok": [
                r"(\d{6})",
                r"code[:\s]+(\d{6})",
                r"tiktok[:\s]+(\d{6})",
                r"verification[:\s]+(\d{6})"
            ],
            "twitter": [
                r"(\d{6})",
                r"code[:\s]+(\d{6})",
                r"twitter[:\s]+(\d{6})",
                r"verification[:\s]+(\d{6})"
            ],
            "reddit": [
                r"(\d{6})",
                r"code[:\s]+(\d{6})",
                r"reddit[:\s]+(\d{6})",
                r"verification[:\s]+(\d{6})"
            ],
            "onlyfans": [
                r"(\d{6})",
                r"code[:\s]+(\d{6})",
                r"onlyfans[:\s]+(\d{6})",
                r"verification[:\s]+(\d{6})"
            ]
        }
        
        # Patterns génériques
        self.generic_patterns = [
            r"(\d{4,8})",  # Codes de 4 à 8 chiffres
            r"code[:\s]+(\d{4,8})",
            r"verification[:\s]+(\d{4,8})",
            r"otp[:\s]+(\d{4,8})",
            r"pin[:\s]+(\d{4,8})"
        ]
    
    def extract_code(self, app: str, sms_text: str) -> Optional[str]:
        """
        Extraire le code OTP d'un SMS pour une app donnée.
        
        Args:
            app: Application cible
            sms_text: Texte du SMS
            
        Returns:
            Code OTP extrait ou None si non trouvé
        """
        if not sms_text or not app:
            return None
        
        # Nettoyer le texte
        clean_text = sms_text.strip().lower()
        
        # Essayer les patterns spécifiques à l'app
        app_patterns = self.patterns.get(app, [])
        for pattern in app_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                code = match.group(1)
                if self._is_valid_code(code, app):
                    return code
        
        # Essayer les patterns génériques
        for pattern in self.generic_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                code = match.group(1)
                if self._is_valid_code(code, app):
                    return code
        
        return None
    
    def _is_valid_code(self, code: str, app: str) -> bool:
        """Vérifier si un code est valide pour une app."""
        if not code or not code.isdigit():
            return False
        
        # Longueurs attendues par app
        expected_lengths = {
            "instagram": [6],
            "telegram": [5],
            "tiktok": [6],
            "twitter": [6],
            "reddit": [6],
            "onlyfans": [6]
        }
        
        expected = expected_lengths.get(app, [4, 5, 6])
        return len(code) in expected
    
    def mask_code(self, code: str) -> str:
        """
        Masquer un code OTP pour l'affichage.
        
        Args:
            code: Code OTP complet
            
        Returns:
            Code masqué (ex: "123***" pour "123456")
        """
        if not code or len(code) < 3:
            return "***"
        
        # Garder les 3 premiers caractères, masquer le reste
        visible_part = code[:3]
        masked_part = "*" * (len(code) - 3)
        return f"{visible_part}{masked_part}"
    
    def extract_message_preview(self, sms_text: str, max_length: int = 50) -> str:
        """
        Extraire un aperçu du message SMS.
        
        Args:
            sms_text: Texte du SMS
            max_length: Longueur maximale de l'aperçu
            
        Returns:
            Aperçu du message
        """
        if not sms_text:
            return ""
        
        # Nettoyer et tronquer
        clean_text = sms_text.strip()
        if len(clean_text) <= max_length:
            return clean_text
        
        return clean_text[:max_length] + "..."
    
    def parse_sms_metadata(self, sms_text: str) -> Dict[str, Any]:
        """
        Parser les métadonnées d'un SMS.
        
        Args:
            sms_text: Texte du SMS
            
        Returns:
            Métadonnées extraites
        """
        metadata = {
            "length": len(sms_text) if sms_text else 0,
            "has_code": False,
            "language": "unknown",
            "sender_hint": None,
            "timestamp_hint": None
        }
        
        if not sms_text:
            return metadata
        
        clean_text = sms_text.lower()
        
        # Détecter la présence d'un code
        for pattern in self.generic_patterns:
            if re.search(pattern, clean_text):
                metadata["has_code"] = True
                break
        
        # Détecter la langue (basique)
        if any(word in clean_text for word in ["code", "verification", "otp"]):
            metadata["language"] = "en"
        elif any(word in clean_text for word in ["code", "vérification", "otp"]):
            metadata["language"] = "fr"
        elif any(word in clean_text for word in ["código", "verificación"]):
            metadata["language"] = "es"
        
        # Détecter des indices sur l'expéditeur
        sender_patterns = {
            "instagram": ["instagram", "meta"],
            "telegram": ["telegram"],
            "tiktok": ["tiktok", "bytedance"],
            "twitter": ["twitter", "x.com"],
            "reddit": ["reddit"],
            "onlyfans": ["onlyfans"]
        }
        
        for app, patterns in sender_patterns.items():
            if any(pattern in clean_text for pattern in patterns):
                metadata["sender_hint"] = app
                break
        
        # Détecter des indices temporels
        time_patterns = [
            r"(\d{1,2}:\d{2})",  # HH:MM
            r"(\d{1,2}/\d{1,2}/\d{4})",  # MM/DD/YYYY
            r"(\d{4}-\d{2}-\d{2})"  # YYYY-MM-DD
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, sms_text)
            if match:
                metadata["timestamp_hint"] = match.group(1)
                break
        
        return metadata

# Instance globale du parser
otp_parser = OTPParser()

# Fonctions de convenance
def extract_code(app: str, sms_text: str) -> Optional[str]:
    """Extraire un code OTP."""
    return otp_parser.extract_code(app, sms_text)

def mask_code(code: str) -> str:
    """Masquer un code OTP."""
    return otp_parser.mask_code(code)

def extract_message_preview(sms_text: str, max_length: int = 50) -> str:
    """Extraire un aperçu de message."""
    return otp_parser.extract_message_preview(sms_text, max_length)

def parse_sms_metadata(sms_text: str) -> Dict[str, Any]:
    """Parser les métadonnées d'un SMS."""
    return otp_parser.parse_sms_metadata(sms_text)

# Tests unitaires intégrés
def test_parser():
    """Tests du parser OTP."""
    parser = OTPParser()
    
    # Tests d'extraction
    test_cases = [
        ("instagram", "Your Instagram code is: 123456", "123456"),
        ("telegram", "Login code: 54321", "54321"),
        ("tiktok", "TikTok verification code 987654", "987654"),
        ("twitter", "Twitter code: 111222", "111222"),
        ("reddit", "Reddit verification: 555666", "555666"),
        ("onlyfans", "OnlyFans code: 777888", "777888")
    ]
    
    for app, sms, expected in test_cases:
        result = parser.extract_code(app, sms)
        assert result == expected, f"Failed for {app}: expected {expected}, got {result}"
    
    # Tests de masquage
    assert parser.mask_code("123456") == "123***"
    assert parser.mask_code("12345") == "123**"
    assert parser.mask_code("123") == "123"
    assert parser.mask_code("12") == "***"
    
    # Tests d'aperçu
    assert parser.extract_message_preview("Short message") == "Short message"
    assert parser.extract_message_preview("This is a very long message that should be truncated") == "This is a very long message that should be..."
    
    print("All parser tests passed!")

if __name__ == "__main__":
    test_parser()




