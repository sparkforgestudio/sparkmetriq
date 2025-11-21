from fastapi import APIRouter, Depends, HTTPException
from typing import List
from api.databases.databases import db
from api.core.auth import get_current_user, is_admin
from api.core.permissions import has_role
from api.schemas.users import (
    UserResponse,
    UserUpdate,
    UserPasswordUpdate,
    UserRole,
    UserRoleUpdate
)
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔹 Récupérer ses propres informations
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user

# 🔹 Récupérer la liste des utilisateurs (modérateurs et admins uniquement)
@router.get("/", response_model=List[UserResponse])
async def get_users(current_user: UserResponse = Depends(has_role(UserRole.moderator))):
    users = await db["users"].find().to_list(100)
    # Map documents to UserResponse models
    return [UserResponse(email=u["email"], is_admin=u.get("is_admin", False)) for u in users]

# 🔹 Supprimer un utilisateur (admins uniquement)
@router.delete("/{email}")
async def delete_user(
    email: str,
    admin_user: UserResponse = Depends(has_role(UserRole.admin))
):
    result = await db["users"].delete_one({"email": email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {email} deleted successfully"}

# 🔹 Modifier le rôle d'un utilisateur (admins uniquement)
@router.put("/{email}/role")
async def update_user_role(
    email: str,
    role_update: UserRoleUpdate,
    admin_user: UserResponse = Depends(has_role(UserRole.admin))
):
    if role_update.role not in UserRole.__members__.values():
        raise HTTPException(status_code=400, detail="Invalid role")
    result = await db["users"].update_one(
        {"email": email}, {"$set": {"role": role_update.role}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {email} role updated to {role_update.role}"}

# 🔹 Mettre à jour son propre profil
@router.put("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    await db["users"].update_one(
        {"email": current_user.email}, {"$set": update_data}
    )
    updated = await db["users"].find_one({"email": current_user.email})
    return UserResponse(email=updated["email"], is_admin=updated.get("is_admin", False))

# 🔹 Changer son mot de passe
@router.put("/me/password")
async def change_password(
    password_data: UserPasswordUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    user = await db["users"].find_one({"email": current_user.email})
    if not pwd_context.verify(password_data.old_password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    new_hashed = pwd_context.hash(password_data.new_password)
    await db["users"].update_one(
        {"email": current_user.email}, {"$set": {"password": new_hashed}}
    )
    return {"message": "Password updated successfully"}
