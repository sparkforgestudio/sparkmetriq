from fastapi.testclient import TestClient
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from api.main import app
from api.schemas.chat import ChatMessageOut
from api.schemas.users import UserResponse

client = TestClient(app)

# Override authentication dependency to use a fake user
@pytest.fixture(autouse=True)
def override_get_current_user(monkeypatch):
    fake_user = UserResponse(id="user123", email="test@example.com")
    async def fake_dep():
        return fake_user
    monkeypatch.setattr("api.routes.chats.get_current_user", fake_dep)

# Provide a MongoDB database for tests
@pytest.fixture(scope="module")
def mongo_client():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_chat_db"]
    yield db
    client.drop_database("test_chat_db")
    client.close()

# Clean up the collection before each test
@pytest.fixture(autouse=True)
async def clear_chat_messages(mongo_client):
    await mongo_client["chat_messages"].delete_many({})
    yield
    await mongo_client["chat_messages"].delete_many({})

# Stub the LLM service to return a fixed response
@pytest.fixture(autouse=True)
def stub_deepseek(monkeypatch):
    from api.services.chat_omnichannel.deepseek_service import DeepSeekService
    async def fake_generate(self, prompt, tenant_id):
        return ChatMessageOut(
            conversation_id=tenant_id or "",
            message="Réponse test",
            attachments=None,
            timestamp=None
        )
    monkeypatch.setattr(DeepSeekService, "generate", fake_generate)


def test_post_chat_send_creates_and_returns_response(mongo_client):
    # Direct access to the collection for assertions
    coll = mongo_client["chat_messages"]

    # Send a user message without conversation_id to start a new one
    payload = {"message": "Hello"}
    response = client.post("/chat/send", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "conversation_id" in data
    assert data["message"] == "Réponse test"

    # Verify two documents are in the collection: user then bot
    docs = list(coll.find().sort("created_at", 1))
    assert len(docs) == 2

    user_doc, bot_doc = docs
    # Check user message stored
    assert user_doc.get("role") == "user"
    assert user_doc.get("message") == "Hello"
    # Check bot response stored
    assert bot_doc.get("role") == "bot"
    assert bot_doc.get("message") == "Réponse test"
