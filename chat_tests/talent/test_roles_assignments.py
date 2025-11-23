# chat_tests/talent/test_roles_assignments.py
"""
Tests d'intégration pour les rôles et assignations.
"""

from fastapi.testclient import TestClient
from datetime import datetime

def test_roles_assignments(test_client: TestClient, mongo_client):
    """Test complet des rôles et assignations."""
    # Test grant role
    r1 = test_client.post("/api/talent/roles/grant", json={
        "user_id": "op_1",
        "role": "operator"
    })
    assert r1.status_code == 200
    
    # Vérifier que le rôle a été accordé
    role = mongo_client["operator_roles"].find_one({
        "tenant_id": "user_123",
        "user_id": "op_1",
        "role": "operator"
    })
    assert role is not None
    
    # Test assignation d'opérateur
    r2 = test_client.post("/api/talent/assignments", json={
        "muse_id": "melissa",
        "platform": "instagram",
        "operator_id": "op_1"
    })
    assert r2.status_code == 200
    assert "id" in r2.json()
    
    # Vérifier l'assignation
    assignment = mongo_client["muse_assignments"].find_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "platform": "instagram",
        "operator_id": "op_1"
    })
    assert assignment is not None
    
    # Test liste des assignations
    r3 = test_client.get("/api/talent/assignments", params={"muse_id": "melissa"})
    assert r3.status_code == 200
    assignments = r3.json()
    assert isinstance(assignments, list)
    assert len(assignments) >= 1
    
    # Vérifier que l'assignation est dans la liste
    assignment_found = any(
        a["muse_id"] == "melissa" and 
        a["platform"] == "instagram" and 
        a["operator_id"] == "op_1"
        for a in assignments
    )
    assert assignment_found

def test_multiple_assignments(test_client: TestClient, mongo_client):
    """Test de plusieurs assignations."""
    # Créer plusieurs assignations
    assignments_data = [
        {"muse_id": "melissa", "platform": "instagram", "operator_id": "op_1"},
        {"muse_id": "melissa", "platform": "twitter", "operator_id": "op_2"},
        {"muse_id": "sophia", "platform": "instagram", "operator_id": "op_1"},
        {"muse_id": "sophia", "platform": "telegram", "operator_id": "op_3"}
    ]
    
    for assignment_data in assignments_data:
        r = test_client.post("/api/talent/assignments", json=assignment_data)
        assert r.status_code == 200
    
    # Récupérer toutes les assignations
    r = test_client.get("/api/talent/assignments")
    assert r.status_code == 200
    assignments = r.json()
    assert len(assignments) >= 4
    
    # Vérifier que toutes les assignations sont présentes
    for assignment_data in assignments_data:
        assignment_found = any(
            a["muse_id"] == assignment_data["muse_id"] and
            a["platform"] == assignment_data["platform"] and
            a["operator_id"] == assignment_data["operator_id"]
            for a in assignments
        )
        assert assignment_found

def test_role_hierarchy(test_client: TestClient, mongo_client):
    """Test de la hiérarchie des rôles."""
    # Accorder différents rôles
    roles_data = [
        {"user_id": "user_admin", "role": "admin"},
        {"user_id": "user_lead", "role": "lead_agent"},
        {"user_id": "user_supervisor", "role": "supervisor"},
        {"user_id": "user_strategist", "role": "strategist"},
        {"user_id": "user_operator", "role": "operator"}
    ]
    
    for role_data in roles_data:
        r = test_client.post("/api/talent/roles/grant", json=role_data)
        assert r.status_code == 200
    
    # Vérifier que tous les rôles ont été accordés
    for role_data in roles_data:
        role = mongo_client["operator_roles"].find_one({
            "tenant_id": "user_123",
            "user_id": role_data["user_id"],
            "role": role_data["role"]
        })
        assert role is not None

def test_revoke_role(test_client: TestClient, mongo_client):
    """Test de révocation de rôle."""
    # Accorder un rôle d'abord
    mongo_client["operator_roles"].insert_one({
        "tenant_id": "user_123",
        "user_id": "user_revoke",
        "role": "operator",
        "created_at": utcnow()
    })
    
    # Vérifier que le rôle existe
    role = mongo_client["operator_roles"].find_one({
        "tenant_id": "user_123",
        "user_id": "user_revoke",
        "role": "operator"
    })
    assert role is not None
    
    # Révoquer le rôle
    r = test_client.delete("/api/talent/roles/revoke", json={
        "user_id": "user_revoke",
        "role": "operator"
    })
    assert r.status_code == 200
    
    # Vérifier que le rôle a été révoqué
    role = mongo_client["operator_roles"].find_one({
        "tenant_id": "user_123",
        "user_id": "user_revoke",
        "role": "operator"
    })
    assert role is None

def test_remove_assignment(test_client: TestClient, mongo_client):
    """Test de suppression d'assignation."""
    # Créer une assignation
    mongo_client["muse_assignments"].insert_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "platform": "instagram",
        "operator_id": "op_remove",
        "created_at": utcnow()
    })
    
    # Vérifier que l'assignation existe
    assignment = mongo_client["muse_assignments"].find_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "platform": "instagram",
        "operator_id": "op_remove"
    })
    assert assignment is not None
    
    # Supprimer l'assignation
    r = test_client.delete("/api/talent/assignments", params={
        "muse_id": "melissa",
        "platform": "instagram"
    })
    assert r.status_code == 200
    
    # Vérifier que l'assignation a été supprimée
    assignment = mongo_client["muse_assignments"].find_one({
        "tenant_id": "user_123",
        "muse_id": "melissa",
        "platform": "instagram"
    })
    assert assignment is None

def test_assignment_stats(test_client: TestClient, mongo_client):
    """Test des statistiques d'assignation."""
    # Créer plusieurs assignations pour les statistiques
    assignments_data = [
        {"muse_id": "melissa", "platform": "instagram", "operator_id": "op_1"},
        {"muse_id": "melissa", "platform": "twitter", "operator_id": "op_1"},
        {"muse_id": "sophia", "platform": "instagram", "operator_id": "op_2"},
        {"muse_id": "sophia", "platform": "telegram", "operator_id": "op_2"}
    ]
    
    for assignment_data in assignments_data:
        mongo_client["muse_assignments"].insert_one({
            "tenant_id": "user_123",
            **assignment_data,
            "created_at": utcnow()
        })
    
    # Récupérer les statistiques
    r = test_client.get("/api/talent/assignments/stats")
    assert r.status_code == 200
    stats = r.json()
    
    assert "total_assignments" in stats
    assert "operators" in stats
    assert "muses" in stats
    assert "platforms" in stats
    
    # Vérifier que les statistiques sont cohérentes
    assert stats["total_assignments"] >= 4
    assert len(stats["operators"]) >= 2
    assert len(stats["muses"]) >= 2
    assert len(stats["platforms"]) >= 3

def test_get_user_roles(test_client: TestClient, mongo_client):
    """Test de récupération des rôles d'un utilisateur."""
    # Accorder plusieurs rôles à un utilisateur
    roles = ["operator", "strategist"]
    for role in roles:
        mongo_client["operator_roles"].insert_one({
            "tenant_id": "user_123",
            "user_id": "user_multi_role",
            "role": role,
            "created_at": utcnow()
        })
    
    # Récupérer les rôles
    r = test_client.get("/api/talent/roles/user_multi_role")
    assert r.status_code == 200
    user_roles = r.json()
    
    assert isinstance(user_roles, list)
    assert len(user_roles) >= 2
    assert "operator" in user_roles
    assert "strategist" in user_roles




