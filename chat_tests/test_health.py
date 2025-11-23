# chat_tests/test_health.py
"""
Tests smoke pour les endpoints de santé et readiness.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from api.main import app


client = TestClient(app)


def test_healthz():
    """Test de l'endpoint /api/healthz."""
    response = client.get("/api/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime_s" in data
    assert "version" in data
    assert "modules" in data
    assert isinstance(data["modules"], dict)


@patch("api.routes.health.get_core_db")
@patch("api.routes.health.get_bi_db")
def test_readyz_success(mock_get_bi_db, mock_get_core_db):
    """Test de l'endpoint /api/readyz avec succès."""
    # Mock des bases de données
    mock_core_db = AsyncMock()
    mock_core_db.command = AsyncMock(return_value={"ok": 1})
    mock_get_core_db.return_value = mock_core_db
    
    mock_bi_db = AsyncMock()
    mock_bi_db.command = AsyncMock(return_value={"ok": 1})
    mock_get_bi_db.return_value = mock_bi_db
    
    # Note: TestClient ne supporte pas async, donc on teste directement la fonction
    from api.routes.health import readyz
    import asyncio
    
    result = asyncio.run(readyz())
    assert result["ready"] is True


def test_root():
    """Test de la route racine."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data




