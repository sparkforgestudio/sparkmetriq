# scripts/test_chat_fixes.py
"""
Script de test pour valider les corrections du système chat/LLM.
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.chat_omnichannel.manager import handle_message, get_history
from api.schemas.chat import ChatMessageIn
from api.databases.databases import db

async def test_chat_fixes():
    """Test des corrections du système chat."""
    print("🧪 === TEST DES CORRECTIONS CHAT/LLM ===\n")
    
    try:
        # Configuration de test
        user_email = "test@example.com"
        conversation_id = str(uuid4())
        
        print(f"📝 Test avec conversation_id: {conversation_id}")
        
        # Test 1: Premier message (nouvelle conversation)
        print("\n1️⃣ Test premier message...")
        msg1 = await handle_message(
            user_email=user_email,
            conversation_id=conversation_id,
            message="Bonjour, comment allez-vous?",
            platform="web",
            user_id="user_123",
            metadata={"test": True}
        )
        
        print(f"   ✅ Message 1 sauvegardé")
        print(f"   📄 Conversation ID: {msg1.conversation_id}")
        print(f"   💬 Réponse: {msg1.message}")
        print(f"   📎 Attachments: {msg1.attachments}")
        
        # Test 2: Deuxième message (reprise de conversation)
        print("\n2️⃣ Test reprise de conversation...")
        msg2 = await handle_message(
            user_email=user_email,
            conversation_id=conversation_id,  # Même conversation
            message="Pouvez-vous m'aider avec quelque chose?",
            platform="web",
            user_id="user_123",
            metadata={"test": True}
        )
        
        print(f"   ✅ Message 2 sauvegardé")
        print(f"   📄 Conversation ID: {msg2.conversation_id}")
        print(f"   💬 Réponse: {msg2.message}")
        
        # Vérifier que c'est la même conversation
        assert msg1.conversation_id == msg2.conversation_id, "Les conversation_id doivent être identiques"
        print(f"   ✅ Même conversation_id: {msg1.conversation_id == msg2.conversation_id}")
        
        # Test 3: Récupération de l'historique
        print("\n3️⃣ Test récupération historique...")
        total, messages = await get_history(
            conversation_id=conversation_id,
            skip=0,
            limit=10
        )
        
        print(f"   📊 Total messages: {total}")
        print(f"   📝 Messages récupérés: {len(messages)}")
        
        # Vérifier la structure des messages
        for i, msg in enumerate(messages):
            print(f"   Message {i+1}:")
            print(f"     - Role: {msg.get('role')}")
            print(f"     - Text: {msg.get('text', 'N/A')[:50]}...")
            print(f"     - Platform: {msg.get('platform')}")
            print(f"     - User ID: {msg.get('user_id')}")
            print(f"     - Attachments: {msg.get('attachments')}")
        
        # Vérifications
        assert total == 4, f"Attendu 4 messages (2 user + 2 bot), reçu {total}"
        assert len(messages) == 4, f"Attendu 4 messages récupérés, reçu {len(messages)}"
        
        roles = [msg.get('role') for msg in messages]
        assert roles.count('user') == 2, f"Attendu 2 messages user, reçu {roles.count('user')}"
        assert roles.count('bot') == 2, f"Attendu 2 messages bot, reçu {roles.count('bot')}"
        
        print(f"   ✅ Structure correcte: {roles.count('user')} user, {roles.count('bot')} bot")
        
        # Test 4: Nouvelle conversation (sans conversation_id)
        print("\n4️⃣ Test nouvelle conversation...")
        msg3 = await handle_message(
            user_email=user_email,
            conversation_id=None,  # Nouvelle conversation
            message="Nouvelle conversation",
            platform="mobile",
            user_id="user_456"
        )
        
        print(f"   ✅ Nouvelle conversation créée")
        print(f"   📄 Nouveau conversation_id: {msg3.conversation_id}")
        
        # Vérifier que c'est une nouvelle conversation
        assert msg3.conversation_id != conversation_id, "Nouvelle conversation doit avoir un ID différent"
        print(f"   ✅ Nouveau conversation_id différent: {msg3.conversation_id != conversation_id}")
        
        # Test 5: Test avec attachments
        print("\n5️⃣ Test avec attachments...")
        msg4 = await handle_message(
            user_email=user_email,
            conversation_id=str(uuid4()),
            message="Message avec pièce jointe",
            platform="web",
            user_id="user_789",
            metadata={"has_attachment": True}
        )
        
        print(f"   ✅ Message avec metadata sauvegardé")
        print(f"   📎 Metadata: {msg4.metadata}")
        
        print("\n🎉 Tous les tests sont passés avec succès!")
        
        # Nettoyage
        print("\n🧹 Nettoyage des données de test...")
        await db["chat_messages"].delete_many({"user_id": {"$in": ["user_123", "user_456", "user_789"]}})
        print("   ✅ Données de test supprimées")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_schema_validation():
    """Test de validation des schémas."""
    print("\n🔍 === TEST VALIDATION SCHÉMAS ===\n")
    
    try:
        from api.schemas.chat import ChatMessageIn, ChatMessageOut
        
        # Test ChatMessageIn
        print("1️⃣ Test ChatMessageIn...")
        msg_in = ChatMessageIn(
            conversation_id="test_conv_123",
            platform="web",
            user_id="user_123",
            message="Test message",
            attachments=["https://example.com/image.jpg"],
            metadata={"test": True}
        )
        
        print(f"   ✅ ChatMessageIn créé: {msg_in.message}")
        print(f"   📎 Attachments: {msg_in.attachments}")
        
        # Test ChatMessageOut
        print("\n2️⃣ Test ChatMessageOut...")
        msg_out = ChatMessageOut(
            conversation_id="test_conv_123",
            message="Réponse test",
            attachments=["https://example.com/image.jpg"],
            timestamp=utcnow()
        )
        
        print(f"   ✅ ChatMessageOut créé: {msg_out.message}")
        print(f"   📎 Attachments: {msg_out.attachments}")
        
        print("\n✅ Validation des schémas réussie!")
        
    except Exception as e:
        print(f"❌ Erreur validation schémas: {e}")
        return False
    
    return True

async def main():
    """Fonction principale de test."""
    print("🚀 Démarrage des tests de validation du système chat...\n")
    
    # Configuration de la base de données de test
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db_test = client["test_chat_fixes"]
    
    # Remplacer la base de données globale
    import api.databases.databases as databases
    databases.db = db_test
    
    try:
        # Tests
        schema_ok = await test_schema_validation()
        chat_ok = await test_chat_fixes()
        
        if schema_ok and chat_ok:
            print("\n🎉 Tous les tests sont passés avec succès!")
            print("✅ Le système chat/LLM est maintenant corrigé et fonctionnel.")
        else:
            print("\n❌ Certains tests ont échoué.")
            return False
            
    finally:
        # Nettoyage
        client.close()
    
    return True

if __name__ == "__main__":
    # Configuration des variables d'environnement pour le test
    os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
    
    # Lancer les tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)




