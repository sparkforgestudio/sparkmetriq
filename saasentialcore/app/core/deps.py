"""
Dépendances communes pour saasentialcore.

Ce module fournit des dépendances FastAPI réutilisables :
- Authentification
- Base de données
- Validation
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

# Schéma OAuth2 pour l'authentification
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    Dépendance FastAPI pour récupérer l'utilisateur actuel depuis le token JWT.
    
    Args:
        token: Token JWT extrait de la requête
        
    Returns:
        Données de l'utilisateur décodées depuis le token
        
    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    from saasentialcore.app.core.security import decode_access_token
    from saasentialcore.app.core.config import settings
    
    payload = decode_access_token(token, settings.secret_key, settings.algorithm)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Vérifier que l'utilisateur existe en base
    # user_id = payload.get("sub")
    # user = await get_user_from_db(user_id)
    # if user is None:
    #     raise HTTPException(...)
    
    return payload


async def get_db() -> AsyncIOMotorDatabase:
    """
    Dépendance FastAPI pour obtenir la connexion à la base de données.
    
    Returns:
        Instance de la base de données MongoDB
    """
    from saasentialcore.app.core.config import settings
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # TODO: Implémenter la gestion du pool de connexions
    # client = AsyncIOMotorClient(settings.mongo_uri)
    # db = client[settings.db_name]
    # return db
    
    raise NotImplementedError("get_db() doit être implémenté")


def get_current_org_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    Dépendance FastAPI pour récupérer l'org_id de l'utilisateur actuel.
    
    Args:
        current_user: Utilisateur actuel (injecté par get_current_user)
        
    Returns:
        ID de l'organisation de l'utilisateur
        
    Raises:
        HTTPException: Si l'utilisateur n'a pas d'organisation
    """
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utilisateur sans organisation"
        )
    return org_id

