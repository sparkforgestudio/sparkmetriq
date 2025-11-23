# api/schemas/collab.py
"""
Schémas Pydantic pour le module de collaboration interne.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime


MessageRole = Literal["operator", "supervisor", "admin", "system"]
TaskStatus = Literal["todo", "in_progress", "blocked", "done", "archived"]
Priority = Literal["low", "medium", "high", "urgent"]


class CollabThreadCreate(BaseModel):
    """Requête de création de thread."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    title: str = Field(
        ...,
        description="Titre du thread"
    )
    muse_id: Optional[str] = Field(
        None,
        description="ID de la muse (optionnel)"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags du thread"
    )


class CollabThreadOut(BaseModel):
    """Réponse de thread."""
    
    id: str = Field(
        ...,
        description="ID du thread"
    )
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    title: str = Field(
        ...,
        description="Titre du thread"
    )
    muse_id: Optional[str] = Field(
        None,
        description="ID de la muse"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags"
    )
    created_by: str = Field(
        ...,
        description="Email de l'auteur"
    )
    created_at: datetime = Field(
        ...,
        description="Date de création"
    )
    updated_at: datetime = Field(
        ...,
        description="Date de mise à jour"
    )
    last_message_preview: Optional[str] = Field(
        None,
        description="Aperçu du dernier message"
    )
    unread_count: int = Field(
        0,
        description="Nombre de messages non lus"
    )


class CollabMessageCreate(BaseModel):
    """Requête de création de message."""
    
    thread_id: str = Field(
        ...,
        description="ID du thread"
    )
    body: str = Field(
        ...,
        description="Corps du message"
    )
    mentions: List[str] = Field(
        default_factory=list,
        description="Mentions (@emails ou user_ids)"
    )
    attachments: List[str] = Field(
        default_factory=list,
        description="URLs des pièces jointes"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées supplémentaires"
    )


class CollabMessageOut(BaseModel):
    """Réponse de message."""
    
    id: str = Field(
        ...,
        description="ID du message"
    )
    thread_id: str = Field(
        ...,
        description="ID du thread"
    )
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    author: str = Field(
        ...,
        description="Email de l'auteur"
    )
    role: MessageRole = Field(
        ...,
        description="Rôle de l'auteur"
    )
    body: str = Field(
        ...,
        description="Corps du message"
    )
    mentions: List[str] = Field(
        default_factory=list,
        description="Mentions"
    )
    attachments: List[str] = Field(
        default_factory=list,
        description="Pièces jointes"
    )
    created_at: datetime = Field(
        ...,
        description="Date de création"
    )


class CollabTaskCreate(BaseModel):
    """Requête de création de tâche."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    title: str = Field(
        ...,
        description="Titre de la tâche"
    )
    description: Optional[str] = Field(
        None,
        description="Description"
    )
    assignees: List[str] = Field(
        default_factory=list,
        description="Assignés (emails ou user_ids)"
    )
    status: TaskStatus = Field(
        "todo",
        description="Statut de la tâche"
    )
    priority: Priority = Field(
        "medium",
        description="Priorité"
    )
    due_at: Optional[datetime] = Field(
        None,
        description="Date d'échéance"
    )
    related_muse_id: Optional[str] = Field(
        None,
        description="ID de la muse liée"
    )
    related_thread_id: Optional[str] = Field(
        None,
        description="ID du thread lié"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags"
    )
    external_sync: Optional[Literal["clickup", "notion"]] = Field(
        None,
        description="Intégration externe optionnelle"
    )


class CollabTaskOut(BaseModel):
    """Réponse de tâche."""
    
    id: str = Field(
        ...,
        description="ID de la tâche"
    )
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    title: str = Field(
        ...,
        description="Titre"
    )
    description: Optional[str] = Field(
        None,
        description="Description"
    )
    assignees: List[str] = Field(
        default_factory=list,
        description="Assignés"
    )
    status: TaskStatus = Field(
        ...,
        description="Statut"
    )
    priority: Priority = Field(
        ...,
        description="Priorité"
    )
    due_at: Optional[datetime] = Field(
        None,
        description="Date d'échéance"
    )
    related_muse_id: Optional[str] = Field(
        None,
        description="ID de la muse liée"
    )
    related_thread_id: Optional[str] = Field(
        None,
        description="ID du thread lié"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags"
    )
    created_by: str = Field(
        ...,
        description="Email du créateur"
    )
    created_at: datetime = Field(
        ...,
        description="Date de création"
    )
    updated_at: datetime = Field(
        ...,
        description="Date de mise à jour"
    )
    external_ref: Optional[Dict[str, Any]] = Field(
        None,
        description="Référence externe (ClickUp/Notion)"
    )


class CollabTaskUpdate(BaseModel):
    """Requête de mise à jour de tâche."""
    
    title: Optional[str] = Field(
        None,
        description="Titre"
    )
    description: Optional[str] = Field(
        None,
        description="Description"
    )
    assignees: Optional[List[str]] = Field(
        None,
        description="Assignés"
    )
    status: Optional[TaskStatus] = Field(
        None,
        description="Statut"
    )
    priority: Optional[Priority] = Field(
        None,
        description="Priorité"
    )
    due_at: Optional[datetime] = Field(
        None,
        description="Date d'échéance"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Tags"
    )


class CollabStatsOut(BaseModel):
    """Statistiques de collaboration."""
    
    org_id: str = Field(
        ...,
        description="ID de l'organisation"
    )
    open_tasks: int = Field(
        ...,
        description="Nombre de tâches ouvertes"
    )
    overdue_tasks: int = Field(
        ...,
        description="Nombre de tâches en retard"
    )
    by_status: Dict[str, int] = Field(
        ...,
        description="Répartition par statut"
    )
    by_assignee: List[Dict[str, Any]] = Field(
        ...,
        description="Répartition par assigné"
    )
    by_priority: Dict[str, int] = Field(
        ...,
        description="Répartition par priorité"
    )




