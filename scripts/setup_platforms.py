#!/usr/bin/env python3
# scripts/setup_platforms.py
"""
Script de configuration des plateformes pour MuseMgmt Platform.
Ce script aide à configurer les credentials et les webhooks pour les nouvelles plateformes.
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

# Ajout du chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.core.platform_configs import (
    get_platform_config, get_supported_platforms, get_platform_status,
    get_webhook_endpoint, validate_platform_credentials
)
from api.databases.databases import db

class PlatformSetup:
    """Classe pour la configuration des plateformes."""
    
    def __init__(self):
        self.supported_platforms = get_supported_platforms()
    
    def display_platform_status(self):
        """Affiche le statut de configuration de toutes les plateformes."""
        print("🔍 Statut des plateformes:")
        print("=" * 60)
        
        status = get_platform_status()
        
        for platform_name, platform_status in status.items():
            status_icon = "✅" if platform_status["configured"] else "❌"
            webhook_icon = "🔗" if platform_status["webhook_supported"] else "🚫"
            
            print(f"{status_icon} {platform_name.upper()}")
            print(f"   Nom: {platform_status['name']}")
            print(f"   API: {platform_status['api_base_url']}")
            print(f"   Webhook: {webhook_icon}")
            
            if not platform_status["configured"]:
                print(f"   ❌ Variables manquantes: {', '.join(platform_status['missing_vars'])}")
            
            if platform_status["optional_vars"]:
                print(f"   ⚙️  Variables optionnelles configurées: {', '.join(platform_status['optional_vars'])}")
            
            print()
    
    def generate_env_template(self, platform_name: str = None):
        """Génère un template de variables d'environnement."""
        if platform_name:
            if platform_name not in self.supported_platforms:
                print(f"❌ Plateforme non supportée: {platform_name}")
                return
            
            config = get_platform_config(platform_name)
            print(f"🔧 Variables d'environnement pour {platform_name.upper()}:")
            print("=" * 50)
            
            for var in config.required_env_vars:
                print(f"{var}=your_{var.lower()}_here")
            
            for var in config.optional_env_vars:
                print(f"# {var}=your_{var.lower()}_here  # Optionnel")
        else:
            print("🔧 Template de variables d'environnement pour toutes les plateformes:")
            print("=" * 70)
            
            for platform_name in self.supported_platforms:
                config = get_platform_config(platform_name)
                print(f"\n# === {platform_name.upper()} ===")
                
                for var in config.required_env_vars:
                    print(f"{var}=your_{var.lower()}_here")
                
                for var in config.optional_env_vars:
                    print(f"# {var}=your_{var.lower()}_here  # Optionnel")
    
    def validate_credentials(self, platform_name: str, credentials: Dict[str, Any]) -> bool:
        """Valide les credentials d'une plateforme."""
        try:
            is_valid = validate_platform_credentials(platform_name, credentials)
            if is_valid:
                print(f"✅ Credentials valides pour {platform_name}")
            else:
                print(f"❌ Credentials invalides pour {platform_name}")
            return is_valid
        except Exception as e:
            print(f"❌ Erreur de validation: {e}")
            return False
    
    async def setup_webhook_urls(self, base_url: str):
        """Configure les URLs de webhooks pour toutes les plateformes."""
        print("🔗 Configuration des URLs de webhooks:")
        print("=" * 50)
        
        for platform_name in self.supported_platforms:
            config = get_platform_config(platform_name)
            if config.webhook_supported:
                webhook_endpoint = get_webhook_endpoint(platform_name)
                webhook_url = f"{base_url}{webhook_endpoint}"
                print(f"{platform_name.upper()}: {webhook_url}")
        
        print("\n📝 Instructions:")
        print("1. Copiez ces URLs dans la configuration de vos applications")
        print("2. Configurez les tokens de vérification dans vos variables d'environnement")
        print("3. Testez les webhooks avec les endpoints /verify")
    
    async def create_platform_collections(self):
        """Crée les collections MongoDB nécessaires pour les plateformes."""
        print("🗄️  Création des collections MongoDB:")
        print("=" * 40)
        
        collections_to_create = [
            "platform_credentials",
            "platform_logs",
            "tiktok_posts",
            "tiktok_analytics",
            "fanvue_posts",
            "fanvue_purchases",
            "fanvue_subscriptions",
            "fanvue_payments",
            "fanvue_analytics",
            "onlyfans_posts",
            "onlyfans_analytics"
        ]
        
        for collection_name in collections_to_create:
            try:
                # Vérifier si la collection existe déjà
                existing_collections = await db.list_collection_names()
                if collection_name not in existing_collections:
                    # Créer la collection avec un document vide
                    await db[collection_name].insert_one({
                        "created_at": utcnow(),
                        "setup": True
                    })
                    print(f"✅ Collection '{collection_name}' créée")
                else:
                    print(f"ℹ️  Collection '{collection_name}' existe déjà")
            except Exception as e:
                print(f"❌ Erreur création collection '{collection_name}': {e}")
    
    def generate_webhook_test_script(self):
        """Génère un script de test pour les webhooks."""
        script_content = '''#!/usr/bin/env python3
"""
Script de test des webhooks pour MuseMgmt Platform.
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Modifiez selon votre configuration
WEBHOOK_SECRET = "your_webhook_secret_here"

def test_webhook_verification(platform: str):
    """Teste la vérification de webhook."""
    verify_url = f"{BASE_URL}/webhook/{platform}/verify"
    params = {
        "hub.challenge": "test_challenge_123",
        "hub.verify_token": f"{platform.upper()}_VERIFY_TOKEN"
    }
    
    try:
        response = requests.get(verify_url, params=params)
        if response.status_code == 200:
            print(f"✅ {platform.upper()} webhook verification: OK")
            return True
        else:
            print(f"❌ {platform.upper()} webhook verification: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {platform.upper()} webhook verification: ERROR - {e}")
        return False

def test_webhook_callback(platform: str):
    """Teste le callback de webhook."""
    callback_url = f"{BASE_URL}/webhook/{platform}/callback"
    
    # Payload de test
    test_payload = {
        "event": "test_event",
        "timestamp": utcnow().isoformat(),
        "data": {
            "test": True,
            "platform": platform
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-{}-Signature".format(platform.title()): "test_signature"
    }
    
    try:
        response = requests.post(
            callback_url,
            json=test_payload,
            headers=headers
        )
        if response.status_code == 200:
            print(f"✅ {platform.upper()} webhook callback: OK")
            return True
        else:
            print(f"❌ {platform.upper()} webhook callback: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {platform.upper()} webhook callback: ERROR - {e}")
        return False

def main():
    """Fonction principale de test."""
    platforms = ["tiktok", "fanvue", "instagram", "telegram", "whatsapp"]
    
    print("🧪 Test des webhooks:")
    print("=" * 30)
    
    for platform in platforms:
        print(f"\\nTesting {platform.upper()}:")
        test_webhook_verification(platform)
        test_webhook_callback(platform)

if __name__ == "__main__":
    main()
'''
        
        with open("test_webhooks.py", "w") as f:
            f.write(script_content)
        
        print("📝 Script de test des webhooks généré: test_webhooks.py")
        print("   Exécutez: python test_webhooks.py")

def main():
    """Fonction principale."""
    setup = PlatformSetup()
    
    print("🚀 Configuration des plateformes MuseMgmt")
    print("=" * 50)
    
    while True:
        print("\\nOptions disponibles:")
        print("1. Afficher le statut des plateformes")
        print("2. Générer template .env")
        print("3. Configurer URLs webhooks")
        print("4. Créer collections MongoDB")
        print("5. Générer script de test webhooks")
        print("6. Quitter")
        
        choice = input("\\nVotre choix (1-6): ").strip()
        
        if choice == "1":
            setup.display_platform_status()
        
        elif choice == "2":
            platform = input("Plateforme spécifique (ou 'all' pour toutes): ").strip()
            if platform.lower() == "all":
                setup.generate_env_template()
            else:
                setup.generate_env_template(platform)
        
        elif choice == "3":
            base_url = input("URL de base de votre API (ex: https://api.musemgmt.com): ").strip()
            if base_url:
                asyncio.run(setup.setup_webhook_urls(base_url))
        
        elif choice == "4":
            asyncio.run(setup.create_platform_collections())
        
        elif choice == "5":
            setup.generate_webhook_test_script()
        
        elif choice == "6":
            print("👋 Au revoir!")
            break
        
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main()




