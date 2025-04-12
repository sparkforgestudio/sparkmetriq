from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from services.databases import db
from schemas.users import UserResponse
from core.configs import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auths/login")

# Créer un token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(hours=1))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Vérifier et extraire l'utilisateur à partir du token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db["users"].find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return UserResponse(email=user["email"], is_admin=user["is_admin"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Vérifier si l'utilisateur est admin
async def is_admin(current_user: UserResponse = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def create_password_reset_token(email: str):
    """ Génère un token JWT pour la réinitialisation de mot de passe (valide 15 min). """
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_password_reset_token(token: str):
    """ Vérifie le token JWT et extrait l'email. """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None