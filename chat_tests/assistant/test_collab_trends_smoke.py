# chat_tests/assistant/test_collab_trends_smoke.py
"""
Tests d'intégration pour les collaborations et tendances.
"""

from fastapi.testclient import TestClient

def test_collab_trends_smoke(test_client: TestClient, mongo_client):
    """Test des suggestions de collaboration et tendances."""
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "niches": ["cosplay"]
    })
    
    # Test des suggestions de collaboration
    r1 = test_client.get("/api/assistant/collabs/melissa")
    assert r1.status_code == 200
    
    collab = r1.json()
    assert "profiles" in collab
    assert "outreach_template" in collab
    assert isinstance(collab["profiles"], list)
    
    # Test des tendances
    r2 = test_client.get("/api/assistant/trends/melissa")
    assert r2.status_code == 200
    
    trends = r2.json()
    assert isinstance(trends, list)

def test_collab_ideas(test_client: TestClient, mongo_client):
    """Test de génération d'idées de collaboration."""
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "niches": ["cosplay"]
    })
    
    r = test_client.get("/api/assistant/collabs/ideas/melissa", params={"niche": "cosplay"})
    assert r.status_code == 200
    
    ideas = r.json()
    assert "ideas" in ideas
    assert isinstance(ideas["ideas"], list)
    assert len(ideas["ideas"]) > 0

def test_trend_insights(test_client: TestClient, mongo_client):
    """Test des insights sur les tendances."""
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "niches": ["cosplay", "fitness"]
    })
    
    r = test_client.get("/api/assistant/trends/melissa/insights")
    assert r.status_code == 200
    
    insights = r.json()
    assert "insights" in insights
    assert "recommendations" in insights
    assert "trend_count" in insights
    assert isinstance(insights["insights"], list)
    assert isinstance(insights["recommendations"], list)

def test_collab_history(test_client: TestClient, mongo_client):
    """Test de l'historique des collaborations."""
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "niches": ["cosplay"]
    })
    
    # Créer quelques suggestions de collaboration
    from datetime import datetime
    mongo_client["ai_collab_suggestions"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "profiles": [{"handle": "test1", "platform": "instagram", "similarity": 0.8}],
            "outreach_template": "Test template 1",
            "ts": utcnow()
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "profiles": [{"handle": "test2", "platform": "twitter", "similarity": 0.7}],
            "outreach_template": "Test template 2",
            "ts": utcnow()
        }
    ])
    
    r = test_client.get("/api/assistant/collabs/history/melissa", params={"limit": 5})
    assert r.status_code == 200
    
    history = r.json()
    assert isinstance(history, list)
    assert len(history) >= 2




