from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from api.core.auths import create_access_token
from services.database import db
from schemas.user import UserCreate, UserLogin, Token
from passlib.context import CryptContext
from datetime import timedelta

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Fonction pour hacher les mots de passe
def hash_password(password: str):
    return pwd_context.hash(password)

# Vérifier le mot de passe
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 📌 Route d'inscription
@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    existing_user = await db["users"].find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(user_data.password)
    new_user = {
        "email": user_data.email,
        "password": hashed_password,
        "is_admin": user_data.is_admin
    }

    await db["users"].insert_one(new_user)
    access_token = create_access_token(data={"sub": user_data.email}, expires_delta=timedelta(hours=1))
    return {"access_token": access_token, "token_type": "bearer"}

# 📌 Route de connexion
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db["users"].find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user["email"]}, expires_delta=timedelta(hours=1))
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(data: PasswordResetConfirm):
    email = verify_reset_token(data.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    hashed_password = pwd_context.hash(data.new_password)
    await db["users"].update_one({"email": email}, {"$set": {"password": hashed_password}})
    
    return {"message": "Password reset successfully"}

# 🔹 Demande de réinitialisation (envoi email avec lien)
@router.post("/password-reset")
async def request_password_reset(data: PasswordResetRequest):
    user = await db["users"].find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    token = create_password_reset_token(data.email)
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    
    # Envoyer l'email
    await send_password_reset_email(data.email, reset_link)

    return {"message": "Email de réinitialisation envoyé"}

# 🔹 Réinitialisation du mot de passe (via le token)
@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm):
    email = verify_password_reset_token(data.token)
    if not email:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")

    new_hashed_password = pwd_context.hash(data.password)
    result = await db["users"].update_one({"email": email}, {"$set": {"password": new_hashed_password}})
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    
    return {"message": "Mot de passe mis à jour avec succès"}