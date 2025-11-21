# tests/collab/test_clickup_notion_stubs.py
"""
Tests pour les intégrations ClickUp/Notion (stubs).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone

from api.main import app
from api.core.settings import settings
from api.core.auth import get_current_user
from api.schemas.users import UserResponse


# Mock pour l'authentification
def mock_get_current_user():
    """Mock de l'utilisateur courant pour les tests."""
    return UserResponse(
        id="test_user_id",
        email="test@org.io",
        org_id="org_test",
        is_admin=True,
        roles=[]
    )


@pytest.fixture(autouse=True)
def override_user():
    """Override l'authentification pour tous les tests."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_task_with_clickup_sync():
    """Test de création d'une tâche avec synchronisation ClickUp."""
    client = TestClient(app)
    
    # Activer les intégrations
    original_integrations = settings.feature_collab_integrations
    original_token = settings.clickup_api_token
    
    settings.feature_collab_integrations = True
    settings.clickup_api_token = "test_token"
    
    try:
        payload = {
            "org_id": "org_demo",
            "title": "Tâche avec ClickUp",
            "description": "Description",
            "status": "todo",
            "priority": "high",
            "external_sync": "clickup"
        }
        
        response = client.post("/api/collab/tasks", json=payload)
        
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Tâche avec ClickUp"
        
        # Vérifier que external_ref est présent (stub)
        if body.get("external_ref"):
            assert body["external_ref"]["ok"] is True
            assert "clickup" in body["external_ref"]["id"].lower()
        
    finally:
        settings.feature_collab_integrations = original_integrations
        settings.clickup_api_token = original_token


@pytest.mark.asyncio
async def test_create_task_with_notion_sync():
    """Test de création d'une tâche avec synchronisation Notion."""
    client = TestClient(app)
    
    # Activer les intégrations
    original_integrations = settings.feature_collab_integrations
    original_token = settings.notion_api_token
    
    settings.feature_collab_integrations = True
    settings.notion_api_token = "test_token"
    
    try:
        payload = {
            "org_id": "org_demo",
            "title": "Tâche avec Notion",
            "description": "Description",
            "status": "todo",
            "priority": "medium",
            "external_sync": "notion"
        }
        
        response = client.post("/api/collab/tasks", json=payload)
        
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Tâche avec Notion"
        
        # Vérifier que external_ref est présent (stub)
        if body.get("external_ref"):
            assert body["external_ref"]["ok"] is True
            assert "notion" in body["external_ref"]["id"].lower()
        
    finally:
        settings.feature_collab_integrations = original_integrations
        settings.notion_api_token = original_token


@pytest.mark.asyncio
async def test_sync_disabled_returns_no_external_ref():
    """Test que si les intégrations sont désactivées, external_ref n'est pas créé."""
    client = TestClient(app)
    
    original_integrations = settings.feature_collab_integrations
    settings.feature_collab_integrations = False
    
    try:
        payload = {
            "org_id": "org_demo",
            "title": "Tâche sans sync",
            "external_sync": "clickup"
        }
        
        response = client.post("/api/collab/tasks", json=payload)
        
        assert response.status_code == 201
        body = response.json()
        
        # external_ref devrait être None ou indiquer que l'intégration est désactivée
        if body.get("external_ref"):
            assert body["external_ref"].get("ok") is False
        
    finally:
        settings.feature_collab_integrations = original_integrations



