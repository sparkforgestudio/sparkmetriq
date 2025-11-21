# api/schemas/recap.py
"""
Schémas Pydantic pour le système de résumé IA des conversations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


RecapKind = Literal["full", "delta"]  # full = recap global, delta = résumé incrémental


class RecapGenerateIn(BaseModel):
    """Requête de génération de recap."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    conversation_id: str = Field(
        ...,
        description="ID de la conversation"
    )
    muse_id: Optional[str] = Field(
        None,
        description="ID de la muse"
    )
    user_id: Optional[str] = Field(
        None,
        description="ID de l'utilisateur/fan"
    )
    kind: RecapKind = Field(
        "full",
        description="Type de recap (full ou delta)"
    )
    since_ts: Optional[datetime] = Field(
        None,
        description="Timestamp depuis lequel générer le recap (pour delta)"
    )
    max_messages: int = Field(
        200,
        description="Nombre maximum de messages à traiter"
    )
    include_examples: bool = Field(
        False,
        description="Inclure des exemples dans le prompt pour le style"
    )


class RecapStructured(BaseModel):
    """Structure du recap généré."""
    
    summary: str = Field(
        ...,
        description="Résumé général de la conversation"
    )
    preferences: List[str] = Field(
        default_factory=list,
        description="Préférences du fan identifiées"
    )
    objections: List[str] = Field(
        default_factory=list,
        description="Objections soulevées"
    )
    purchases: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Achats/PPV mentionnés (ex: [{'item': 'PPV custom video', 'amount': 25}])"
    )
    sensitive_topics: List[str] = Field(
        default_factory=list,
        description="Sujets sensibles abordés"
    )
    next_actions: List[str] = Field(
        default_factory=list,
        description="Actions suggérées pour la suite"
    )
    recommended_tone: Optional[str] = Field(
        None,
        description="Ton recommandé pour la suite de la conversation"
    )


class RecapOut(BaseModel):
    """Réponse de recap."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    conversation_id: str = Field(
        ...,
        description="ID de la conversation"
    )
    muse_id: Optional[str] = Field(
        None,
        description="ID de la muse"
    )
    user_id: Optional[str] = Field(
        None,
        description="ID de l'utilisateur/fan"
    )
    last_message_ts: Optional[datetime] = Field(
        None,
        description="Timestamp du dernier message traité"
    )
    window: Dict[str, Any] = Field(
        default_factory=dict,
        description="Fenêtre de messages analysés (kind, since_ts, count)"
    )
    structured: RecapStructured = Field(
        ...,
        description="Structure du recap"
    )
    tokens_used: Optional[int] = Field(
        None,
        description="Nombre de tokens utilisés"
    )
    version: str = Field(
        "v1",
        description="Version du format de recap"
    )
    updated_at: datetime = Field(
        ...,
        description="Date de mise à jour"
    )


class RecapItem(BaseModel):
    """Item de liste de recaps."""
    
    id: str = Field(
        ...,
        description="ID du recap"
    )
    conversation_id: str = Field(
        ...,
        description="ID de la conversation"
    )
    updated_at: datetime = Field(
        ...,
        description="Date de mise à jour"
    )
    last_message_ts: Optional[datetime] = Field(
        None,
        description="Timestamp du dernier message"
    )
    kind: RecapKind = Field(
        "full",
        description="Type de recap"
    )


class RecapListOut(BaseModel):
    """Liste de recaps."""
    
    items: List[RecapItem] = Field(
        ...,
        description="Liste des recaps"
    )



