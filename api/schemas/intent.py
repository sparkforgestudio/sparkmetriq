# api/schemas/intent.py
"""
Schémas Pydantic pour le Moteur d'Intentions.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


# ---------- Persona & Branding ----------
class PersonaToneProfile(BaseModel):
    """Profil de ton pour la persona."""
    
    emoji_ratio: float = Field(
        0.2,
        ge=0.0,
        le=1.0,
        description="Ratio d'utilisation d'emojis (0.0 = aucun, 1.0 = beaucoup)"
    )
    avg_sentence_length: int = Field(
        12,
        ge=5,
        le=50,
        description="Longueur moyenne des phrases"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Mots-clés représentatifs du style"
    )
    do: List[str] = Field(
        default_factory=list,
        description="Ce qu'il faut faire (règles de style)"
    )
    dont: List[str] = Field(
        default_factory=list,
        description="Ce qu'il ne faut pas faire (interdictions)"
    )


class PersonaProfile(BaseModel):
    """Profil de persona pour une muse."""
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    tone_profile: PersonaToneProfile = Field(..., description="Profil de ton")
    brand_boosters: List[str] = Field(
        default_factory=list,
        description="Règles de branding courtes (snippets prioritaires)"
    )


# ---------- Knowledge Chunks ----------
class KnowledgeChunk(BaseModel):
    """Fragment de connaissance pour le RAG."""
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    kind: Literal["dm_history", "caption", "prompt_history", "brand_doc"] = Field(
        ...,
        description="Type de connaissance"
    )
    text: str = Field(..., description="Contenu du fragment")
    weight: float = Field(
        1.0,
        ge=0.0,
        description="Poids pour le scoring (brand_doc doit avoir poids supérieur)"
    )
    ts: Optional[datetime] = Field(
        None,
        description="Timestamp (pour tri temporel)"
    )


# ---------- Policies ----------
class ChatPolicies(BaseModel):
    """Politiques de chat pour une muse."""
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    ppv_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Règles PPV (max_per_day, cooldown_minutes, etc.)"
    )
    compliance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Règles de conformité (forbidden_words, nsfw_level, etc.)"
    )
    latency_profiles: Dict[str, Any] = Field(
        default_factory=dict,
        description="Profils de latence (typing, min_ms, max_ms)"
    )


# ---------- Scenarios ----------
class ScenarioStep(BaseModel):
    """Étape d'un scénario."""
    
    id: str = Field(..., description="ID unique de l'étape")
    type: Literal["message", "ppv_offer", "wait", "tag_fan", "media"] = Field(
        ...,
        description="Type d'étape"
    )
    template: Optional[str] = Field(
        None,
        description="Template de message (pour type message/ppv_offer)"
    )
    use_llm_tone: bool = Field(
        True,
        description="Utiliser le LLM pour styliser le template"
    )
    delay_s: int = Field(
        0,
        ge=0,
        description="Délai en secondes avant l'exécution"
    )
    condition: Optional[Dict[str, Any]] = Field(
        None,
        description="Conditions d'exécution (optionnel)"
    )
    actions_on_send: List[str] = Field(
        default_factory=list,
        description="Actions à effectuer lors de l'envoi (tag_fan, track_event, etc.)"
    )


class ScenarioTrigger(BaseModel):
    """Déclencheur d'un scénario."""
    
    type: Literal["dm_received", "comment_created", "story_mention", "reaction"] = Field(
        ...,
        description="Type de déclencheur"
    )
    conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Conditions supplémentaires (filtres texte, fan_id, etc.)"
    )


class ChatScenario(BaseModel):
    """Scénario de conversation."""
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    title: str = Field(..., description="Titre du scénario")
    version: int = Field(
        1,
        ge=1,
        description="Version du scénario"
    )
    is_active: bool = Field(
        True,
        description="Scénario actif"
    )
    platforms: List[str] = Field(
        ...,
        description="Plateformes supportées (instagram, tiktok, telegram, etc.)"
    )
    trigger: ScenarioTrigger = Field(..., description="Déclencheur du scénario")
    steps: List[ScenarioStep] = Field(..., description="Étapes du scénario")
    policy_refs: List[str] = Field(
        default_factory=list,
        description="Références aux politiques à appliquer"
    )


# ---------- Sessions ----------
class ChatSession(BaseModel):
    """Session de conversation en cours."""
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    conversation_id: str = Field(..., description="ID de la conversation")
    scenario_id: str = Field(..., description="ID du scénario en cours")
    current_step: str = Field(..., description="ID de l'étape actuelle")
    status: Literal["in_progress", "completed", "aborted"] = Field(
        "in_progress",
        description="Statut de la session"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contexte additionnel (variables, fan info, etc.)"
    )
    platform: str = Field(..., description="Plateforme utilisée")


# ---------- Dispatch IO ----------
class InboundEvent(BaseModel):
    """Événement entrant à traiter."""
    
    org_id: str = Field(..., description="ID de l'organisation")
    muse_id: str = Field(..., description="ID de la muse")
    platform: Literal["instagram", "tiktok", "telegram", "onlyfans", "reddit", "x"] = Field(
        ...,
        description="Plateforme source"
    )
    conversation_id: str = Field(..., description="ID de la conversation")
    fan_id: Optional[str] = Field(
        None,
        description="ID du fan (si disponible)"
    )
    type: Literal["dm_received", "comment_created", "story_mention", "reaction"] = Field(
        ...,
        description="Type d'événement"
    )
    text: Optional[str] = Field(
        None,
        description="Texte du message/commentaire"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )


class OutboundMessage(BaseModel):
    """Message sortant à envoyer."""
    
    conversation_id: str = Field(..., description="ID de la conversation")
    text: str = Field(..., description="Texte du message")
    platform: str = Field(..., description="Plateforme cible")
    attachments: Optional[List[str]] = Field(
        None,
        description="URLs ou IDs des pièces jointes"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )


# ---------- Execution Mode toggle ----------
class ConversationModePatch(BaseModel):
    """Requête pour forcer le mode d'exécution."""
    
    mode: Literal["llm_pilot", "scenario_guided"] = Field(
        ...,
        description="Mode d'exécution souhaité"
    )




