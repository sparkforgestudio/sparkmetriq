# chat_tests/analytics/test_bi_basic.py
"""
Tests d'intégration pour les analytics BI (funnel et revenus).
"""

from fastapi.testclient import TestClient

def test_bi_funnel_revenue_smoke(test_client: TestClient, mongo_client):
    db = mongo_client
    db["events_funnel"].insert_many([
        {"tenant_id":"user_123","muse_id":"m1","phase":"contact","source":"tg","ts":"2025-01-02T12:00:00"},
        {"tenant_id":"user_123","muse_id":"m1","phase":"lead","source":"tg","ts":"2025-01-02T12:05:00"},
        {"tenant_id":"user_123","muse_id":"m1","phase":"subscriber","source":"tg","ts":"2025-01-03T10:00:00"},
        {"tenant_id":"user_123","muse_id":"m1","phase":"payer","source":"tg","ts":"2025-01-03T10:10:00"},
    ])
    db["payments"].insert_many([
        {"tenant_id":"user_123","muse_id":"m1","user_hash":"u1","status":"confirmed","amount":10.0,"ts":"2025-01-03T10:10:00"},
        {"tenant_id":"user_123","muse_id":"m1","user_hash":"u2","status":"confirmed","amount":15.0,"ts":"2025-01-04T11:00:00"},
    ])

    r1 = test_client.get("/api/analytics/bi/funnel", params={"date_from":"2024-01-01T00:00:00","date_to":"2030-01-01T00:00:00","muse_id":"m1"})
    assert r1.status_code == 200
    r2 = test_client.get("/api/analytics/bi/revenue", params={"date_from":"2024-01-01T00:00:00","date_to":"2030-01-01T00:00:00","muse_id":"m1"})
    assert r2.status_code == 200
