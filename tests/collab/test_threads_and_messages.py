# tests/collab/test_threads_and_messages.py
"""
Tests pour les threads et messages de collaboration.
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


@pytest.fixture
def mock_ws_hub():
    """Mock du hub WebSocket."""
    with patch("api.services.collab.chat_service.hub") as mock:
        mock.broadcast = AsyncMock()
        yield mock


@pytest.mark.asyncio
async def test_create_thread():
    """Test de création d'un thread."""
    client = TestClient(app)
    
    payload = {
        "org_id": "org_demo",
        "title": "Thread de test",
        "muse_id": "muse_1",
        "tags": ["urgent", "support"]
    }
    
    response = client.post("/api/collab/threads", json=payload)
    
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Thread de test"
    assert body["org_id"] == "org_demo"
    assert "id" in body


@pytest.mark.asyncio
async def test_post_message(mock_ws_hub):
    """Test de post d'un message dans un thread."""
    client = TestClient(app)
    
    # Créer un thread d'abord
    thread_payload = {
        "org_id": "org_demo",
        "title": "Thread test"
    }
    thread_resp = client.post("/api/collab/threads", json=thread_payload)
    assert thread_resp.status_code == 201
    thread_id = thread_resp.json()["id"]
    
    # Poster un message
    msg_payload = {
        "thread_id": thread_id,
        "body": "Hello team! @test@org.io",
        "mentions": ["test@org.io"],
        "attachments": ["https://example.com/file.pdf"]
    }
    
    response = client.post("/api/collab/messages", json=msg_payload)
    
    assert response.status_code == 201
    body = response.json()
    assert body["body"] == "Hello team! @test@org.io"
    assert "test@org.io" in body["mentions"]
    assert thread_id == body["thread_id"]
    
    # Vérifier que le broadcast a été appelé
    mock_ws_hub.broadcast.assert_called_once()


@pytest.mark.asyncio
async def test_list_threads():
    """Test de liste des threads."""
    client = TestClient(app)
    
    # Créer quelques threads
    for i in range(3):
        payload = {
            "org_id": "org_demo",
            "title": f"Thread {i}"
        }
        client.post("/api/collab/threads", json=payload)
    
    # Lister
    response = client.get("/api/collab/threads?org_id=org_demo")
    
    assert response.status_code == 200
    threads = response.json()
    assert len(threads) >= 3
    assert all("title" in t for t in threads)


@pytest.mark.asyncio
async def test_list_messages():
    """Test de liste des messages d'un thread."""
    client = TestClient(app)
    
    # Créer thread et messages
    thread_resp = client.post("/api/collab/threads", json={
        "org_id": "org_demo",
        "title": "Thread test"
    })
    thread_id = thread_resp.json()["id"]
    
    for i in range(3):
        client.post("/api/collab/messages", json={
            "thread_id": thread_id,
            "body": f"Message {i}"
        })
    
    # Lister les messages
    response = client.get(f"/api/collab/messages?org_id=org_demo&thread_id={thread_id}")
    
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 3
    assert all("body" in m for m in messages)


@pytest.mark.asyncio
async def test_feature_disabled():
    """Test que la collaboration retourne 403 si désactivée."""
    original_value = settings.feature_collab_enabled
    settings.feature_collab_enabled = False
    
    try:
        client = TestClient(app)
        
        payload = {
            "org_id": "org_demo",
            "title": "Test"
        }
        
        response = client.post("/api/collab/threads", json=payload)
        assert response.status_code == 403
        
    finally:
        settings.feature_collab_enabled = original_value




