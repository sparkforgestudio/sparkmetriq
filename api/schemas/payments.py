from pydantic import BaseModel, Field, EmailStr, HttpUrl, ConfigDict
from typing import Literal, Optional
from datetime import datetime, timezone
from bson import ObjectId

# ── Paiement fiat-to-crypto via carte (on-ramp)
class PaymentRequest(BaseModel):
    """Requête de paiement."""
    amount: float = Field(..., gt=0, description="Montant du paiement")
    currency: Literal["USDT", "ETH", "BTC"] = Field(default="USDT", description="Devise crypto")
    description: str = Field(..., description="Description du paiement")
    muse_id: str = Field(..., description="Identifiant de la muse")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "amount": 29.99,
                    "currency": "USDT",
                    "description": "Abonnement Premium",
                    "muse_id": "muse123"
                }
            ]
        }
    )

class PaymentResponse(BaseModel):
    """Réponse de paiement."""
    payment_url: HttpUrl

# ── Utilitaire pour les ObjectId MongoDB
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
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {'type': 'string'}

# ── Modèles internes de paiement (MongoDB)
class PaymentBase(BaseModel):
    """Base pour les modèles de paiement."""
    email: EmailStr = Field(..., description="Email du client")
    muse_id: str = Field(..., description="Identifiant de la muse")
    amount: float = Field(..., gt=0, description="Montant du paiement")
    currency: Literal["USDT", "ETH", "BTC"] = Field(default="USDT", description="Devise crypto")
    invoice_id: str = Field(..., description="ID de la facture")
    status: Literal["pending", "paid", "failed"] = Field(default="pending", description="Statut du paiement")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date de création")
    
    model_config = ConfigDict(from_attributes=True)

class PaymentOut(PaymentBase):
    """Modèle de sortie pour les paiements."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "_id": "64f8a0b5e5d3c2a1b2c3d4e5",
                    "email": "user@example.com",
                    "muse_id": "muse123",
                    "amount": 29.99,
                    "currency": "USDT",
                    "invoice_id": "abc123xyz",
                    "status": "paid",
                    "created_at": "2025-04-04T11:45:00Z"
                }
            ]
        }
    )

class PaymentUpdate(BaseModel):
    """Modèle pour mettre à jour un paiement."""
    status: Optional[Literal["pending", "paid", "failed"]] = Field(None, description="Nouveau statut")

# ── Schémas NowPayments (crypto on-ramp)
class CryptoOnrampRequest(BaseModel):
    """Requête d'on-ramp crypto."""
    price_amount: float = Field(..., description="Montant en devise fiat")
    price_currency: Optional[str] = Field(default="EUR", description="Devise fiat")
    pay_currency: Optional[str] = Field(default="USDT", description="Devise crypto à recevoir")
    order_id: Optional[str] = Field(None, description="ID de commande")
    callback_url: Optional[HttpUrl] = Field(None, description="URL de callback")

class CryptoOnrampResponse(BaseModel):
    """Réponse d'on-ramp crypto."""
    id: str = Field(..., description="ID de la transaction")
    payment_id: str = Field(..., description="ID du paiement")
    pay_address: str = Field(..., description="Adresse de réception")
    pay_amount: float = Field(..., description="Montant à payer")
    pay_currency: str = Field(..., description="Devise à payer")
    invoice_url: HttpUrl = Field(..., description="URL de la facture")

class CryptoWebhookPayload(BaseModel):
    """Payload du webhook crypto."""
    payment_id: str = Field(..., description="ID du paiement")
    order_id: Optional[str] = Field(None, description="ID de commande")
    status: str = Field(..., description="Statut du paiement")
    pay_amount: float = Field(..., description="Montant payé")
    pay_currency: str = Field(..., description="Devise payée")
    price_amount: float = Field(..., description="Montant en devise fiat")
    price_currency: str = Field(..., description="Devise fiat")
