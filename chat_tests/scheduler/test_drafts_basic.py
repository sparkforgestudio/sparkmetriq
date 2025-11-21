# chat_tests/scheduler/test_drafts_basic.py
"""
Tests d'intégration pour les drafts de base.
"""

from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from api.main import app

def test_create_and_list_drafts(test_client: TestClient, mongo_client):
    """Test de création et listing des drafts."""
    client = test_client
    payload = {
        "platform": "instagram",
        "muse_id": "melissa",
        "caption": "Hello IG",
        "scheduled_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        "tone": "flirty",
        "objective": "teasing"
    }
    r = client.post("/api/scheduler/drafts", json=payload)
    assert r.status_code == 200, r.text
    did = r.json()["id"]

    r2 = client.get("/api/scheduler/drafts")
    assert r2.status_code == 200
    assert any(d["id"] == did for d in r2.json())

def test_update_draft(test_client: TestClient, mongo_client):
    """Test de mise à jour d'un draft."""
    client = test_client
    
    # Créer un draft
    payload = {
        "platform": "twitter",
        "muse_id": "melissa",
        "caption": "Original caption",
        "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "tone": "flirty",
        "objective": "teasing"
    }
    r = client.post("/api/scheduler/drafts", json=payload)
    assert r.status_code == 200
    draft_id = r.json()["id"]
    
    # Mettre à jour le draft
    updates = {
        "caption": "Updated caption",
        "tone": "professional"
    }
    r2 = client.put(f"/api/scheduler/drafts/{draft_id}", json=updates)
    assert r2.status_code == 200
    
    # Vérifier la mise à jour
    r3 = client.get(f"/api/scheduler/drafts/{draft_id}")
    assert r3.status_code == 200
    assert r3.json()["caption"] == "Updated caption"
    assert r3.json()["tone"] == "professional"

def test_delete_draft(test_client: TestClient, mongo_client):
    """Test de suppression d'un draft."""
    client = test_client
    
    # Créer un draft
    payload = {
        "platform": "reddit",
        "muse_id": "melissa",
        "caption": "Test post",
        "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "tone": "flirty",
        "objective": "teasing"
    }
    r = client.post("/api/scheduler/drafts", json=payload)
    assert r.status_code == 200
    draft_id = r.json()["id"]
    
    # Supprimer le draft
    r2 = client.delete(f"/api/scheduler/drafts/{draft_id}")
    assert r2.status_code == 200
    assert r2.json()["ok"] == True
    
    # Vérifier que le draft n'existe plus
    r3 = client.get(f"/api/scheduler/drafts/{draft_id}")
    assert r3.status_code == 404



