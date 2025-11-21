# chat_tests/talent/test_tag_note_escalate.py
"""
Tests d'intégration pour le tagging, les notes et l'escalade.
"""

from fastapi.testclient import TestClient
from datetime import datetime

def test_tag_note_escalate(test_client: TestClient, mongo_client):
    """Test complet du tagging, des notes et de l'escalade."""
    # Seed un thread
    mongo_client["chat_threads"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_abc",
        "platform": "instagram",
        "last_message": "hello",
        "last_ts": utcnow(),
        "unseen_count": 1,
        "priority": 0,
        "tags": []
    })
    
    # Test ajout de tag
    r1 = test_client.post("/api/talent/fans/tag", json={
        "muse_id": "melissa",
        "user_hash": "fan_abc",
        "tag": "vip"
    })
    assert r1.status_code == 200
    
    # Vérifier que le tag a été ajouté
    thread = mongo_client["chat_threads"].find_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_abc"
    })
    assert "vip" in thread["tags"]
    
    # Test ajout de note
    r2 = test_client.post("/api/talent/fans/note", json={
        "muse_id": "melissa",
        "user_hash": "fan_abc",
        "text": "aime les oranges"
    })
    assert r2.status_code == 200
    assert "id" in r2.json()
    
    # Test récupération des notes
    r3 = test_client.get("/api/talent/fans/notes", params={
        "muse_id": "melissa",
        "user_hash": "fan_abc"
    })
    assert r3.status_code == 200
    notes = r3.json()
    assert isinstance(notes, list)
    assert len(notes) >= 1
    assert any("oranges" in note["text"] for note in notes)
    
    # Test escalade
    r4 = test_client.post("/api/talent/inbox/escalate", params={
        "muse_id": "melissa",
        "user_hash": "fan_abc",
        "level": 2,
        "reason": "Customer complaint"
    })
    assert r4.status_code == 200
    
    # Vérifier que la priorité a été mise à jour
    thread = mongo_client["chat_threads"].find_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_abc"
    })
    assert thread["priority"] >= 2

def test_bulk_tagging(test_client: TestClient, mongo_client):
    """Test du tagging en lot."""
    # Seed plusieurs threads
    fan_hashes = ["fan_1", "fan_2", "fan_3"]
    for fan_hash in fan_hashes:
        mongo_client["chat_threads"].insert_one({
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": fan_hash,
            "platform": "instagram",
            "last_message": f"Message from {fan_hash}",
            "last_ts": utcnow(),
            "unseen_count": 0,
            "priority": 0,
            "tags": []
        })
    
    # Test tagging en lot
    r = test_client.post("/api/talent/fans/tag/bulk", params={
        "muse_id": "melissa",
        "tag": "premium"
    }, json=fan_hashes)
    assert r.status_code == 200
    assert r.json()["tagged_count"] == 3
    
    # Vérifier que tous les threads ont le tag
    for fan_hash in fan_hashes:
        thread = mongo_client["chat_threads"].find_one({
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": fan_hash
        })
        assert "premium" in thread["tags"]

def test_remove_tag(test_client: TestClient, mongo_client):
    """Test de suppression de tag."""
    # Seed un thread avec un tag
    mongo_client["chat_threads"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_remove",
        "platform": "instagram",
        "last_message": "test",
        "last_ts": utcnow(),
        "unseen_count": 0,
        "priority": 0,
        "tags": ["vip", "premium"]
    })
    
    # Ajouter le tag dans fan_tags
    mongo_client["fan_tags"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_remove",
        "tag": "vip",
        "created_at": utcnow()
    })
    
    # Test suppression de tag
    r = test_client.delete("/api/talent/fans/tag", json={
        "muse_id": "melissa",
        "user_hash": "fan_remove",
        "tag": "vip"
    })
    assert r.status_code == 200
    
    # Vérifier que le tag a été supprimé
    thread = mongo_client["chat_threads"].find_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_remove"
    })
    assert "vip" not in thread["tags"]
    assert "premium" in thread["tags"]  # L'autre tag doit rester

def test_multiple_notes(test_client: TestClient, mongo_client):
    """Test de plusieurs notes pour un fan."""
    # Seed un thread
    mongo_client["chat_threads"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_notes",
        "platform": "instagram",
        "last_message": "test",
        "last_ts": utcnow(),
        "unseen_count": 0,
        "priority": 0,
        "tags": []
    })
    
    # Ajouter plusieurs notes
    notes_texts = [
        "Première note importante",
        "Deuxième note avec détails",
        "Troisième note de suivi"
    ]
    
    for note_text in notes_texts:
        r = test_client.post("/api/talent/fans/note", json={
            "muse_id": "melissa",
            "user_hash": "fan_notes",
            "text": note_text
        })
        assert r.status_code == 200
    
    # Récupérer toutes les notes
    r = test_client.get("/api/talent/fans/notes", params={
        "muse_id": "melissa",
        "user_hash": "fan_notes"
    })
    assert r.status_code == 200
    notes = r.json()
    assert len(notes) >= 3
    
    # Vérifier que toutes les notes sont présentes
    note_texts_found = [note["text"] for note in notes]
    for note_text in notes_texts:
        assert note_text in note_texts_found

def test_escalation_levels(test_client: TestClient, mongo_client):
    """Test des différents niveaux d'escalade."""
    # Seed un thread
    mongo_client["chat_threads"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_escalate",
        "platform": "instagram",
        "last_message": "urgent",
        "last_ts": utcnow(),
        "unseen_count": 1,
        "priority": 0,
        "tags": []
    })
    
    # Test escalade niveau 1
    r1 = test_client.post("/api/talent/inbox/escalate", params={
        "muse_id": "melissa",
        "user_hash": "fan_escalate",
        "level": 1
    })
    assert r1.status_code == 200
    
    # Vérifier la priorité
    thread = mongo_client["chat_threads"].find_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_escalate"
    })
    assert thread["priority"] >= 1
    
    # Test escalade niveau 3
    r2 = test_client.post("/api/talent/inbox/escalate", params={
        "muse_id": "melissa",
        "user_hash": "fan_escalate",
        "level": 3,
        "reason": "Critical issue"
    })
    assert r2.status_code == 200
    
    # Vérifier que la priorité a été mise à jour
    thread = mongo_client["chat_threads"].find_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "user_hash": "fan_escalate"
    })
    assert thread["priority"] >= 3



