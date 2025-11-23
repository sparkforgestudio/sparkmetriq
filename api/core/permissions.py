# api/core/permissions.py
"""
Système RBAC minimal pour la gestion des talents.
"""

from fastapi import HTTPException, status, Depends
from typing import Iterable, List, Optional, Callable, TYPE_CHECKING
from api.schemas.users import UserResponse, UserRole

# Import conditionnel pour éviter les imports circulaires
if TYPE_CHECKING:
    from api.core.auth import get_current_user

def require_role(current_user: UserResponse, roles: Iterable[str]):
    """Vérifie que l'utilisateur a au moins un des rôles requis."""
    # Si l'utilisateur est admin, il a tous les droits
    if getattr(current_user, "is_admin", False):
        return
    
    # Récupérer les rôles de l'utilisateur
    user_roles = set(getattr(current_user, "roles", []) or [])
    
    # Vérifier s'il y a une intersection avec les rôles requis
    if not (user_roles & set(roles)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Insufficient role. Required: {list(roles)}, User has: {list(user_roles)}"
        )


def has_role(required_role: UserRole) -> Callable:
    """
    Crée une dépendance FastAPI qui vérifie que l'utilisateur a le rôle requis.
    
    Args:
        required_role: Le rôle requis (UserRole enum)
        
    Returns:
        Fonction de dépendance FastAPI qui retourne l'utilisateur si le rôle est valide,
        ou lève une HTTPException 403 sinon.
    """
    # Import lazy pour éviter les imports circulaires
    from api.core.auth import get_current_user
    
    async def role_checker(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        # Si l'utilisateur est admin, il a tous les droits
        if getattr(current_user, "is_admin", False):
            return current_user
        
        # Récupérer les rôles de l'utilisateur
        user_roles = getattr(current_user, "roles", []) or []
        
        # Convertir les rôles en strings pour comparaison
        user_role_strings = [role.value if isinstance(role, UserRole) else str(role) for role in user_roles]
        
        # Vérifier si l'utilisateur a le rôle requis
        if required_role.value not in user_role_strings:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {required_role.value}, User has: {user_role_strings}"
            )
        
        return current_user
    
    return role_checker

def require_admin(current_user: UserResponse):
    """Vérifie que l'utilisateur est admin."""
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )

def require_operator_or_above(current_user: UserResponse):
    """Vérifie que l'utilisateur est au moins opérateur."""
    require_role(current_user, ["operator", "strategist", "supervisor", "lead_agent", "admin"])

def require_supervisor_or_above(current_user: UserResponse):
    """Vérifie que l'utilisateur est au moins superviseur."""
    require_role(current_user, ["supervisor", "lead_agent", "admin"])

def require_lead_agent_or_above(current_user: UserResponse):
    """Vérifie que l'utilisateur est au moins lead agent."""
    require_role(current_user, ["lead_agent", "admin"])

def can_access_muse(current_user: UserResponse, muse_id: str, tenant_id: str) -> bool:
    """Vérifie si l'utilisateur peut accéder à une muse spécifique."""
    # Admin peut accéder à tout
    if getattr(current_user, "is_admin", False):
        return True
    
    # Vérifier les assignments spécifiques
    # Cette fonction sera étendue avec la logique d'assignments
    return True  # Pour V1, on autorise l'accès

def get_user_accessible_muses(current_user: UserResponse, tenant_id: str) -> List[str]:
    """Récupère la liste des muses accessibles à l'utilisateur."""
    # Admin peut accéder à toutes les muses du tenant
    if getattr(current_user, "is_admin", False):
        # Cette fonction sera étendue pour récupérer toutes les muses du tenant
        return []
    
    # Pour les autres rôles, récupérer les assignments spécifiques
    # Cette fonction sera étendue avec la logique d'assignments
    return []

def check_platform_access(current_user: UserResponse, platform: str, muse_id: str) -> bool:
    """Vérifie si l'utilisateur peut accéder à une plateforme spécifique pour une muse."""
    # Admin peut accéder à tout
    if getattr(current_user, "is_admin", False):
        return True
    
    # Vérifier les assignments spécifiques par plateforme
    # Cette fonction sera étendue avec la logique d'assignments
    return True  # Pour V1, on autorise l'accès

class RoleHierarchy:
    """Hiérarchie des rôles avec leurs permissions."""
    
    ROLES = {
        "admin": {
            "level": 5,
            "permissions": ["all"],
            "description": "Accès complet à toutes les fonctionnalités"
        },
        "lead_agent": {
            "level": 4,
            "permissions": ["manage_operators", "view_analytics", "manage_integrations"],
            "description": "Gestion des opérateurs et intégrations"
        },
        "supervisor": {
            "level": 3,
            "permissions": ["assign_operators", "view_audit", "escalate"],
            "description": "Supervision des opérateurs et audit"
        },
        "strategist": {
            "level": 2,
            "permissions": ["view_analytics", "create_content", "manage_campaigns"],
            "description": "Stratégie et contenu"
        },
        "operator": {
            "level": 1,
            "permissions": ["reply_messages", "tag_fans", "add_notes"],
            "description": "Opérations de base"
        }
    }
    
    @classmethod
    def get_role_level(cls, role: str) -> int:
        """Récupère le niveau d'un rôle."""
        return cls.ROLES.get(role, {}).get("level", 0)
    
    @classmethod
    def has_permission(cls, user_roles: List[str], permission: str) -> bool:
        """Vérifie si l'utilisateur a une permission spécifique."""
        for role in user_roles:
            role_info = cls.ROLES.get(role, {})
            permissions = role_info.get("permissions", [])
            if "all" in permissions or permission in permissions:
                return True
        return False
    
    @classmethod
    def can_manage_role(cls, manager_roles: List[str], target_role: str) -> bool:
        """Vérifie si un manager peut gérer un rôle cible."""
        manager_level = max([cls.get_role_level(role) for role in manager_roles], default=0)
        target_level = cls.get_role_level(target_role)
        return manager_level > target_level