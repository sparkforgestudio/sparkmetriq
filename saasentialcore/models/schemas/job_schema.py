"""
Schémas Pydantic pour les jobs du scheduler.

Ce module définit les schémas de validation et de sérialisation
pour les requêtes et réponses liées aux jobs.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """
    Schéma pour la création d'un job.
    """
    org_id: str = Field(..., description="ID de l'organisation")
    scheduled_at: datetime = Field(..., description="Date/heure de planification")
    payload: Dict[str, Any] = Field(..., description="Payload du job")
    max_attempts: int = Field(default=3, ge=1, le=10, description="Nombre maximum de tentatives")


class JobUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'un job.
    """
    scheduled_at: Optional[datetime] = Field(default=None, description="Nouvelle date/heure de planification")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Nouveau payload")
    max_attempts: Optional[int] = Field(default=None, ge=1, le=10, description="Nouveau nombre maximum de tentatives")


class JobResponse(BaseModel):
    """
    Schéma de réponse pour un job.
    """
    id: str = Field(..., description="ID MongoDB du job")
    job_id: str = Field(..., description="ID unique du job")
    org_id: str = Field(..., description="ID de l'organisation")
    status: str = Field(..., description="Statut du job")
    scheduled_at: datetime = Field(..., description="Date/heure de planification")
    payload: Dict[str, Any] = Field(..., description="Payload du job")
    attempt: int = Field(..., description="Nombre de tentatives")
    max_attempts: int = Field(..., description="Nombre maximum de tentatives")
    last_error: Optional[str] = Field(default=None, description="Dernière erreur")
    next_run_at: Optional[datetime] = Field(default=None, description="Prochaine exécution")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")

