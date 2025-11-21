from fastapi import APIRouter, HTTPException, Depends
from api.databases.databases import db
from core.security import hash_password, verify_password, create_access_token
from datetime import timedelta
from core.auth import get_current_user, is_admin

router = APIRouter()

@router.get("/", response_model=list)
async def get_bots(current_user: str = Depends(get_current_user)):
    bots = await db["bots"].find().to_list(100)
    return bots

@router.post("/register", response_model=dict)
async def register_user(user: dict):
    user["password"] = hash_password(user["password"])
    result = await db["users"].insert_one(user)
    return {"id": str(result.inserted_id)}

@router.post("/login", response_model=dict)
async def login_user(user: dict):
    db_user = await db["users"].find_one({"email": user["email"]})
    if not db_user or not verify_password(user["password"], db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": db_user["email"]}, expires_delta=timedelta(hours=1))
    return {"access_token": token, "token_type": "bearer"}
