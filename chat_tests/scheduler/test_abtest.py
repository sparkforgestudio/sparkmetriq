# chat_tests/scheduler/test_abtest.py
"""
Tests d'intégration pour les tests A/B.
"""

from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

def test_create_abtest(test_client: TestClient, mongo_client):
    """Test de création d'un test A/B."""
    start_at = datetime.now(timezone.utc) + timedelta(hours=1)
    end_at = start_at + timedelta(days=7)
    
    payload = {
        "campaign_id": "test_campaign_1",
        "platform": "instagram",
        "muse_id": "melissa",
        "hypothesis": "Test A vs B for engagement",
        "kpi": "engagement",
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "variants": [
            {
                "platform": "instagram",
                "muse_id": "melissa",
                "caption": "Variant A - Original approach",
                "scheduled_at": start_at.isoformat(),
                "tone": "flirty",
                "objective": "engagement"
            },
            {
                "platform": "instagram",
                "muse_id": "melissa",
                "caption": "Variant B - Alternative approach",
                "scheduled_at": (start_at + timedelta(hours=2)).isoformat(),
                "tone": "professional",
                "objective": "engagement"
            }
        ]
    }
    
    r = test_client.post("/api/scheduler/abtest", json=payload)
    assert r.status_code == 200
    assert "id" in r.json()
    assert "draft_ids" in r.json()
    assert len(r.json()["draft_ids"]) == 2

def test_abtest_summary(test_client: TestClient, mongo_client):
    """Test de résumé d'un test A/B."""
    campaign_id = "test_campaign_summary"
    
    # Créer un test A/B d'abord
    start_at = datetime.now(timezone.utc) + timedelta(hours=1)
    end_at = start_at + timedelta(days=7)
    
    payload = {
        "campaign_id": campaign_id,
        "platform": "twitter",
        "muse_id": "melissa",
        "hypothesis": "Test summary",
        "kpi": "engagement",
        "start_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "variants": [
            {
                "platform": "twitter",
                "muse_id": "melissa",
                "caption": "Variant A",
                "scheduled_at": start_at.isoformat(),
                "tone": "flirty",
                "objective": "engagement"
            },
            {
                "platform": "twitter",
                "muse_id": "melissa",
                "caption": "Variant B",
                "scheduled_at": (start_at + timedelta(hours=2)).isoformat(),
                "tone": "professional",
                "objective": "engagement"
            }
        ]
    }
    
    r1 = test_client.post("/api/scheduler/abtest", json=payload)
    assert r1.status_code == 200
    
    # Récupérer le résumé
    r2 = test_client.get(f"/api/scheduler/abtest/{campaign_id}/summary")
    assert r2.status_code == 200
    
    b = r2.json()
    assert "campaign_id" in b
    assert "platform" in b
    assert "kpi" in b

def test_abtest_recommendations(test_client: TestClient, mongo_client):
    """Test de recommandations A/B."""
    r = test_client.get("/api/scheduler/abtest/recommendations", params={
        "muse_id": "melissa",
        "platform": "instagram"
    })
    assert r.status_code == 200
    
    b = r.json()
    assert "recommendations" in b
    assert isinstance(b["recommendations"], list)

def test_auto_abtest(test_client: TestClient, mongo_client):
    """Test de création automatique d'un test A/B."""
    r = test_client.post("/api/scheduler/abtest/auto", params={
        "muse_id": "melissa",
        "platform": "instagram",
        "recommendation_type": "first_test"
    })
    assert r.status_code == 200
    
    b = r.json()
    assert "id" in b
    assert "draft_ids" in b



