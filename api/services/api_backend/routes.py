from fastapi import APIRouter, HTTPException
from services.api_backend.database import database
from services.api_backend.models import UserModel

router = APIRouter()

@router.post("/users/", response_model=UserModel)
async def create_user(user: UserModel):
    user_dict = user.dict(exclude={"id"})
    result = await database["users"].insert_one(user_dict)
    user.id = str(result.inserted_id)
    return user

@router.get("/users/{user_id}", response_model=UserModel)
async def get_user(user_id: str):
    user = await database["users"].find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserModel(**user)
