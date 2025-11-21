import pytest
from fastapi.testclient import TestClient
from api.main import app  # Assurez-vous que ce chemin correspond à l'emplacement de votre instance d'app FastAPI

client = TestClient(app)

def test_homepage():
    # Exemple de test simple qui vérifie que la route racine répond avec un code 200
    response = client.get("/")
    assert response.status_code == 200
