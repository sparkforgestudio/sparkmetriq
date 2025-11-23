# chat_tests/talent/test_inbox_smoke.py
"""
Tests d'intégration pour l'inbox des talents.
"""

from fastapi.testclient import TestClient
from datetime import datetime

def test_inbox_empty(test_client: TestClient, mongo_client):
    """Test de l'inbox vide."""
    r = test_client.get("/api/talent/inbox")
    assert r.status_code == 200
    j = r.json()
    assert "items" in j and isinstance(j["items"], list)

def test_inbox_with_data(test_client: TestClient, mongo_client):
    """Test de l'inbox avec des données."""
    # Seed des threads
    mongo_client["chat_threads"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": "fan_abc",
            "platform": "instagram",
            "last_message": "Hello there",
            "last_ts": utcnow(),
            "unseen_count": 1,
            "priority": 0,
            "tags": []
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": "fan_def",
            "platform": "twitter",
            "last_message": "How are you?",
            "last_ts": utcnow(),
            "unseen_count": 0,
            "priority": 1,
            "tags": ["vip"]
        }
    ])
    
    r = test_client.get("/api/talent/inbox")
    assert r.status_code == 200
    j = r.json()
    assert j["total"] >= 2
    assert len(j["items"]) >= 2

def test_inbox_filters(test_client: TestClient, mongo_client):
    """Test des filtres de l'inbox."""
    # Seed des données
    mongo_client["chat_threads"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_ghi",
        "platform": "instagram",
        "last_message": "Test message",
        "last_ts": utcnow(),
        "unseen_count": 1,
        "priority": 0,
        "tags": ["vip"]
    })
    
    # Test filtre par muse
    r1 = test_client.get("/api/talent/inbox", params={"muse_id": "melissa"})
    assert r1.status_code == 200
    
    # Test filtre par plateforme
    r2 = test_client.get("/api/talent/inbox", params={"platform": "instagram"})
    assert r2.status_code == 200
    
    # Test filtre par statut VIP
    r3 = test_client.get("/api/talent/inbox", params={"status": "vip"})
    assert r3.status_code == 200
    
    # Test filtre par statut nouveau
    r4 = test_client.get("/api/talent/inbox", params={"status": "new"})
    assert r4.status_code == 200

def test_thread_details(test_client: TestClient, mongo_client):
    """Test des détails d'un thread."""
    # Seed un thread
    mongo_client["chat_threads"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_jkl",
        "platform": "instagram",
        "last_message": "Hello",
        "last_ts": utcnow(),
        "unseen_count": 1,
        "priority": 0,
        "tags": []
    })
    
    # Seed des messages
    mongo_client["chat_messages"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_id": "fan_jkl",
            "role": "user",
            "text": "Hello",
            "timestamp": utcnow()
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_id": "fan_jkl",
            "role": "bot",
            "text": "Hi there!",
            "timestamp": utcnow()
        }
    ])
    
    r = test_client.get("/api/talent/inbox/melissa/fan_jkl")
    assert r.status_code == 200
    j = r.json()
    assert "thread" in j
    assert "message_count" in j
    assert j["message_count"] >= 2

def test_search_threads(test_client: TestClient, mongo_client):
    """Test de la recherche dans les threads."""
    # Seed des threads avec des messages différents
    mongo_client["chat_threads"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": "fan_mno",
            "platform": "instagram",
            "last_message": "Looking for content",
            "last_ts": utcnow(),
            "unseen_count": 0,
            "priority": 0,
            "tags": []
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": "fan_pqr",
            "platform": "twitter",
            "last_message": "Different message",
            "last_ts": utcnow(),
            "unseen_count": 0,
            "priority": 0,
            "tags": []
        }
    ])
    
    r = test_client.get("/api/talent/inbox/search", params={"q": "content"})
    assert r.status_code == 200
    results = r.json()
    assert isinstance(results, list)
    # Au moins un résultat devrait contenir "content"
    assert any("content" in thread["last_message"].lower() for thread in results)




