# chat_tests/conftest.py

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from api.main import app
import api.databases.databases as databases
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.services.chat_omnichannel.deepseek_service import DeepSeekService
from api.services.chat_omnichannel.llm_service import GeneratedResponse
from unittest.mock import AsyncMock

from motor.motor_asyncio import AsyncIOMotorClient


@pytest.fixture(scope="session")
def mongo_client():
    """
    Crée un client Mongo Motor et surcharge databases.db pour l'app.
    (Fixture sync : on renvoie un AsyncIOMotorDatabase prêt à l'emploi.)
    """
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_chat_db"]
    databases.db = db  # <- l'app FastAPI utilisera cette DB
    yield db
    # Teardown minimal (éviter les soucis de boucle async ici)
    client.close()


@pytest_asyncio.fixture(autouse=True)
async def db_cleanup(mongo_client):
    """
    Nettoie la collection avant et après chaque test (auto).
    Remplace l'ancienne clear_chat_collection.
    """
    await mongo_client["chat_messages"].delete_many({})
    yield
    await mongo_client["chat_messages"].delete_many({})


@pytest.fixture(scope="session")
def test_client():
    """
    TestClient configuré avec :
    - override user (get_current_user)
    - stub LLM (DeepSeekService.generate -> "Réponse test")
    """
    fake_user = UserResponse(
        id="user_123",
        email="test@example.com",
        is_admin=True,
        roles=["admin"],
    )
    app.dependency_overrides[get_current_user] = lambda: fake_user

    # Stub LLM
    DeepSeekService.generate = AsyncMock(return_value=GeneratedResponse(text="Réponse test"))

    return TestClient(app)
