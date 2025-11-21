# chat_tests/analytics/test_conv_kpis.py
"""
Tests d'intégration pour les KPIs conversationnels.
"""

from fastapi.testclient import TestClient
from api.main import app

def test_conv_kpis_smoke(test_client: TestClient, mongo_client):
    client = test_client
    send_url = app.url_path_for("chat_send")

    r1 = client.post(send_url, json={"message": "Salut"})
    assert r1.status_code == 200
    conv_id = r1.json()["conversation_id"]
    r2 = client.post(send_url, json={"conversation_id": conv_id, "message": "Encore moi"})
    assert r2.status_code == 200

    resp = client.get("/api/analytics/conversations/kpis", params={
        "date_from":"2024-01-01T00:00:00","date_to":"2030-01-01T00:00:00"
    })
    assert resp.status_code == 200, resp.text
    b = resp.json()
    assert b["kpis"]["messages"] >= 2
