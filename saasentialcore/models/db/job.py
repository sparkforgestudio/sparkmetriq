"""
Modèle de base de données pour les jobs du scheduler.

Ce module définit la structure des documents job dans MongoDB.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class JobDB(BaseModel):
    """
    Modèle de document job en base de données.
    
    Structure MongoDB :
    {
        "_id": ObjectId,
        "job_id": str,
        "org_id": str,
        "status": str,
        "scheduled_at": datetime,
        "payload": dict,
        "attempt": int,
        "max_attempts": int,
        "last_error": str,
        "created_at": datetime,
        "updated_at": datetime
    }
    """
    
    id: str = Field(..., alias="_id", description="ID MongoDB du job")
    job_id: str = Field(..., description="ID unique du job")
    org_id: str = Field(..., description="ID de l'organisation")
    status: str = Field(..., description="Statut du job (PENDING, RUNNING, SUCCESS, FAILED)")
    scheduled_at: datetime = Field(..., description="Date/heure de planification")
    payload: Dict[str, Any] = Field(..., description="Payload du job")
    attempt: int = Field(default=0, description="Nombre de tentatives")
    max_attempts: int = Field(default=3, description="Nombre maximum de tentatives")
    last_error: Optional[str] = Field(default=None, description="Dernière erreur rencontrée")
    next_run_at: Optional[datetime] = Field(default=None, description="Prochaine exécution (pour retries)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date de création")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Date de mise à jour")
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "job_id": "job_abc123",
                "org_id": "org_123",
                "status": "PENDING",
                "scheduled_at": "2024-01-01T12:00:00Z",
                "payload": {"action": "publish", "content_id": "content_456"},
                "attempt": 0,
                "max_attempts": 3,
                "last_error": None,
                "next_run_at": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )

