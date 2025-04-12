from fastapi import APIRouter, HTTPException, Depends
from services.database import db
from core.security import hash_password, verify_password, create_access_token
from datetime import timedelta
from schemas.payments import PaymentRequest, PaymentResponse
from api.services.payment_gateway.cryptobot import generate_payment_link
from core.auths import get_current_user
from schemas.users import UserResponse

router = APIRouter()

@router.get("/", response_model=list)
async def get_payments(current_user: str = Depends(get_current_user)):
    payments = await db["payments"].find().to_list(100)
    return payments

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

@router.post("/create", response_model=PaymentResponse)
async def create_payment_link(
    payment_request: PaymentRequest,
    user: UserResponse = Depends(get_current_user)
):
    try:
        payment_link = await generate_payment_link(payment_request, user)
        return PaymentResponse(payment_url=payment_link)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
