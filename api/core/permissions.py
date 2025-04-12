from fastapi import Depends, HTTPException
from core.auths import get_current_user
from schemas.users import UserResponse, UserRole

def has_role(required_role: UserRole):
    def role_checker(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker
