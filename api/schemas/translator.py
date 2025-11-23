# api/schemas/translator.py
"""
Schémas Pydantic pour le système de traduction IA.
"""

from pydantic import BaseModel, Field, constr
from typing import Optional, Literal, Dict, Any, List


# Types de ton, emoji et formalité
Tone = Literal["neutral", "flirt", "respectful", "playful"]
EmojiLevel = Literal["none", "low", "medium", "high"]
Formality = Literal["casual", "standard", "formal"]


class TranslateIn(BaseModel):
    """Requête de traduction."""
    
    text: constr(min_length=1) = Field(
        ...,
        description="Texte original à traduire"
    )
    source_lang: Optional[str] = Field(
        None,
        description="Langue source ISO-639-1 (auto-détection si None)"
    )
    target_lang: str = Field(
        ...,
        description="Langue cible ISO-639-1 (ex: 'en', 'fr', 'de')"
    )
    tone: Tone = Field(
        "neutral",
        description="Ton de réécriture (neutral|flirt|respectful|playful)"
    )
    emoji: EmojiLevel = Field(
        "medium",
        description="Niveau d'emojis (none|low|medium|high)"
    )
    formality: Formality = Field(
        "standard",
        description="Niveau de formalité (casual|standard|formal)"
    )
    # Contexte optionnel
    org_id: Optional[str] = Field(
        None,
        description="ID de l'organisation"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="ID de la conversation"
    )
    platform: Optional[str] = Field(
        None,
        description="Plateforme (instagram, telegram, etc.)"
    )
    user_role: Optional[Literal["fan", "operator", "bot"]] = Field(
        None,
        description="Rôle de l'utilisateur"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Métadonnées supplémentaires"
    )


class TranslateOut(BaseModel):
    """Réponse de traduction."""
    
    source_lang: str = Field(
        ...,
        description="Langue source détectée ou fournie"
    )
    target_lang: str = Field(
        ...,
        description="Langue cible"
    )
    original: str = Field(
        ...,
        description="Texte original"
    )
    translated: str = Field(
        ...,
        description="Texte traduit"
    )
    rewritten: str = Field(
        ...,
        description="Texte réécrit avec le ton/style/emojis"
    )
    quality: Optional[str] = Field(
        None,
        description="Qualité de la traduction (ok, needs_review)"
    )
    tokens_used: Optional[int] = Field(
        None,
        description="Nombre de tokens utilisés"
    )
    extras: Optional[Dict[str, Any]] = Field(
        None,
        description="Informations supplémentaires"
    )


class BatchTranslateIn(BaseModel):
    """Requête de traduction par lot."""
    
    items: List[TranslateIn] = Field(
        ...,
        description="Liste des requêtes de traduction"
    )


class BatchTranslateOut(BaseModel):
    """Réponse de traduction par lot."""
    
    items: List[TranslateOut] = Field(
        ...,
        description="Liste des traductions"
    )




