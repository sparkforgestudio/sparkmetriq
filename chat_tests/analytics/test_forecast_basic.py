# chat_tests/analytics/test_forecast_basic.py
"""
Tests d'intégration pour les prévisions (forecasts).
"""

from fastapi.testclient import TestClient

def test_forecast_smoke(test_client: TestClient, mongo_client):
    r1 = test_client.get("/api/analytics/bi/forecast/messages", params={"date_from":"2024-01-01T00:00:00","date_to":"2030-01-01T00:00:00","horizon":7})
    assert r1.status_code == 200
    r2 = test_client.get("/api/analytics/bi/forecast/gmv", params={"date_from":"2024-01-01T00:00:00","date_to":"2030-01-01T00:00:00","horizon":7})
    assert r2.status_code == 200
