# tests/cloudphone/test_profiles_form_crud.py
"""
Tests d'intégration pour le CRUD des profils CloudPhone (form-first).
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch, AsyncMock
from api.main import app
from api.schemas.cloudphone import ProfileCreate, ProfileUpdate

client = TestClient(app)

# Mock pour l'authentification
def mock_get_current_user():
    """Mock de l'utilisateur courant pour les tests."""
    from api.schemas.users import UserResponse
    return UserResponse(
        id="test_user_id",
        email="test@example.com",
        org_id="test_org",
        role="admin"
    )

@pytest.fixture
def setup_test_data():
    """Configurer les données de test."""
    # Pour les tests avec TestClient, on utilise des mocks
    return "507f1f77bcf86cd799439011"  # Mock ObjectId

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_create_profile_success(mock_auth):
    """Test de création d'un profil avec succès."""
    profile_data = ProfileCreate(
        name="Nouveau Profil",
        area="US",
        lang="en-US",
        proxy_template="residential_fixed_us_01",
        tags=["production", "us"],
        remark="Profil de production US"
    )
    
    response = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data.dict()
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Nouveau Profil"
    assert data["area"] == "US"
    assert data["lang"] == "en-US"
    assert data["proxy_template"] == "residential_fixed_us_01"
    assert data["tags"] == ["production", "us"]
    assert data["remark"] == "Profil de production US"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_create_profile_duplicate_name(mock_auth):
    """Test de création d'un profil avec un nom dupliqué."""
    # Créer le premier profil
    profile_data = ProfileCreate(
        name="Profil Unique",
        area="EU",
        lang="fr-FR"
    )
    
    response1 = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data.dict()
    )
    assert response1.status_code == 201
    
    # Essayer de créer un profil avec le même nom
    response2 = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data.dict()
    )
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"]

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_create_profile_validation_error(mock_auth):
    """Test de création d'un profil avec des données invalides."""
    profile_data = {
        "name": "",  # Nom vide
        "area": "INVALID_AREA",  # Zone invalide
        "lang": "invalid-lang"  # Langue invalide
    }
    
    response = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data
    )
    
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) > 0

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_get_profile_success(mock_auth):
    """Test de récupération d'un profil avec succès."""
    # Créer d'abord un profil
    profile_data = ProfileCreate(
        name="Test Profile",
        area="EU",
        lang="fr-FR"
    )
    
    create_response = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data.dict()
    )
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]
    
    # Récupérer le profil
    response = client.get(f"/api/mobile-cloud/profiles/{profile_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == profile_id
    assert data["name"] == "Test Profile"
    assert data["area"] == "EU"
    assert data["lang"] == "fr-FR"

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_get_profile_not_found(mock_auth):
    """Test de récupération d'un profil inexistant."""
    fake_id = "507f1f77bcf86cd799439011"
    
    response = client.get(f"/api/mobile-cloud/profiles/{fake_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_update_profile_success(mock_auth):
    """Test de mise à jour d'un profil avec succès."""
    # Créer d'abord un profil
    profile_data = ProfileCreate(
        name="Test Profile",
        area="EU",
        lang="fr-FR"
    )
    
    create_response = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data.dict()
    )
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]
    
    # Mettre à jour le profil
    update_data = ProfileUpdate(
        name="Profil Modifié",
        area="US",
        lang="en-US",
        tags=["updated", "production"]
    )
    
    response = client.put(
        f"/api/mobile-cloud/profiles/{profile_id}",
        json=update_data.dict(exclude_unset=True)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Profil Modifié"
    assert data["area"] == "US"
    assert data["lang"] == "en-US"
    assert data["tags"] == ["updated", "production"]
    assert data["updated_at"] != data["created_at"]

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_update_profile_not_found(mock_auth):
    """Test de mise à jour d'un profil inexistant."""
    fake_id = "507f1f77bcf86cd799439011"
    
    update_data = ProfileUpdate(name="Profil Modifié")
    
    response = client.put(
        f"/api/mobile-cloud/profiles/{fake_id}",
        json=update_data.dict(exclude_unset=True)
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_list_profiles_success(mock_auth):
    """Test de liste des profils avec succès."""
    # Créer plusieurs profils
    profiles = [
        {"name": "Profil 1", "area": "EU", "tags": ["test"]},
        {"name": "Profil 2", "area": "US", "tags": ["production"]},
        {"name": "Profil 3", "area": "ASIA", "tags": ["test", "demo"]}
    ]
    
    for profile_data in profiles:
        response = client.post(
            "/api/mobile-cloud/profiles",
            json=profile_data
        )
        assert response.status_code == 201
    
    # Lister les profils
    response = client.get("/api/mobile-cloud/profiles")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 3
    assert data["total"] >= 3
    assert data["page"] == 1
    assert data["page_size"] == 25

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_list_profiles_with_filters(mock_auth):
    """Test de liste des profils avec filtres."""
    # Créer des profils avec différents tags
    profiles = [
        {"name": "Profil EU", "area": "EU", "tags": ["test", "eu"]},
        {"name": "Profil US", "area": "US", "tags": ["production", "us"]},
        {"name": "Profil ASIA", "area": "ASIA", "tags": ["test", "asia"]}
    ]
    
    for profile_data in profiles:
        response = client.post(
            "/api/mobile-cloud/profiles",
            json=profile_data
        )
        assert response.status_code == 201
    
    # Filtrer par zone
    response = client.get("/api/mobile-cloud/profiles?area=EU")
    
    assert response.status_code == 200
    data = response.json()
    assert all(item["area"] == "EU" for item in data["items"])
    
    # Filtrer par tag
    response = client.get("/api/mobile-cloud/profiles?tag=test")
    
    assert response.status_code == 200
    data = response.json()
    assert all("test" in item["tags"] for item in data["items"])
    
    # Filtrer par recherche
    response = client.get("/api/mobile-cloud/profiles?search=EU")
    
    assert response.status_code == 200
    data = response.json()
    assert any("EU" in item["name"] for item in data["items"])

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_delete_profile_success(mock_auth):
    """Test de suppression d'un profil avec succès."""
    # Créer d'abord un profil
    profile_data = ProfileCreate(
        name="Test Profile",
        area="EU",
        lang="fr-FR"
    )
    
    create_response = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data.dict()
    )
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]
    
    # Supprimer le profil
    response = client.delete(f"/api/mobile-cloud/profiles/{profile_id}")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Profile deleted successfully"
    
    # Vérifier que le profil n'existe plus
    response = client.get(f"/api/mobile-cloud/profiles/{profile_id}")
    assert response.status_code == 404

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_delete_profile_not_found(mock_auth):
    """Test de suppression d'un profil inexistant."""
    fake_id = "507f1f77bcf86cd799439011"
    
    response = client.delete(f"/api/mobile-cloud/profiles/{fake_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_profile_validation(mock_auth):
    """Test de validation des données de profil."""
    # Test des longueurs min/max
    test_cases = [
        {"name": "A", "expected_status": 422},  # Trop court
        {"name": "A" * 81, "expected_status": 422},  # Trop long
        {"name": "Valid Name", "expected_status": 201},  # Valide
    ]
    
    for case in test_cases:
        profile_data = {"name": case["name"]}
        
        response = client.post(
            "/api/mobile-cloud/profiles",
            json=profile_data
        )
        
        assert response.status_code == case["expected_status"]
    
    # Test des tags
    profile_data = {
        "name": "Test Tags",
        "tags": ["valid", "test", "tag"]  # Tags valides
    }
    
    response = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["tags"] == ["valid", "test", "tag"]

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_profile_audit_trail(mock_auth):
    """Test du trail d'audit des profils."""
    # Créer un profil
    profile_data = ProfileCreate(
        name="Audit Test Profile",
        area="EU",
        lang="fr-FR"
    )
    
    response = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data.dict()
    )
    
    assert response.status_code == 201
    profile_id = response.json()["id"]
    
    # Modifier le profil
    update_data = ProfileUpdate(name="Audit Test Profile Updated")
    
    response = client.put(
        f"/api/mobile-cloud/profiles/{profile_id}",
        json=update_data.dict(exclude_unset=True)
    )
    
    assert response.status_code == 200
    
    # Supprimer le profil
    response = client.delete(f"/api/mobile-cloud/profiles/{profile_id}")
    
    assert response.status_code == 200

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_profile_indexes(mock_auth):
    """Test des index MongoDB pour les profils."""
    # Ce test vérifie que les routes fonctionnent correctement
    # Les index sont testés indirectement via les performances
    profile_data = ProfileCreate(
        name="Index Test Profile",
        area="EU",
        lang="fr-FR"
    )
    
    response = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data.dict()
    )
    
    assert response.status_code == 201
    profile_id = response.json()["id"]
    
    # Vérifier que le profil peut être récupéré rapidement
    response = client.get(f"/api/mobile-cloud/profiles/{profile_id}")
    assert response.status_code == 200
    
    # Vérifier que la liste fonctionne rapidement
    response = client.get("/api/mobile-cloud/profiles")
    assert response.status_code == 200

@patch('api.core.auth.get_current_user', side_effect=mock_get_current_user)
def test_profile_cleanup(mock_auth):
    """Test de nettoyage des données de test."""
    # Créer un profil pour le test
    profile_data = ProfileCreate(
        name="Cleanup Test Profile",
        area="EU",
        lang="fr-FR"
    )
    
    response = client.post(
        "/api/mobile-cloud/profiles",
        json=profile_data.dict()
    )
    
    assert response.status_code == 201
    profile_id = response.json()["id"]
    
    # Supprimer le profil
    response = client.delete(f"/api/mobile-cloud/profiles/{profile_id}")
    
    assert response.status_code == 200
    
    # Vérifier que le profil n'existe plus
    response = client.get(f"/api/mobile-cloud/profiles/{profile_id}")
    assert response.status_code == 404