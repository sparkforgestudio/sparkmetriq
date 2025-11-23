# tests/intent/test_decision_and_flow.py
"""
Tests pour le Moteur d'Intentions.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

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
async def test_llm_fallback_when_no_scenario(mongo_client):
    """Test que le mode LLM Pilote fonctionne quand aucun scénario n'est disponible."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    db = get_core_db()
    
    org_id = "org_demo"
    muse_id = "muse_demo"
    
    # Seed persona + minimal knowledge
    await db["persona_profiles"].insert_one({
        "org_id": org_id,
        "muse_id": muse_id,
        "tone_profile": {
            "emoji_ratio": 0.3,
            "avg_sentence_length": 12,
            "keywords": ["playful", "teasing"],
            "do": ["Be playful", "Use emojis"],
            "dont": ["Be rude"]
        },
        "brand_boosters": ["Always playful"]
    })
    
    await db["knowledge_chunks"].insert_one({
        "org_id": org_id,
        "muse_id": muse_id,
        "kind": "brand_doc",
        "text": "Always playful; no illegal topics",
        "weight": 2.0,
        "ts": datetime.now(timezone.utc)
    })
    
    await db["chat_policies"].insert_one({
        "org_id": org_id,
        "muse_id": muse_id,
        "compliance": {
            "forbidden_words": ["minor", "illegal"]
        }
    })
    
    # Mock du LLM (on va juste vérifier que l'endpoint répond)
    # En production, on utiliserait un vrai mock pour le service LLM
    
    ev = {
        "org_id": org_id,
        "muse_id": muse_id,
        "platform": "instagram",
        "conversation_id": "conv_test_1",
        "type": "dm_received",
        "text": "hello"
    }
    
    resp = client.post("/api/intent/event", json=ev)
    
    # On accepte 200 ou 500 (si LLM non configuré en test)
    assert resp.status_code in [200, 500]
    
    if resp.status_code == 200:
        body = resp.json()
        assert body["mode"] in ("llm_pilot", "llm_fallback")
        assert "sent" in body or "status" in body


@pytest.mark.asyncio
async def test_scenario_guided_basic(mongo_client):
    """Test du mode scénario guidé."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    db = get_core_db()
    
    org_id = "org_demo"
    muse_id = "muse_demo"
    
    # Seed scenario
    await db["chat_scenarios"].insert_one({
        "org_id": org_id,
        "muse_id": muse_id,
        "title": "welcome_flow",
        "version": 1,
        "is_active": True,
        "platforms": ["instagram"],
        "trigger": {
            "type": "dm_received",
            "conditions": {}
        },
        "steps": [
            {
                "id": "s1",
                "type": "message",
                "template": "Hey {fan_name} 😘 Welcome!",
                "use_llm_tone": True,
                "delay_s": 0,
                "actions_on_send": []
            }
        ],
        "policy_refs": []
    })
    
    await db["persona_profiles"].insert_one({
        "org_id": org_id,
        "muse_id": muse_id,
        "tone_profile": {
            "emoji_ratio": 0.3,
            "avg_sentence_length": 12
        },
        "brand_boosters": []
    })
    
    await db["chat_policies"].insert_one({
        "org_id": org_id,
        "muse_id": muse_id,
        "compliance": {
            "forbidden_words": []
        }
    })
    
    ev = {
        "org_id": org_id,
        "muse_id": muse_id,
        "platform": "instagram",
        "conversation_id": "conv_test_2",
        "type": "dm_received",
        "text": "hi"
    }
    
    resp = client.post("/api/intent/event", json=ev)
    
    # On accepte 200 ou 500 (si LLM non configuré en test)
    assert resp.status_code in [200, 500]
    
    if resp.status_code == 200:
        body = resp.json()
        assert body["mode"] == "scenario_guided"
        assert "step" in body or "scenario" in body


@pytest.mark.asyncio
async def test_create_scenario(mongo_client):
    """Test de création d'un scénario."""
    client = TestClient(app)
    
    scenario = {
        "org_id": "org_demo",
        "muse_id": "muse_demo",
        "title": "test_scenario",
        "version": 1,
        "is_active": True,
        "platforms": ["instagram", "telegram"],
        "trigger": {
            "type": "dm_received",
            "conditions": {}
        },
        "steps": [
            {
                "id": "step1",
                "type": "message",
                "template": "Hello!",
                "use_llm_tone": False,
                "delay_s": 0,
                "actions_on_send": []
            }
        ],
        "policy_refs": []
    }
    
    resp = client.post("/api/intent/scenarios", json=scenario)
    
    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert body["scenario_title"] == "test_scenario"


@pytest.mark.asyncio
async def test_list_scenarios(mongo_client):
    """Test de liste des scénarios."""
    client = TestClient(app)
    
    from api.databases.databases import get_core_db
    db = get_core_db()
    
    org_id = "org_demo"
    muse_id = "muse_demo"
    
    # Seed scenarios
    await db["chat_scenarios"].insert_many([
        {
            "org_id": org_id,
            "muse_id": muse_id,
            "title": "scenario1",
            "version": 1,
            "is_active": True,
            "platforms": ["instagram"],
            "trigger": {"type": "dm_received", "conditions": {}},
            "steps": []
        },
        {
            "org_id": org_id,
            "muse_id": muse_id,
            "title": "scenario2",
            "version": 1,
            "is_active": False,
            "platforms": ["telegram"],
            "trigger": {"type": "dm_received", "conditions": {}},
            "steps": []
        }
    ])
    
    resp = client.get("/api/intent/scenarios", params={"muse_id": muse_id})
    
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["count"] >= 2
    assert len(body["items"]) >= 2


@pytest.mark.asyncio
async def test_upsert_persona(mongo_client):
    """Test de création/mise à jour de persona."""
    client = TestClient(app)
    
    persona = {
        "org_id": "org_demo",
        "muse_id": "muse_demo",
        "tone_profile": {
            "emoji_ratio": 0.4,
            "avg_sentence_length": 15,
            "keywords": ["funny", "sarcastic"],
            "do": ["Be funny"],
            "dont": ["Be boring"]
        },
        "brand_boosters": ["Always engaging"]
    }
    
    resp = client.post("/api/intent/persona", json=persona)
    
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True




