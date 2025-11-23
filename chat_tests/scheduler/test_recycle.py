# chat_tests/scheduler/test_recycle.py
"""
Tests d'intégration pour le recyclage de contenu.
"""

from fastapi.testclient import TestClient
from datetime import datetime, timezone

def test_recycle_content(test_client: TestClient, mongo_client):
    """Test de recyclage de contenu."""
    policy = {
        "name": "test_recycle_policy",
        "active": True,
        "selection": "top_by_ctr",
        "lookback_days": 30,
        "max_per_week": 3,
        "reformat": ["twitter", "reddit", "instagram"],
        "filters": {}
    }
    
    r = test_client.post("/api/scheduler/recycle", params={
        "muse_id": "melissa"
    }, json=policy)
    assert r.status_code == 200
    
    b = r.json()
    assert "created" in b
    assert isinstance(b["created"], list)

def test_recycle_policy_management(test_client: TestClient, mongo_client):
    """Test de gestion des politiques de recyclage."""
    policy = {
        "name": "test_policy_management",
        "active": True,
        "selection": "top_by_views",
        "lookback_days": 14,
        "max_per_week": 2,
        "reformat": ["instagram", "twitter"],
        "filters": {"min_views": 100}
    }
    
    # Créer une politique
    r1 = test_client.post("/api/scheduler/recycle/policy", params={
        "muse_id": "melissa"
    }, json=policy)
    assert r1.status_code == 200
    assert "policy_id" in r1.json()
    
    # Récupérer les politiques
    r2 = test_client.get("/api/scheduler/recycle/policies", params={
        "muse_id": "melissa"
    })
    assert r2.status_code == 200
    
    b = r2.json()
    assert "policies" in b
    assert isinstance(b["policies"], list)

def test_recycle_analytics(test_client: TestClient, mongo_client):
    """Test des analytics de recyclage."""
    r = test_client.get("/api/scheduler/recycle/analytics", params={
        "muse_id": "melissa",
        "days": 30
    })
    assert r.status_code == 200
    
    b = r.json()
    assert "total_recycled" in b
    assert "published_recycled" in b
    assert "success_rate" in b
    assert "avg_performance" in b
    assert "period_days" in b

def test_scheduler_status(test_client: TestClient, mongo_client):
    """Test du statut du scheduler."""
    r = test_client.get("/api/scheduler/status")
    assert r.status_code == 200
    
    b = r.json()
    assert "running" in b
    assert "total_jobs" in b
    assert "jobs" in b

def test_publish_history(test_client: TestClient, mongo_client):
    """Test de l'historique des publications."""
    r = test_client.get("/api/scheduler/history", params={
        "muse_id": "melissa",
        "limit": 20
    })
    assert r.status_code == 200
    
    b = r.json()
    assert "history" in b
    assert isinstance(b["history"], list)




