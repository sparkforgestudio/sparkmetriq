from pydantic import BaseModel, EmailStr
from typing import Optional

class UserInDB(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "user"  # Par défaut, tous les utilisateurs sont "user"
