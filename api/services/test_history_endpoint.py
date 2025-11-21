import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from api.main import app  # Entrypoint FastAPI

client = TestClient(app)

@pytest.fixture

def setup_data(mongo_client):
    """
    Prépare des messages de test pour la conversation 'conv123'.
    """
    coll = mongo_client['chat_messages']
    # Insérer deux messages (user puis bot)
    docs = [
        {
            'conversation_id': 'conv123',
            'message': 'Hello',
            'role': 'user',
            'timestamp': datetime(2025, 5, 1, 12, 0)
        },
        {
            'conversation_id': 'conv123',
            'message': 'Reply',
            'role': 'bot',
            'timestamp': datetime(2025, 5, 1, 12, 1)
        }
    ]
    coll.insert_many(docs)
    yield
    # Nettoyage après test
    coll.delete_many({'conversation_id': 'conv123'})


def test_get_history_default(setup_data):
    """
    Teste la récupération paginée par défaut (skip=0, limit=50).
    """
    resp = client.get('/chat/history/conv123')
    assert resp.status_code == 200
    body = resp.json()

    # Vérifier les métadonnées de pagination
    assert body['conversation_id'] == 'conv123'
    assert body['skip'] == 0
    assert body['limit'] == 50
    assert body['total'] == 2

    # Vérifier le contenu des messages
    messages = body['messages']
    assert isinstance(messages, list)
    assert len(messages) == 2
    assert messages[0]['message'] == 'Hello'
    assert messages[1]['message'] == 'Reply'
