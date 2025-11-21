# chat_tests/talent/test_dashboard_smoke.py
"""
Tests d'intégration pour le dashboard multi-muse.
"""

from fastapi.testclient import TestClient
from datetime import datetime, timedelta

def test_dashboard_smoke(test_client: TestClient, mongo_client):
    """Test de base du dashboard."""
    # Seed des muses
    mongo_client["muses"].insert_many([
        {"tenant_id": "user_123", "muse_id": "melissa"},
        {"tenant_id": "user_123", "muse_id": "sophia"}
    ])
    
    r = test_client.get("/api/talent/dashboard")
    assert r.status_code == 200
    dashboard = r.json()
    assert isinstance(dashboard, list)
    assert len(dashboard) >= 2

def test_dashboard_with_metrics(test_client: TestClient, mongo_client):
    """Test du dashboard avec des métriques."""
    # Seed des muses
    mongo_client["muses"].insert_many([
        {"tenant_id": "user_123", "muse_id": "melissa"},
        {"tenant_id": "user_123", "muse_id": "sophia"}
    ])
    
    # Seed des données de performance
    now = utcnow()
    week_ago = now - timedelta(days=7)
    
    # Messages récents
    mongo_client["chat_messages"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "role": "user",
            "text": "Hello",
            "timestamp": week_ago
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "role": "bot",
            "text": "Hi there!",
            "timestamp": week_ago
        },
        {
            "tenant_id": "user_123",
            "muse_id": "sophia",
            "role": "user",
            "text": "How are you?",
            "timestamp": week_ago
        }
    ])
    
    # Paiements récents
    mongo_client["payments"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "status": "confirmed",
            "amount": 25.0,
            "ts": week_ago
        },
        {
            "tenant_id": "user_123",
            "muse_id": "sophia",
            "status": "confirmed",
            "amount": 15.0,
            "ts": week_ago
        }
    ])
    
    r = test_client.get("/api/talent/dashboard")
    assert r.status_code == 200
    dashboard = r.json()
    
    # Vérifier que les métriques sont calculées
    for muse_data in dashboard:
        assert "muse_id" in muse_data
        assert "revenue_7d" in muse_data
        assert "replies_rate_7d" in muse_data
        assert "ppv_conv_rate_7d" in muse_data
        assert "growth_msgs_7d" in muse_data
        assert "status" in muse_data

def test_agency_overview(test_client: TestClient, mongo_client):
    """Test de la vue d'ensemble de l'agence."""
    # Seed des données d'agence
    mongo_client["muses"].insert_many([
        {"tenant_id": "user_123", "muse_id": "melissa"},
        {"tenant_id": "user_123", "muse_id": "sophia"},
        {"tenant_id": "user_123", "muse_id": "luna"}
    ])
    
    mongo_client["operator_roles"].insert_many([
        {"tenant_id": "user_123", "user_id": "op_1", "role": "operator"},
        {"tenant_id": "user_123", "user_id": "op_2", "role": "supervisor"}
    ])
    
    # Seed des threads
    mongo_client["chat_threads"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": "fan_1",
            "platform": "instagram",
            "priority": 0,
            "unseen_count": 1
        },
        {
            "tenant_id": "user_123",
            "muse_id": "sophia",
            "user_hash": "fan_2",
            "platform": "twitter",
            "priority": 2,
            "unseen_count": 0
        }
    ])
    
    r = test_client.get("/api/talent/dashboard/agency")
    assert r.status_code == 200
    overview = r.json()
    
    assert "total_muses" in overview
    assert "active_operators" in overview
    assert "total_revenue_7d" in overview
    assert "avg_response_rate" in overview
    assert "total_threads" in overview
    assert "escalated_threads" in overview
    
    # Vérifier les valeurs
    assert overview["total_muses"] >= 3
    assert overview["active_operators"] >= 2
    assert overview["total_threads"] >= 2
    assert overview["escalated_threads"] >= 1

def test_muse_detailed_metrics(test_client: TestClient, mongo_client):
    """Test des métriques détaillées d'une muse."""
    # Seed une muse
    mongo_client["muses"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "niches": ["cosplay"]
    })
    
    # Seed des données détaillées
    now = utcnow()
    month_ago = now - timedelta(days=30)
    
    # Messages par plateforme
    mongo_client["chat_messages"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "platform": "instagram",
            "role": "user",
            "text": "Hello",
            "timestamp": month_ago
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "platform": "instagram",
            "role": "bot",
            "text": "Hi!",
            "timestamp": month_ago
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "platform": "twitter",
            "role": "user",
            "text": "Tweet",
            "timestamp": month_ago
        }
    ])
    
    # Revenus quotidiens
    for i in range(5):
        day = month_ago + timedelta(days=i)
        mongo_client["payments"].insert_one({
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "status": "confirmed",
            "amount": 10.0 + i * 5,
            "ts": day
        })
    
    # Threads
    mongo_client["chat_threads"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": "fan_1",
            "platform": "instagram",
            "unseen_count": 1,
            "priority": 0,
            "tags": ["vip"]
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": "fan_2",
            "platform": "twitter",
            "unseen_count": 0,
            "priority": 1,
            "tags": []
        }
    ])
    
    r = test_client.get("/api/talent/dashboard/muse/melissa", params={"days": 30})
    assert r.status_code == 200
    metrics = r.json()
    
    assert "summary" in metrics
    assert "platform_metrics" in metrics
    assert "daily_revenue" in metrics
    assert "thread_stats" in metrics
    assert "period_days" in metrics
    
    # Vérifier les métriques de plateforme
    platform_metrics = metrics["platform_metrics"]
    assert len(platform_metrics) >= 2
    
    # Vérifier les revenus quotidiens
    daily_revenue = metrics["daily_revenue"]
    assert len(daily_revenue) >= 5
    
    # Vérifier les statistiques de threads
    thread_stats = metrics["thread_stats"]
    assert thread_stats["total_threads"] >= 2
    assert thread_stats["unseen_threads"] >= 1
    assert thread_stats["escalated_threads"] >= 1
    assert thread_stats["vip_threads"] >= 1

def test_segment_metrics(test_client: TestClient, mongo_client):
    """Test des métriques par segment."""
    # Seed des muses avec différents segments
    mongo_client["muses"].insert_many([
        {"tenant_id": "user_123", "muse_id": "melissa", "niches": ["cosplay"]},
        {"tenant_id": "user_123", "muse_id": "sophia", "niches": ["cosplay"]},
        {"tenant_id": "user_123", "muse_id": "luna", "niches": ["fitness"]}
    ])
    
    # Seed des données pour le segment cosplay
    now = utcnow()
    month_ago = now - timedelta(days=30)
    
    # Messages pour les muses cosplay
    mongo_client["chat_messages"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "role": "user",
            "text": "Cosplay message 1",
            "timestamp": month_ago
        },
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "role": "bot",
            "text": "Cosplay reply 1",
            "timestamp": month_ago
        },
        {
            "tenant_id": "user_123",
            "muse_id": "sophia",
            "role": "user",
            "text": "Cosplay message 2",
            "timestamp": month_ago
        }
    ])
    
    # Paiements pour les muses cosplay
    mongo_client["payments"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "status": "confirmed",
            "amount": 30.0,
            "ts": month_ago
        },
        {
            "tenant_id": "user_123",
            "muse_id": "sophia",
            "status": "confirmed",
            "amount": 20.0,
            "ts": month_ago
        }
    ])
    
    r = test_client.get("/api/talent/dashboard/segment", params={"segment": "cosplay"})
    assert r.status_code == 200
    segment_metrics = r.json()
    
    assert "segment" in segment_metrics
    assert "total_muses" in segment_metrics
    assert "total_revenue" in segment_metrics
    assert "avg_revenue_per_muse" in segment_metrics
    assert "total_messages" in segment_metrics
    assert "avg_response_rate" in segment_metrics
    
    # Vérifier les valeurs
    assert segment_metrics["segment"] == "cosplay"
    assert segment_metrics["total_muses"] >= 2
    assert segment_metrics["total_revenue"] >= 50.0
    assert segment_metrics["total_messages"] >= 3

def test_operator_performance(test_client: TestClient, mongo_client):
    """Test des performances d'un opérateur."""
    # Seed des assignations
    mongo_client["muse_assignments"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "platform": "instagram",
            "operator_id": "op_perf",
            "created_at": utcnow()
        },
        {
            "tenant_id": "user_123",
            "muse_id": "sophia",
            "platform": "twitter",
            "operator_id": "op_perf",
            "created_at": utcnow()
        }
    ])
    
    # Seed des threads actifs
    mongo_client["chat_threads"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "user_hash": "fan_1",
            "platform": "instagram",
            "unseen_count": 1,
            "priority": 0,
            "tags": []
        },
        {
            "tenant_id": "user_123",
            "muse_id": "sophia",
            "user_hash": "fan_2",
            "platform": "twitter",
            "unseen_count": 0,
            "priority": 0,
            "tags": []
        }
    ])
    
    # Seed des messages de l'opérateur
    now = utcnow()
    week_ago = now - timedelta(days=7)
    
    mongo_client["chat_messages"].insert_many([
        {
            "tenant_id": "user_123",
            "muse_id": "melissa",
            "role": "operator",
            "user_id": "op_perf",
            "text": "Operator reply 1",
            "timestamp": week_ago
        },
        {
            "tenant_id": "user_123",
            "muse_id": "sophia",
            "role": "operator",
            "user_id": "op_perf",
            "text": "Operator reply 2",
            "timestamp": week_ago
        }
    ])
    
    r = test_client.get("/api/talent/dashboard/operator/op_perf")
    assert r.status_code == 200
    performance = r.json()
    
    assert "operator_id" in performance
    assert "assigned_muses" in performance
    assert "total_threads" in performance
    assert "active_threads" in performance
    assert "replies_today" in performance
    assert "avg_response_time" in performance
    assert "performance_score" in performance
    
    # Vérifier les valeurs
    assert performance["operator_id"] == "op_perf"
    assert len(performance["assigned_muses"]) >= 2
    assert performance["replies_today"] >= 2
    assert performance["active_threads"] >= 1



