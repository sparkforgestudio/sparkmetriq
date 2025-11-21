# chat_tests/scheduler/test_weekly_plan.py
"""
Tests d'intégration pour le plan hebdomadaire.
"""

from fastapi.testclient import TestClient
from datetime import datetime, timezone

def test_weekly_plan(test_client: TestClient, mongo_client):
    """Test de création du plan hebdomadaire."""
    r = test_client.post("/api/scheduler/weekly_plan", params={
        "muse_id": "melissa",
        "start_day": datetime.now(timezone.utc).isoformat(),
        "tone": "flirty",
        "objective": "teasing"
    })
    assert r.status_code == 200
    assert len(r.json()["created"]) >= 1

def test_weekly_plan_different_tones(test_client: TestClient, mongo_client):
    """Test de plan hebdomadaire avec différents tons."""
    tones = ["flirty", "professional", "energetic"]
    
    for tone in tones:
        r = test_client.post("/api/scheduler/weekly_plan", params={
            "muse_id": "melissa",
            "start_day": datetime.now(timezone.utc).isoformat(),
            "tone": tone,
            "objective": "engagement"
        })
        assert r.status_code == 200, f"Failed for tone {tone}"
        assert len(r.json()["created"]) >= 1

def test_optimal_times(test_client: TestClient, mongo_client):
    """Test de récupération des heures optimales."""
    platforms = ["instagram", "twitter", "reddit", "tiktok"]
    
    for platform in platforms:
        r = test_client.get(f"/api/scheduler/optimal_times/{platform}", params={
            "muse_id": "melissa"
        })
        assert r.status_code == 200, f"Failed for platform {platform}"
        
        b = r.json()
        assert "platform" in b
        assert "optimal_times" in b
        assert len(b["optimal_times"]) > 0

def test_content_calendar(test_client: TestClient, mongo_client):
    """Test de récupération du calendrier de contenu."""
    start_date = datetime.now(timezone.utc)
    end_date = start_date.replace(hour=23, minute=59, second=59)
    
    r = test_client.get("/api/scheduler/calendar", params={
        "muse_id": "melissa",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    })
    assert r.status_code == 200
    
    b = r.json()
    assert isinstance(b, dict)



