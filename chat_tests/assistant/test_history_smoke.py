# chat_tests/assistant/test_history_smoke.py
"""
Tests d'intégration pour l'historique des recommandations.
"""

from fastapi.testclient import TestClient
from datetime import datetime

def test_history_smoke(test_client: TestClient, mongo_client):
    """Test de l'historique des recommandations."""
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "niches": ["cosplay"]
    })
    
    # Ajouter une recommandation
    r1 = test_client.post("/api/assistant/history", params={
        "muse_id": "melissa",
        "text": "Test recommendation",
        "plan_month": "2025-11"
    })
    assert r1.status_code == 200
    
    reco_id = r1.json()["id"]
    assert reco_id is not None
    
    # Mettre à jour le feedback
    r2 = test_client.post(f"/api/assistant/history/{reco_id}/feedback", params={
        "applied": True,
        "feedback": "useful"
    })
    assert r2.status_code == 200
    
    # Récupérer l'historique
    r3 = test_client.get("/api/assistant/history/melissa", params={"limit": 10})
    assert r3.status_code == 200
    
    history = r3.json()
    assert isinstance(history, list)
    assert len(history) >= 1
    
    # Vérifier que la recommandation a été mise à jour
    reco = history[0]
    assert reco["recommendation"] == "Test recommendation"
    assert reco["applied"] == True
    assert reco["feedback"] == "useful"

def test_history_stats(test_client: TestClient, mongo_client):
    """Test des statistiques de l'historique."""
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "niches": ["cosplay"]
    })
    
    # Créer plusieurs recommandations avec différents statuts
    from datetime import datetime, timedelta
    now = utcnow()
    
    mongo_client["ai_reco_history"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "recommendation": "Reco 1",
            "applied": True,
            "feedback": "useful",
            "ts": now
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "recommendation": "Reco 2",
            "applied": False,
            "feedback": "not_useful",
            "ts": now - timedelta(hours=1)
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "recommendation": "Reco 3",
            "applied": True,
            "feedback": "useful",
            "ts": now - timedelta(hours=2)
        }
    ])
    
    r = test_client.get("/api/assistant/history/melissa/stats", params={"days": 30})
    assert r.status_code == 200
    
    stats = r.json()
    assert "total_recommendations" in stats
    assert "applied_recommendations" in stats
    assert "application_rate" in stats
    assert "feedback_summary" in stats
    
    assert stats["total_recommendations"] >= 3
    assert stats["applied_recommendations"] >= 2
    assert stats["application_rate"] > 0

def test_dashboard(test_client: TestClient, mongo_client):
    """Test du tableau de bord de l'assistant."""
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "niches": ["cosplay"]
    })
    
    # Créer quelques données pour le dashboard
    from datetime import datetime
    
    # Plan d'action
    mongo_client["ai_action_plans"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "month": "2025-11",
        "goals": [{"name": "Test goal", "target_value": 50, "unit": "subs"}],
        "actions": [{"title": "Test action", "description": "Test desc"}],
        "insights": ["Test insight"],
        "created_at": utcnow(),
        "version": 1
    })
    
    # Alerte
    mongo_client["ai_alerts"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "kind": "growth_drop",
        "message": "Test alert",
        "severity": "medium",
        "status": "open",
        "ts": utcnow()
    })
    
    # Recommandation
    mongo_client["ai_reco_history"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "recommendation": "Test recommendation",
        "applied": True,
        "feedback": "useful",
        "ts": utcnow()
    })
    
    r = test_client.get("/api/assistant/dashboard/melissa")
    assert r.status_code == 200
    
    dashboard = r.json()
    assert "recent_plan" in dashboard
    assert "recent_alerts" in dashboard
    assert "recent_collabs" in dashboard
    assert "recent_trends" in dashboard
    assert "recommendation_stats" in dashboard
    assert "last_updated" in dashboard




