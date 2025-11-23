# tests/muses/test_muse_categories.py
"""
Tests pour les catégories de muses et agrégations.
"""

import pytest
from fastapi.testclient import TestClient
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


@pytest.mark.asyncio
async def test_list_categories(mongo_client):
    """Test de liste des catégories avec compteurs."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    db = get_core_db()
    
    org_id = "org_test"
    
    # Seed catégories
    await db["muse_categories"].insert_many([
        {"_id": "cosplay", "label": "Cosplay", "is_active": True, "order": 10},
        {"_id": "fitness", "label": "Fitness", "is_active": True, "order": 20}
    ])
    
    # Seed muses avec catégories
    await db["muses"].insert_many([
        {"_id": "muse1", "org_id": org_id, "categories": ["cosplay", "fitness"], "status": "active"},
        {"_id": "muse2", "org_id": org_id, "categories": ["cosplay"], "status": "active"},
        {"_id": "muse3", "org_id": "other_org", "categories": ["cosplay"], "status": "active"}  # Autre org
    ])
    
    # Lister les catégories
    response = client.get("/api/muses/categories")
    
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) >= 2
    assert body["counts"]["cosplay"] == 2  # Seulement pour org_test
    assert body["counts"]["fitness"] == 1


@pytest.mark.asyncio
async def test_patch_muse_categories(mongo_client):
    """Test de mise à jour des catégories d'une muse."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    db = get_core_db()
    
    org_id = "org_test"
    muse_id = "muse_test"
    
    # Seed catégories
    await db["muse_categories"].insert_many([
        {"_id": "cosplay", "label": "Cosplay", "is_active": True},
        {"_id": "fitness", "label": "Fitness", "is_active": True}
    ])
    
    # Créer une muse
    await db["muses"].insert_one({
        "_id": muse_id,
        "org_id": org_id,
        "display_name": "Test Muse",
        "categories": []
    })
    
    # Mettre à jour les catégories
    payload = {
        "categories": ["cosplay", "fitness"]
    }
    
    response = client.patch(f"/api/muses/{muse_id}/categories", json=payload)
    
    assert response.status_code == 200
    assert response.json()["ok"] is True
    
    # Vérifier que les catégories ont été mises à jour
    muse = await db["muses"].find_one({"_id": muse_id})
    assert set(muse["categories"]) == {"cosplay", "fitness"}


@pytest.mark.asyncio
async def test_patch_invalid_category(mongo_client):
    """Test que les catégories invalides sont rejetées."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    db = get_core_db()
    
    org_id = "org_test"
    muse_id = "muse_test"
    
    # Créer une muse
    await db["muses"].insert_one({
        "_id": muse_id,
        "org_id": org_id,
        "display_name": "Test Muse",
        "categories": []
    })
    
    # Essayer d'assigner une catégorie inexistante
    payload = {
        "categories": ["invalid_category"]
    }
    
    response = client.patch(f"/api/muses/{muse_id}/categories", json=payload)
    
    assert response.status_code == 400
    assert "Unknown" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analytics_by_category(mongo_client):
    """Test des agrégations par catégorie."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db, get_bi_db
    
    db_core = get_core_db()
    db_bi = get_bi_db()
    
    org_id = "org_test"
    now = datetime.now(timezone.utc)
    date_from = (now - timedelta(days=30)).isoformat()
    date_to = now.isoformat()
    
    # Seed catégories
    await db_core["muse_categories"].insert_many([
        {"_id": "cosplay", "label": "Cosplay", "is_active": True},
        {"_id": "fitness", "label": "Fitness", "is_active": True}
    ])
    
    # Seed muses
    await db_core["muses"].insert_many([
        {"_id": "muse1", "org_id": org_id, "categories": ["cosplay"], "status": "active"},
        {"_id": "muse2", "org_id": org_id, "categories": ["fitness"], "status": "active"}
    ])
    
    # Seed données BI
    await db_bi["payments"].insert_many([
        {
            "org_id": org_id,
            "muse_id": "muse1",
            "amount": 100.0,
            "ts": now - timedelta(days=1)
        },
        {
            "org_id": org_id,
            "muse_id": "muse2",
            "amount": 50.0,
            "ts": now - timedelta(days=1)
        }
    ])
    
    await db_bi["ppv_sales"].insert_many([
        {
            "org_id": org_id,
            "muse_id": "muse1",
            "ppv_amount": 25.0,
            "ts": now - timedelta(days=2)
        }
    ])
    
    await db_bi["messages"].insert_many([
        {
            "org_id": org_id,
            "muse_id": "muse1",
            "direction": "in",
            "ts": now - timedelta(days=3)
        },
        {
            "org_id": org_id,
            "muse_id": "muse2",
            "direction": "out",
            "ts": now - timedelta(days=3)
        }
    ])
    
    await db_bi["funnel_events"].insert_many([
        {
            "org_id": org_id,
            "muse_id": "muse1",
            "event": "subscribe",
            "ts": now - timedelta(days=4)
        },
        {
            "org_id": org_id,
            "muse_id": "muse2",
            "event": "churn",
            "ts": now - timedelta(days=4)
        }
    ])
    
    # Appeler l'agrégation
    payload = {
        "date_from": date_from,
        "date_to": date_to,
        "granularity": "daily"
    }
    
    response = client.post("/api/analytics/muses/by-category", json=payload)
    
    assert response.status_code == 200
    body = response.json()
    
    assert len(body["items"]) >= 2
    assert body["total_revenue"] > 0
    
    # Vérifier les totaux
    cosplay_item = next((item for item in body["items"] if item["category"] == "cosplay"), None)
    fitness_item = next((item for item in body["items"] if item["category"] == "fitness"), None)
    
    if cosplay_item:
        assert cosplay_item["revenue_total"] >= 100.0
        assert cosplay_item["ppv_total"] >= 25.0
    
    if fitness_item:
        assert fitness_item["revenue_total"] >= 50.0


@pytest.mark.asyncio
async def test_analytics_by_category_with_filters(mongo_client):
    """Test des agrégations avec filtres de catégorie et canal."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db, get_bi_db
    
    db_core = get_core_db()
    db_bi = get_bi_db()
    
    org_id = "org_test"
    now = datetime.now(timezone.utc)
    date_from = (now - timedelta(days=30)).isoformat()
    date_to = now.isoformat()
    
    # Setup de base
    await db_core["muse_categories"].insert_one({
        "_id": "cosplay",
        "label": "Cosplay",
        "is_active": True
    })
    
    await db_core["muses"].insert_one({
        "_id": "muse1",
        "org_id": org_id,
        "categories": ["cosplay"],
        "status": "active"
    })
    
    await db_bi["payments"].insert_one({
        "org_id": org_id,
        "muse_id": "muse1",
        "amount": 100.0,
        "source": "instagram",
        "ts": now - timedelta(days=1)
    })
    
    # Appeler avec filtre de catégorie
    payload = {
        "date_from": date_from,
        "date_to": date_to,
        "categories": ["cosplay"],
        "channels": ["instagram"]
    }
    
    response = client.post("/api/analytics/muses/by-category", json=payload)
    
    assert response.status_code == 200
    body = response.json()
    
    # Devrait avoir seulement cosplay
    assert len(body["items"]) >= 1
    cosplay_items = [item for item in body["items"] if item["category"] == "cosplay"]
    assert len(cosplay_items) > 0


@pytest.mark.asyncio
async def test_analytics_empty_data(mongo_client):
    """Test avec aucune donnée."""
    client = TestClient(app)
    
    org_id = "org_test"
    now = datetime.now(timezone.utc)
    date_from = (now - timedelta(days=30)).isoformat()
    date_to = now.isoformat()
    
    payload = {
        "date_from": date_from,
        "date_to": date_to
    }
    
    response = client.post("/api/analytics/muses/by-category", json=payload)
    
    assert response.status_code == 200
    body = response.json()
    
    assert body["items"] == []
    assert body["total_revenue"] == 0.0
    assert body["total_ppv"] == 0.0
    assert body["total_messages_in"] == 0
    assert body["total_messages_out"] == 0




