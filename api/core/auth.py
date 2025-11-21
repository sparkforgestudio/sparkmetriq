from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from api.databases.databases import db
from api.schemas.users import UserResponse
from api.core.configs import SECRET_KEY, ALGORITHM  # Votre fichier api/core/configs.py

# Utilitaire pour datetime UTC
def utcnow() -> datetime:
    """Retourne un datetime timezone-aware en UTC."""
    return datetime.now(timezone.utc)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auths/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token d'accès JWT avec une expiration (par défaut 1 heure).
    """
    to_encode = data.copy()
    expire = utcnow() + (expires_delta or timedelta(hours=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """
    Décode le token JWT et renvoie l'utilisateur correspondant.
    Lève une 401 si le token est invalide ou si l'utilisateur n'existe pas.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide : sujet manquant",
            )
        user = await db["users"].find_one({"email": email})
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé",
            )
        return UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            org_id=user.get("org_id", ""),
            is_admin=user.get("is_admin", False),
            roles=user.get("roles", [])
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
        )


async def is_admin(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Vérifie que l'utilisateur est admin ; lève une 403 sinon.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes",
        )
    return current_user


def create_password_reset_token(email: str) -> str:
    """
    Génère un token JWT pour la réinitialisation de mot de passe (valide 15 min).
    """
    expire = utcnow() + timedelta(minutes=15)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Vérifie le token de réinitialisation et retourne l'email si valide,
    ou None si expiré / invalide.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def send_password_reset_email(email: str, reset_link: str) -> None:
    """
    Envoie (ici de manière factice) l'email de réinitialisation.
    À remplacer par votre implémentation d'envoi réel.
    """
    # Exemple : appel à votre service SMTP / SendGrid / etc.
    print(f"[Email RESET] Vers : {email} — Lien : {reset_link}")


# Aliases pour compatibilité avec les imports existants
verify_reset_token = verify_password_reset_token
