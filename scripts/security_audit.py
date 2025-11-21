# scripts/security_audit.py
"""
Script d'audit de sécurité pour vérifier les fuites de données sensibles.
Scanne le code pour détecter les codes OTP en clair, les secrets exposés, etc.
"""

import os
import re
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityAuditor:
    """Auditeur de sécurité pour détecter les fuites de données."""
    
    def __init__(self, root_dir: str = "api"):
        self.root_dir = Path(root_dir)
        self.security_issues = []
        self.otp_leaks = []
        self.secret_exposures = []
        self.pii_exposures = []
        self.files_scanned = 0
        
        # Patterns de détection
        self.otp_patterns = [
            r'code["\']?\s*[:=]\s*["\']?\d{4,8}["\']?',  # Code OTP numérique
            r'otp["\']?\s*[:=]\s*["\']?\w+["\']?',      # Variable OTP
            r'verification_code["\']?\s*[:=]\s*["\']?\w+["\']?',  # Code de vérification
            r'sms_code["\']?\s*[:=]\s*["\']?\w+["\']?',  # Code SMS
        ]
        
        self.secret_patterns = [
            r'password["\']?\s*[:=]\s*["\']?\w+["\']?',  # Mot de passe
            r'token["\']?\s*[:=]\s*["\']?\w+["\']?',     # Token
            r'secret["\']?\s*[:=]\s*["\']?\w+["\']?',    # Secret
            r'api_key["\']?\s*[:=]\s*["\']?\w+["\']?',   # Clé API
            r'private_key["\']?\s*[:=]\s*["\']?\w+["\']?',  # Clé privée
        ]
        
        self.pii_patterns = [
            r'email["\']?\s*[:=]\s*["\']?[^"\']+@[^"\']+\.[^"\']+["\']?',  # Email
            r'phone["\']?\s*[:=]\s*["\']?\+?[\d\s\-\(\)]+["\']?',  # Téléphone
            r'address["\']?\s*[:=]\s*["\']?[^"\']+["\']?',  # Adresse
            r'name["\']?\s*[:=]\s*["\']?[A-Za-z\s]+["\']?',  # Nom
            r'ssn["\']?\s*[:=]\s*["\']?\d{3}-\d{2}-\d{4}["\']?',  # SSN
        ]
        
        # Patterns de logging dangereux
        self.logging_patterns = [
            r'print\([^)]*password[^)]*\)',  # Print avec mot de passe
            r'print\([^)]*token[^)]*\)',     # Print avec token
            r'print\([^)]*secret[^)]*\)',    # Print avec secret
            r'logger\.(info|debug|warning)\([^)]*password[^)]*\)',  # Log avec mot de passe
            r'logger\.(info|debug|warning)\([^)]*token[^)]*\)',     # Log avec token
            r'logger\.(info|debug|warning)\([^)]*secret[^)]*\)',    # Log avec secret
        ]
    
    def scan_file(self, file_path: Path) -> Dict[str, List[str]]:
        """
        Scanner un fichier pour détecter les problèmes de sécurité.
        
        Args:
            file_path: Chemin du fichier à scanner
            
        Returns:
            Dictionnaire des problèmes détectés
        """
        issues = {
            'otp_leaks': [],
            'secret_exposures': [],
            'pii_exposures': [],
            'logging_issues': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Vérifier les fuites OTP
                for pattern in self.otp_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues['otp_leaks'].append({
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
                
                # Vérifier les expositions de secrets
                for pattern in self.secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues['secret_exposures'].append({
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
                
                # Vérifier les expositions PII
                for pattern in self.pii_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues['pii_exposures'].append({
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
                
                # Vérifier les problèmes de logging
                for pattern in self.logging_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues['logging_issues'].append({
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
            
            self.files_scanned += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur scan {file_path}: {e}")
        
        return issues
    
    def scan_directory(self, directory: Path) -> None:
        """Scanner un répertoire récursivement."""
        for file_path in directory.rglob("*.py"):
            if file_path.is_file():
                issues = self.scan_file(file_path)
                
                # Collecter les problèmes
                if any(issues.values()):
                    self.security_issues.append({
                        'file': str(file_path),
                        'issues': issues
                    })
    
    def check_otp_security(self) -> None:
        """Vérifier spécifiquement la sécurité OTP."""
        logger.info("🔍 Vérification de la sécurité OTP...")
        
        otp_files = list(self.root_dir.rglob("*otp*"))
        
        for file_path in otp_files:
            if file_path.is_file() and file_path.suffix == '.py':
                issues = self.scan_file(file_path)
                
                if issues['otp_leaks']:
                    self.otp_leaks.extend(issues['otp_leaks'])
                    logger.warning(f"⚠️ Fuite OTP détectée dans {file_path}")
    
    def check_secret_management(self) -> None:
        """Vérifier la gestion des secrets."""
        logger.info("🔍 Vérification de la gestion des secrets...")
        
        # Vérifier les fichiers de configuration
        config_files = list(self.root_dir.rglob("*config*"))
        config_files.extend(list(self.root_dir.rglob("*.env*")))
        
        for file_path in config_files:
            if file_path.is_file():
                issues = self.scan_file(file_path)
                
                if issues['secret_exposures']:
                    self.secret_exposures.extend(issues['secret_exposures'])
                    logger.warning(f"⚠️ Secret exposé dans {file_path}")
    
    def check_pii_handling(self) -> None:
        """Vérifier la gestion des PII."""
        logger.info("🔍 Vérification de la gestion des PII...")
        
        # Vérifier les fichiers de schémas et modèles
        schema_files = list(self.root_dir.rglob("*schema*"))
        schema_files.extend(list(self.root_dir.rglob("*model*")))
        
        for file_path in schema_files:
            if file_path.is_file() and file_path.suffix == '.py':
                issues = self.scan_file(file_path)
                
                if issues['pii_exposures']:
                    self.pii_exposures.extend(issues['pii_exposures'])
                    logger.warning(f"⚠️ PII exposée dans {file_path}")
    
    def check_logging_security(self) -> None:
        """Vérifier la sécurité des logs."""
        logger.info("🔍 Vérification de la sécurité des logs...")
        
        # Vérifier tous les fichiers Python
        for file_path in self.root_dir.rglob("*.py"):
            if file_path.is_file():
                issues = self.scan_file(file_path)
                
                if issues['logging_issues']:
                    logger.warning(f"⚠️ Problème de logging dans {file_path}")
    
    def check_environment_variables(self) -> None:
        """Vérifier la gestion des variables d'environnement."""
        logger.info("🔍 Vérification des variables d'environnement...")
        
        # Vérifier les fichiers .env
        env_files = list(self.root_dir.rglob(".env*"))
        
        for file_path in env_files:
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Vérifier les secrets en dur
                    secret_lines = []
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if '=' in line and any(secret in line.lower() for secret in ['password', 'secret', 'token', 'key']):
                            secret_lines.append({
                                'line': line_num,
                                'content': line.strip()
                            })
                    
                    if secret_lines:
                        logger.warning(f"⚠️ Secrets potentiels dans {file_path}")
                        
                except Exception as e:
                    logger.error(f"❌ Erreur lecture {file_path}: {e}")
    
    def check_database_security(self) -> None:
        """Vérifier la sécurité de la base de données."""
        logger.info("🔍 Vérification de la sécurité de la base de données...")
        
        # Vérifier les fichiers de base de données
        db_files = list(self.root_dir.rglob("*database*"))
        db_files.extend(list(self.root_dir.rglob("*db*")))
        
        for file_path in db_files:
            if file_path.is_file() and file_path.suffix == '.py':
                issues = self.scan_file(file_path)
                
                # Vérifier les requêtes non sécurisées
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Vérifier les requêtes SQL non sécurisées
                    if re.search(r'execute\([^)]*\+', content):
                        logger.warning(f"⚠️ Requête SQL potentiellement non sécurisée dans {file_path}")
                    
                    # Vérifier les requêtes MongoDB non sécurisées
                    if re.search(r'find\([^)]*\+', content):
                        logger.warning(f"⚠️ Requête MongoDB potentiellement non sécurisée dans {file_path}")
                        
                except Exception as e:
                    logger.error(f"❌ Erreur lecture {file_path}: {e}")
    
    def generate_security_report(self) -> None:
        """Générer un rapport de sécurité."""
        report = f"""
# Rapport d'audit de sécurité

## Résumé
- Fichiers scannés: {self.files_scanned}
- Problèmes de sécurité détectés: {len(self.security_issues)}
- Fuites OTP: {len(self.otp_leaks)}
- Expositions de secrets: {len(self.secret_exposures)}
- Expositions PII: {len(self.pii_exposures)}

## Problèmes détectés

### Fuites OTP
"""
        
        if self.otp_leaks:
            for leak in self.otp_leaks:
                report += f"- Ligne {leak['line']}: {leak['content']}\n"
        else:
            report += "- ✅ Aucune fuite OTP détectée\n"
        
        report += "\n### Expositions de secrets\n"
        if self.secret_exposures:
            for exposure in self.secret_exposures:
                report += f"- Ligne {exposure['line']}: {exposure['content']}\n"
        else:
            report += "- ✅ Aucune exposition de secret détectée\n"
        
        report += "\n### Expositions PII\n"
        if self.pii_exposures:
            for exposure in self.pii_exposures:
                report += f"- Ligne {exposure['line']}: {exposure['content']}\n"
        else:
            report += "- ✅ Aucune exposition PII détectée\n"
        
        report += """
## Recommandations

### Sécurité OTP
1. ✅ Vérifier que les codes OTP sont toujours masqués
2. ✅ Utiliser des fonctions de masquage appropriées
3. ✅ Ne jamais logger les codes OTP en clair

### Gestion des secrets
1. ✅ Utiliser des variables d'environnement
2. ✅ Ne jamais commiter les secrets
3. ✅ Utiliser des services de gestion de secrets

### Protection des PII
1. ✅ Chiffrer les données personnelles
2. ✅ Implémenter l'anonymisation
3. ✅ Respecter le RGPD

### Logging sécurisé
1. ✅ Ne jamais logger les secrets
2. ✅ Utiliser des niveaux de log appropriés
3. ✅ Implémenter la rotation des logs

## Actions correctives
1. Corriger les problèmes détectés
2. Implémenter les recommandations
3. Mettre en place des contrôles automatiques
4. Former l'équipe sur la sécurité
"""
        
        with open("SECURITY_AUDIT_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info("📄 Rapport de sécurité généré: SECURITY_AUDIT_REPORT.md")
    
    def run(self) -> None:
        """Exécuter l'audit de sécurité."""
        logger.info("🚀 Début de l'audit de sécurité...")
        
        if not self.root_dir.exists():
            logger.error(f"❌ Répertoire {self.root_dir} n'existe pas")
            return
        
        # Scanner le répertoire
        self.scan_directory(self.root_dir)
        
        # Vérifications spécifiques
        self.check_otp_security()
        self.check_secret_management()
        self.check_pii_handling()
        self.check_logging_security()
        self.check_environment_variables()
        self.check_database_security()
        
        # Générer le rapport
        self.generate_security_report()
        
        # Résumé
        total_issues = len(self.security_issues)
        if total_issues == 0:
            logger.info("✅ Aucun problème de sécurité détecté!")
        else:
            logger.warning(f"⚠️ {total_issues} problèmes de sécurité détectés")
        
        logger.info(f"📊 Audit terminé: {self.files_scanned} fichiers scannés")


def main():
    """Fonction principale."""
    auditor = SecurityAuditor()
    auditor.run()


if __name__ == "__main__":
    main()



