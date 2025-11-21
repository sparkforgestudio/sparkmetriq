# scripts/test_llm_connection.py
"""
Script pour tester la connexion au LLM.
"""

import os
import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.chat_omnichannel.llm_service import Message, OpenAIService, DeepSeekService
from api.services.chat_omnichannel.manager import _get_llm_service


async def test_openai():
    """Tester la connexion OpenAI."""
    print("🔍 Test de connexion OpenAI...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY non trouvée")
        return False
    
    try:
        service = OpenAIService(
            api_key=api_key,
            model=os.getenv("LLM_MODEL", "gpt-4"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
        )
        
        # Test simple
        messages = [
            Message(role="user", content="Bonjour, peux-tu me dire 'Hello World' en français?")
        ]
        
        response = await service.generate(messages=messages, tenant_id="test")
        
        print(f"✅ Connexion OpenAI réussie!")
        print(f"📝 Réponse: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur OpenAI: {e}")
        return False


async def test_deepseek():
    """Tester la connexion DeepSeek."""
    print("🔍 Test de connexion DeepSeek...")
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY non trouvée")
        return False
    
    try:
        service = DeepSeekService(
            endpoint_url=os.getenv("DEEPSEEK_ENDPOINT_URL", "https://api.deepseek.com"),
            api_key=api_key
        )
        
        # Test simple
        messages = [
            Message(role="user", content="Bonjour, peux-tu me dire 'Hello World' en français?")
        ]
        
        response = await service.generate(messages=messages, tenant_id="test")
        
        print(f"✅ Connexion DeepSeek réussie!")
        print(f"📝 Réponse: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur DeepSeek: {e}")
        return False


async def test_service_selection():
    """Tester la sélection automatique du service."""
    print("🔍 Test de sélection du service...")
    
    try:
        service = _get_llm_service()
        
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        print(f"✅ Service sélectionné: {type(service).__name__}")
        print(f"🔗 Provider configuré: {provider}")
        
        # Test simple
        messages = [
            Message(role="user", content="Dis-moi bonjour en une phrase")
        ]
        
        response = await service.generate(messages=messages, tenant_id="test")
        
        print(f"📝 Réponse: {response.text}")
        print(f"✅ Sélection automatique fonctionne!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


async def main():
    """Fonction principale."""
    print("🚀 Test de connexion LLM - musAI Platform\n")
    
    # Vérifier les variables d'environnement
    print("📋 Variables d'environnement:")
    print(f"   LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'openai')}")
    print(f"   LLM_MODEL: {os.getenv('LLM_MODEL', 'gpt-4')}")
    print(f"   LLM_TEMPERATURE: {os.getenv('LLM_TEMPERATURE', '0.7')}")
    print(f"   OPENAI_API_KEY: {'✅ Définie' if os.getenv('OPENAI_API_KEY') else '❌ Non définie'}")
    print(f"   DEEPSEEK_API_KEY: {'✅ Définie' if os.getenv('DEEPSEEK_API_KEY') else '❌ Non définie'}")
    print()
    
    # Test selon le provider
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "openai":
        success = await test_openai()
    elif provider == "deepseek":
        success = await test_deepseek()
    else:
        print(f"⚠️ Provider '{provider}' non reconnu, test de sélection automatique...")
        success = await test_service_selection()
    
    print()
    if success:
        print("✅ Tous les tests sont passés!")
        return 0
    else:
        print("❌ Certains tests ont échoué")
        print("\n📖 Consultez docs/LLM_INTEGRATION_GUIDE.md pour plus d'infos")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)



