from pydantic import BaseModel, Field, EmailStr
from typing import Literal
from datetime import datetime
from bson import ObjectId

class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: Literal["USDT", "ETH", "BTC"] = "USDT"
    description: str
    muse_id: str  # Identifiant de la muse ou le token de configuration du bot

class PaymentResponse(BaseModel):
    payment_url: str

# 🔹 Utilitaire pour convertir les ObjectId MongoDB
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# 🔹 Modèle de base pour création
class PaymentBase(BaseModel):
    email: EmailStr
    muse_id: str = Field(..., example="muse123")
    amount: float = Field(..., gt=0)
    currency: Literal["USDT", "ETH", "BTC"] = "USDT"
    invoice_id: str = Field(..., example="invoice_abc123")
    status: Literal["pending", "paid", "failed"] = "pending"
    created_at: Optional[datetime] = None

# 🔹 Modèle de retour pour les API
class PaymentResponse(PaymentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "muse_id": "muse123",
                "amount": 29.99,
                "currency": "USDT",
                "invoice_id": "abc123xyz",
                "status": "paid",
                "created_at": "2025-04-04T11:45:00Z"
            }
        }

# 🔹 Modèle pour mise à jour éventuelle
class PaymentUpdate(BaseModel):
    status: Optional[Literal["pending", "paid", "failed"]] = None