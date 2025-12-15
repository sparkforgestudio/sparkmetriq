"""
Sécurité et authentification pour saasentialcore.

Ce module gère :
- Génération et validation de tokens JWT
- Hachage et vérification de mots de passe
- Utilitaires de sécurité
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext


# Contexte de hachage de mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond au hash.
    
    Args:
        plain_password: Mot de passe en clair
        hashed_password: Hash du mot de passe
        
    Returns:
        True si le mot de passe correspond, False sinon
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash un mot de passe.
    
    Args:
        password: Mot de passe en clair
        
    Returns:
        Hash du mot de passe
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None,
    default_expire_minutes: int = 60
) -> str:
    """
    Crée un token JWT d'accès.
    
    Args:
        data: Données à encoder dans le token
        secret_key: Clé secrète pour signer le token
        algorithm: Algorithme de signature (défaut: HS256)
        expires_delta: Durée d'expiration personnalisée
        default_expire_minutes: Durée d'expiration par défaut (minutes)
        
    Returns:
        Token JWT encodé
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=default_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def decode_access_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256"
) -> Optional[Dict[str, Any]]:
    """
    Décode et valide un token JWT.
    
    Args:
        token: Token JWT à décoder
        secret_key: Clé secrète pour vérifier le token
        algorithm: Algorithme de signature (défaut: HS256)
        
    Returns:
        Données décodées du token ou None si invalide
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        return None

