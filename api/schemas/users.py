from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional

# 🔹 Définition des rôles possibles
class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    moderator = "moderator"

# 🔹 Réponse utilisateur incluant le rôle
class UserResponse(BaseModel):
    email: EmailStr
    role: UserRole

# 🔹 Mise à jour de rôle
class UserRoleUpdate(BaseModel):
    role: UserRole
    
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    email: EmailStr
    is_admin: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

# 🔹 Réponse utilisateur (sécurisée)
class UserResponse(BaseModel):
    email: EmailStr
    is_admin: bool

# 🔹 Mise à jour utilisateur (optionnel)
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# 🔹 Mise à jour mot de passe
class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str

from pydantic import BaseModel, EmailStr

# 🔹 Demande de réinitialisation
class PasswordResetRequest(BaseModel):
    email: EmailStr

# 🔹 Confirmation de réinitialisation
class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
