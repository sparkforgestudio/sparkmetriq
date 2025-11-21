from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional, List


# 🔹 Rôles utilisateur possibles
class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    moderator = "moderator"


# 🔹 Schéma de réponse d'un utilisateur
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    org_id: str  # Organisation/tenant ID pour multi-tenancy
    is_admin: bool
    roles: List[UserRole] = []

    class Config:
        from_attributes = True


# 🔹 Création d'utilisateur
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False


# 🔹 Connexion utilisateur
class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True


# 🔹 Mise à jour des rôles
class UserRoleUpdate(BaseModel):
    role: UserRole


# 🔹 Mise à jour utilisateur (profil)
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None


# 🔹 Mise à jour mot de passe
class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str


# 🔹 Demande de réinitialisation
class PasswordResetRequest(BaseModel):
    email: EmailStr


# 🔹 Confirmation de réinitialisation
class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# 🔹 Token JWT
class Token(BaseModel):
    access_token: str
    token_type: str
