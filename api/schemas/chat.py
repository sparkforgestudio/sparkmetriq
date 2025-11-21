from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    """
    Schéma pour envoyer un message à l'IA via /chat/send ou webhook
    """
    conversation_id: Optional[str] = Field(
        None,
        description="ID de la conversation existante, ou None pour en démarrer une nouvelle"
    )
    platform: Optional[str] = Field(
        None,
        description="Nom de la plateforme source (ex. 'telegram', 'instagram', etc.)"
    )
    user_id: Optional[str] = Field(
        None,
        description="Identifiant de l'utilisateur sur la plateforme"
    )
    message: str = Field(
        ...,  # message obligatoire
        description="Contenu du message à envoyer à l'IA"
    )
    attachments: Optional[List[str]] = Field(
        None,
        description="URLs des pièces jointes (images, fichiers, etc.)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Données additionnelles (ex. contexte UX, préférences, etc.)"
    )


class ChatMessageOut(BaseModel):
    """
    Réponse de l'IA pour un seul message
    """
    conversation_id: str = Field(
        ...,  # toujours renvoyé
        description="ID de la conversation associée"
    )
    message: str = Field(
        ...,  # texte de la réponse
        description="Texte de la réponse générée par l'IA"
    )
    attachments: Optional[List[str]] = Field(
        None,
        description="URLs des pièces jointes (images, fichiers, etc.)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Horodatage UTC du message"
    )


class ChatHistory(BaseModel):
    """
    Historique paginé d'une conversation
    """
    conversation_id: str = Field(
        ...,  # identifiant de la conversation
        description="ID de la conversation"
    )
    skip: int = Field(
        0, ge=0,
        description="Nombre de messages à ignorer (offset)"
    )
    limit: int = Field(
        50, ge=1, le=200,
        description="Nombre maximal de messages retournés"
    )
    total: int = Field(
        ...,  # total des messages
        ge=0,
        description="Nombre total de messages dans la conversation"
    )
    messages: List[ChatMessageOut] = Field(
        ...,  # liste des messages
        description="Liste des messages (ordre chronologique ascendant)"
    )
