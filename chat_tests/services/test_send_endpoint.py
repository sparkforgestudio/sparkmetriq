import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from pydantic import EmailStr


@pytest.fixture(scope="session")
def test_client():
    """
    Fixture stable avec uniquement l’override d’utilisateur.
    """
    print("🧪 [Fixture] Création du TestClient avec utilisateur factice...")

    # Crée un utilisateur conforme à UserResponse (à adapter selon ton modèle exact)
    fake_user = UserResponse(
        id="user_123",
        email="test@example.com",
        is_admin=True,
        roles=["admin"]
    )

    # Override de la dépendance auth
    app.dependency_overrides[get_current_user] = lambda: fake_user

    print("✅ [Fixture] TestClient avec user prêt.")
    return TestClient(app)
