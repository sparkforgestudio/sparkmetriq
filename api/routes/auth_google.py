# api/routes/auth_google.py
"""
Routes FastAPI pour l'authentification Google OAuth.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from api.core.auth import create_access_token
from api.services.auth.google_oauth import verify_google_token, get_or_create_google_user
from api.schemas.users import UserResponse
from api.core.configs import GOOGLE_CLIENT_ID
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/google", tags=["Auth Google"])


class GoogleTokenRequest(BaseModel):
    """Requête avec token Google ID."""
    token: str = Field(..., description="Token ID Google (id_token)")
    org_id: Optional[str] = Field(None, description="ID de l'organisation (optionnel)")


@router.post("/login", response_model=Dict[str, Any])
async def google_login(payload: GoogleTokenRequest) -> Dict[str, Any]:
    """Connecte un utilisateur avec son token Google.
    
    Vérifie le token Google ID, crée ou récupère l'utilisateur,
    et retourne un token JWT pour l'API.
    
    Args:
        payload: Token Google ID et optionnellement org_id.
        
    Returns:
        Dict avec access_token (JWT), token_type, et user (informations utilisateur).
        
    Raises:
        HTTPException: 400 si le token est invalide, 500 en cas d'erreur serveur.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured"
        )
    
    # Vérifier le token Google
    google_info = await verify_google_token(payload.token)
    if not google_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google token"
        )
    
    # Récupérer ou créer l'utilisateur
    try:
        user = await get_or_create_google_user(google_info, payload.org_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Créer un token JWT
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(hours=24)  # Token plus long pour OAuth
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name"),
            "picture": user.get("picture"),
            "org_id": user.get("org_id"),
            "is_admin": user.get("is_admin", False),
        }
    }


@router.post("/register", response_model=Dict[str, Any])
async def google_register(payload: GoogleTokenRequest) -> Dict[str, Any]:
    """Inscrit ou connecte un utilisateur avec son token Google.
    
    Alias pour /login car Google OAuth gère automatiquement l'inscription.
    Crée l'utilisateur s'il n'existe pas, sinon le connecte.
    
    Args:
        payload: Token Google ID et optionnellement org_id.
        
    Returns:
        Dict avec access_token (JWT), token_type, et user (informations utilisateur).
        
    Raises:
        HTTPException: 400 si le token est invalide, 500 en cas d'erreur serveur.
    """
    # Pour Google OAuth, register et login font la même chose
    return await google_login(payload)
