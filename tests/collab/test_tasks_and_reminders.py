# tests/collab/test_tasks_and_reminders.py
"""
Tests pour les tâches et rappels de collaboration.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone

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


@pytest.fixture
def mock_ws_hub():
    """Mock du hub WebSocket."""
    with patch("api.services.collab.task_service.hub") as mock:
        mock.broadcast = AsyncMock()
        yield mock


@pytest.mark.asyncio
async def test_create_task(mock_ws_hub):
    """Test de création d'une tâche."""
    client = TestClient(app)
    
    payload = {
        "org_id": "org_demo",
        "title": "Tâche de test",
        "description": "Description de la tâche",
        "assignees": ["user1@org.io", "user2@org.io"],
        "status": "todo",
        "priority": "high",
        "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "tags": ["urgent", "client"]
    }
    
    response = client.post("/api/collab/tasks", json=payload)
    
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Tâche de test"
    assert body["status"] == "todo"
    assert body["priority"] == "high"
    assert len(body["assignees"]) == 2
    assert "id" in body
    
    # Vérifier que le broadcast a été appelé
    mock_ws_hub.broadcast.assert_called_once()


@pytest.mark.asyncio
async def test_update_task(mock_ws_hub):
    """Test de mise à jour d'une tâche."""
    client = TestClient(app)
    
    # Créer une tâche
    create_payload = {
        "org_id": "org_demo",
        "title": "Tâche originale",
        "status": "todo"
    }
    create_resp = client.post("/api/collab/tasks", json=create_payload)
    task_id = create_resp.json()["id"]
    
    # Mettre à jour
    update_payload = {
        "status": "in_progress",
        "priority": "urgent"
    }
    
    response = client.patch(f"/api/collab/tasks/{task_id}", json=update_payload)
    
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["priority"] == "urgent"
    
    # Vérifier que le broadcast a été appelé
    mock_ws_hub.broadcast.assert_called()


@pytest.mark.asyncio
async def test_list_tasks():
    """Test de liste des tâches."""
    client = TestClient(app)
    
    # Créer quelques tâches
    for i in range(3):
        payload = {
            "org_id": "org_demo",
            "title": f"Tâche {i}",
            "status": "todo" if i % 2 == 0 else "in_progress"
        }
        client.post("/api/collab/tasks", json=payload)
    
    # Lister toutes
    response = client.get("/api/collab/tasks?org_id=org_demo")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) >= 3
    
    # Filtrer par statut
    response2 = client.get("/api/collab/tasks?org_id=org_demo&status=todo")
    assert response2.status_code == 200
    tasks_todo = response2.json()
    assert all(t["status"] == "todo" for t in tasks_todo)


@pytest.mark.asyncio
async def test_stats():
    """Test des statistiques de collaboration."""
    client = TestClient(app)
    
    org_id = "org_demo"
    
    # Créer des tâches avec différents statuts et priorités
    now = datetime.now(timezone.utc)
    
    tasks = [
        {"org_id": org_id, "title": "T1", "status": "todo", "priority": "high"},
        {"org_id": org_id, "title": "T2", "status": "in_progress", "priority": "medium"},
        {"org_id": org_id, "title": "T3", "status": "done", "priority": "low"},
        {"org_id": org_id, "title": "T4", "status": "todo", "priority": "high", "due_at": (now - timedelta(days=1)).isoformat()},
    ]
    
    for task in tasks:
        client.post("/api/collab/tasks", json=task)
    
    # Récupérer les stats
    response = client.get(f"/api/collab/stats?org_id={org_id}")
    
    assert response.status_code == 200
    stats = response.json()
    assert stats["org_id"] == org_id
    assert stats["open_tasks"] >= 2  # todo + in_progress
    assert stats["overdue_tasks"] >= 1  # T4 en retard
    assert "by_status" in stats
    assert "by_priority" in stats


@pytest.mark.asyncio
async def test_check_overdue_tasks(mongo_client):
    """Test de vérification des tâches en retard."""
    from api.services.collab.reminders import check_overdue_tasks
    from api.databases.databases import get_core_db
    
    db = get_core_db()
    org_id = "org_demo"
    now = datetime.now(timezone.utc)
    
    # Créer une tâche en retard
    overdue_task = {
        "org_id": org_id,
        "title": "Tâche en retard",
        "status": "todo",
        "due_at": now - timedelta(days=1),
        "assignees": ["user@org.io"],
        "priority": "medium",
        "created_by": "test@org.io",
        "created_at": now - timedelta(days=2),
        "updated_at": now - timedelta(days=2)
    }
    await db["collab_tasks"].insert_one(overdue_task)
    
    # Vérifier les tâches en retard
    with patch("api.services.collab.reminders.hub") as mock_hub:
        mock_hub.broadcast = AsyncMock()
        
        count = await check_overdue_tasks()
        
        assert count >= 1
        # Vérifier que le broadcast a été appelé
        mock_hub.broadcast.assert_called()




