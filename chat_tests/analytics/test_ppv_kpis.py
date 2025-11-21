# chat_tests/analytics/test_ppv_kpis.py
"""
Tests d'intégration pour les KPIs PPV.
"""

from fastapi.testclient import TestClient
from datetime import datetime

def test_ppv_kpis_smoke(test_client: TestClient, mongo_client):
    db = mongo_client
    now = utcnow().isoformat()

    db["ppv_logs"].insert_many([
        {"tenant_id":"user_123","muse_id":"m1","platform":"instagram","status":"sent","price":15.0,"ts":now},
        {"tenant_id":"user_123","muse_id":"m1","platform":"instagram","status":"clicked","price":15.0,"ts":now},
        {"tenant_id":"user_123","muse_id":"m1","platform":"instagram","status":"paid","price":15.0,"ts":now},
    ])

    r = test_client.get("/api/analytics/bi/ppv", params={"date_from":"2024-01-01T00:00:00","date_to":"2030-01-01T00:00:00","muse_id":"m1"})
    assert r.status_code == 200
    b = r.json()
    assert b["sent"] >= 1 and b["paid"] >= 1



