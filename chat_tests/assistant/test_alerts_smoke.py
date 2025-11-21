# chat_tests/assistant/test_alerts_smoke.py
"""
Tests d'intégration pour les alertes stratégiques.
"""

from fastapi.testclient import TestClient

def test_alerts_smoke(test_client: TestClient, mongo_client):
    """Test de génération d'alertes."""
    # Seed minimal
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa"
    })
    
    # Seed quelques données pour déclencher des alertes
    from datetime import datetime, timedelta
    now = utcnow()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    # Messages récents (plus que la semaine précédente pour déclencher une alerte positive)
    mongo_client["chat_messages"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "timestamp": week_ago,
            "role": "user",
            "text": "Message récent"
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "timestamp": week_ago,
            "role": "user",
            "text": "Autre message récent"
        }
    ])
    
    # Messages anciens (moins pour créer un contraste)
    mongo_client["chat_messages"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "timestamp": two_weeks_ago,
        "role": "user",
        "text": "Message ancien"
    })
    
    # Lancer les alertes
    r = test_client.post("/api/assistant/alerts/run", params={"muse_id": "melissa"})
    assert r.status_code == 200
    
    # Vérifier que des alertes ont été créées
    r2 = test_client.get("/api/assistant/alerts/melissa")
    assert r2.status_code == 200
    
    alerts = r2.json()
    assert isinstance(alerts, list)

def test_alert_acknowledge(test_client: TestClient, mongo_client):
    """Test d'acquittement d'alerte."""
    # Créer une alerte
    mongo_client["ai_alerts"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "kind": "growth_drop",
        "message": "Test alert",
        "severity": "medium",
        "status": "open",
        "ts": utcnow()
    })
    
    # Récupérer les alertes
    r1 = test_client.get("/api/assistant/alerts/melissa")
    assert r1.status_code == 200
    
    alerts = r1.json()
    assert len(alerts) > 0
    
    alert_id = alerts[0]["id"]
    
    # Acquitter l'alerte
    r2 = test_client.post(f"/api/assistant/alerts/{alert_id}/acknowledge")
    assert r2.status_code == 200
    
    # Fermer l'alerte
    r3 = test_client.post(f"/api/assistant/alerts/{alert_id}/close")
    assert r3.status_code == 200

def test_alert_summary(test_client: TestClient, mongo_client):
    """Test du résumé des alertes."""
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa"
    })
    
    # Créer quelques alertes
    from datetime import datetime, timedelta
    now = utcnow()
    
    mongo_client["ai_alerts"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "kind": "growth_drop",
            "message": "Alert 1",
            "severity": "high",
            "status": "open",
            "ts": now
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "kind": "over_perform",
            "message": "Alert 2",
            "severity": "medium",
            "status": "ack",
            "ts": now - timedelta(hours=1)
        }
    ])
    
    r = test_client.get("/api/assistant/alerts/melissa/summary")
    assert r.status_code == 200
    
    summary = r.json()
    assert "total_alerts" in summary
    assert "open_alerts" in summary
    assert "high_severity" in summary



