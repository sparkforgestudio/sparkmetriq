# chat_tests/assistant/test_plan_smoke.py
"""
Tests d'intégration pour les plans d'action mensuels.
"""

from fastapi.testclient import TestClient
from datetime import datetime

def test_plan_smoke(test_client: TestClient, mongo_client):
    """Test de génération de plan mensuel."""
    # Seed muse
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "persona": {"tone": "flirty"},
        "niches": ["cosplay", "elf"]
    })
    
    payload = {
        "muse_id": "melissa",
        "month": "2025-11",
        "goals": [{"name": "New subscribers", "target_value": 50, "unit": "subs"}],
        "preferences": {"tone": "flirty"},
    }
    
    r = test_client.post("/api/assistant/plan", json=payload)
    assert r.status_code == 200, r.text
    
    j = r.json()
    assert j["muse_id"] == "melissa"
    assert isinstance(j["actions"], list)
    assert isinstance(j["goals"], list)
    assert isinstance(j["insights"], list)

def test_get_plan(test_client: TestClient, mongo_client):
    """Test de récupération de plan existant."""
    # Créer un plan d'abord
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "persona": {"tone": "flirty"},
        "niches": ["cosplay"]
    })
    
    payload = {
        "muse_id": "melissa",
        "month": "2025-11",
        "goals": [{"name": "Test goal", "target_value": 25, "unit": "subs"}],
        "preferences": {"tone": "flirty"},
    }
    
    r1 = test_client.post("/api/assistant/plan", json=payload)
    assert r1.status_code == 200
    
    # Récupérer le plan
    r2 = test_client.get("/api/assistant/plan/melissa/2025-11")
    assert r2.status_code == 200
    
    j = r2.json()
    assert j["muse_id"] == "melissa"
    assert j["month"] == "2025-11"

def test_plan_history(test_client: TestClient, mongo_client):
    """Test de l'historique des plans."""
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "persona": {"tone": "flirty"},
        "niches": ["cosplay"]
    })
    
    # Créer plusieurs plans
    for month in ["2025-10", "2025-11"]:
        payload = {
            "muse_id": "melissa",
            "month": month,
            "goals": [{"name": f"Goal {month}", "target_value": 30, "unit": "subs"}],
            "preferences": {"tone": "flirty"},
        }
        r = test_client.post("/api/assistant/plan", json=payload)
        assert r.status_code == 200
    
    # Récupérer l'historique
    r = test_client.get("/api/assistant/plan/history/melissa", params={"limit": 5})
    assert r.status_code == 200
    
    history = r.json()
    assert isinstance(history, list)
    assert len(history) >= 2



