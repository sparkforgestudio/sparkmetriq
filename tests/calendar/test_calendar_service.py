# tests/calendar/test_calendar_service.py
"""
Tests pour le service Calendar.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from api.main import app
from api.core.auth import get_current_user
from api.schemas.users import UserResponse


# Mock pour l'authentification
def mock_get_current_user():
    """Mock de l'utilisateur courant pour les tests."""
    return UserResponse(
        id="test_user_id",
        email="test@org.io",
        org_id="org_demo",
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
async def test_create_scheduled_post(mongo_client):
    """Test de création d'un post programmé."""
    client = TestClient(app)
    
    org_id = "org_demo"
    now = datetime.now(timezone.utc)
    start_at = (now + timedelta(days=1)).isoformat()
    
    payload = {
        "org_id": org_id,
        "muse_id": "muse_demo",
        "platform": "instagram",
        "status": "scheduled",
        "visibility": "public",
        "content_ref": {
            "text": "Test post caption"
        },
        "schedule": {
            "start_at_utc": start_at,
            "tz": "Europe/Paris"
        },
        "labels": ["test"]
    }
    
    resp = client.post("/api/calendar/schedule", json=payload)
    
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert "id" in body


@pytest.mark.asyncio
async def test_query_calendar(mongo_client):
    """Test de requête du calendrier."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    db = get_core_db()
    
    org_id = "org_demo"
    now = datetime.now(timezone.utc)
    start_at = (now + timedelta(days=1)).isoformat()
    end_at = (now + timedelta(days=7)).isoformat()
    
    # Seed un post
    await db["scheduled_posts"].insert_one({
        "org_id": org_id,
        "muse_id": "muse_demo",
        "platform": "instagram",
        "status": "scheduled",
        "content_ref": {"text": "Test post"},
        "schedule": {
            "start_at_utc": start_at,
            "tz": "Europe/Paris"
        },
        "labels": ["test"]
    })
    
    # Requête
    resp = client.get(
        "/api/calendar/items",
        params={
            "org_id": org_id,
            "from_utc": start_at,
            "to_utc": end_at
        }
    )
    
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert len(body["items"]) >= 1


@pytest.mark.asyncio
async def test_reschedule_post(mongo_client):
    """Test de reprogrammation d'un post."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    from bson import ObjectId
    
    db = get_core_db()
    org_id = "org_demo"
    
    now = datetime.now(timezone.utc)
    original_start = (now + timedelta(days=1)).isoformat()
    new_start = (now + timedelta(days=2)).isoformat()
    
    # Créer un post
    result = await db["scheduled_posts"].insert_one({
        "org_id": org_id,
        "muse_id": "muse_demo",
        "platform": "instagram",
        "status": "scheduled",
        "content_ref": {"text": "Test post"},
        "schedule": {
            "start_at_utc": original_start,
            "tz": "Europe/Paris"
        }
    })
    
    post_id = str(result.inserted_id)
    
    # Reprogrammer
    resp = client.post(
        "/api/calendar/reschedule",
        json={
            "id": post_id,
            "new_start_at_utc": new_start
        }
    )
    
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    
    # Vérifier la mise à jour
    post = await db["scheduled_posts"].find_one({"_id": ObjectId(post_id)})
    assert post["schedule"]["start_at_utc"] == new_start


@pytest.mark.asyncio
async def test_duplicate_post(mongo_client):
    """Test de duplication d'un post."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    from bson import ObjectId
    
    db = get_core_db()
    org_id = "org_demo"
    
    now = datetime.now(timezone.utc)
    original_start = (now + timedelta(days=1)).isoformat()
    new_start = (now + timedelta(days=3)).isoformat()
    
    # Créer un post
    result = await db["scheduled_posts"].insert_one({
        "org_id": org_id,
        "muse_id": "muse_demo",
        "platform": "instagram",
        "status": "scheduled",
        "content_ref": {"text": "Test post"},
        "schedule": {
            "start_at_utc": original_start,
            "tz": "Europe/Paris"
        }
    })
    
    post_id = str(result.inserted_id)
    
    # Dupliquer
    resp = client.post(
        "/api/calendar/duplicate",
        json={
            "id": post_id,
            "target_start_at_utc": new_start,
            "tz": "Europe/Paris",
            "with_ai_variation": False
        }
    )
    
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert "ids" in body
    assert len(body["ids"]) == 1


@pytest.mark.asyncio
async def test_platform_validation(mongo_client):
    """Test de validation des contraintes de plateforme."""
    client = TestClient(app)
    
    org_id = "org_demo"
    now = datetime.now(timezone.utc)
    start_at = (now + timedelta(days=1)).isoformat()
    
    # Post avec caption trop long pour Twitter
    payload = {
        "org_id": org_id,
        "muse_id": "muse_demo",
        "platform": "x",
        "status": "scheduled",
        "content_ref": {
            "text": "A" * 300  # Trop long pour Twitter (280 max)
        },
        "schedule": {
            "start_at_utc": start_at,
            "tz": "Europe/Paris"
        }
    }
    
    resp = client.post("/api/calendar/schedule", json=payload)
    
    # Doit échouer avec une erreur de validation
    assert resp.status_code == 400
    assert "too long" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_calendar_filters(mongo_client):
    """Test des filtres du calendrier."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    db = get_core_db()
    
    org_id = "org_demo"
    now = datetime.now(timezone.utc)
    start_at = (now + timedelta(days=1)).isoformat()
    end_at = (now + timedelta(days=7)).isoformat()
    
    # Seed plusieurs posts
    await db["scheduled_posts"].insert_many([
        {
            "org_id": org_id,
            "muse_id": "muse_demo",
            "platform": "instagram",
            "status": "scheduled",
            "content_ref": {"text": "Post 1"},
            "schedule": {"start_at_utc": start_at, "tz": "Europe/Paris"},
            "labels": ["promo"]
        },
        {
            "org_id": org_id,
            "muse_id": "muse_demo",
            "platform": "tiktok",
            "status": "draft",
            "content_ref": {"text": "Post 2"},
            "schedule": {"start_at_utc": start_at, "tz": "Europe/Paris"},
            "labels": ["test"]
        }
    ])
    
    # Filtrer par plateforme
    resp = client.get(
        "/api/calendar/items",
        params={
            "org_id": org_id,
            "from_utc": start_at,
            "to_utc": end_at,
            "platforms": "instagram"
        }
    )
    
    assert resp.status_code == 200
    body = resp.json()
    assert all(item["platform"] == "instagram" for item in body["items"])
    
    # Filtrer par statut
    resp = client.get(
        "/api/calendar/items",
        params={
            "org_id": org_id,
            "from_utc": start_at,
            "to_utc": end_at,
            "statuses": "scheduled"
        }
    )
    
    assert resp.status_code == 200
    body = resp.json()
    assert all(item["status"] == "scheduled" for item in body["items"])




