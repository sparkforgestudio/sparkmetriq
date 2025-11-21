# api/routes/intent.py
"""
Routes FastAPI pour le Moteur d'Intentions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from api.core.auth import get_current_user
from api.schemas.users import UserResponse
from api.schemas.intent import (
    InboundEvent, ChatScenario, ConversationModePatch,
    PersonaProfile, KnowledgeChunk, ChatPolicies
)
from api.services.intent.intent_engine import IntentEngine
from api.databases.databases import get_core_db

router = APIRouter(prefix="/intent", tags=["Intent Engine"])

# Instance globale du moteur
engine = IntentEngine()


@router.post("/event")
async def inbound_event(
    ev: InboundEvent,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Traite un événement entrant (DM, commentaire, etc.).
    
    Args:
        ev: Événement entrant
        current_user: Utilisateur actuel
        
    Returns:
        Résultat du traitement
    """
    # Vérification multi-tenant
    if ev.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: org_id mismatch"
        )
    
    try:
        result = await engine.handle_inbound(ev)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du traitement: {str(e)}"
        )


@router.post("/scenarios", status_code=status.HTTP_201_CREATED)
async def create_scenario(
    payload: ChatScenario,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Crée un nouveau scénario.
    
    Args:
        payload: Scénario à créer
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation de création
    """
    if payload.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: org_id mismatch"
        )
    
    db = get_core_db()
    
    try:
        await db["chat_scenarios"].insert_one(payload.model_dump())
        return {"ok": True, "scenario_title": payload.title}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )


@router.get("/scenarios", status_code=status.HTTP_200_OK)
async def list_scenarios(
    muse_id: str = None,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Liste les scénarios pour une organisation/muse.
    
    Args:
        muse_id: ID de la muse (optionnel, filtre)
        current_user: Utilisateur actuel
        
    Returns:
        Liste des scénarios
    """
    db = get_core_db()
    org_id = current_user.org_id
    
    query = {"org_id": org_id}
    if muse_id:
        query["muse_id"] = muse_id
    
    try:
        cursor = db["chat_scenarios"].find(query)
        scenarios = await cursor.to_list(length=None)
        
        return {
            "ok": True,
            "items": scenarios,
            "count": len(scenarios)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )


@router.patch("/conversations/{conversation_id}/mode", status_code=status.HTTP_200_OK)
async def set_mode(
    conversation_id: str,
    body: ConversationModePatch,
    muse_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Force le mode d'exécution pour une conversation.
    
    Args:
        conversation_id: ID de la conversation
        body: Mode souhaité
        muse_id: ID de la muse
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation
    """
    org_id = current_user.org_id
    
    try:
        result = await engine.set_conversation_mode(
            org_id, muse_id, conversation_id, body.mode
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


@router.post("/persona", status_code=status.HTTP_200_OK)
async def upsert_persona(
    body: PersonaProfile,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Crée ou met à jour un profil de persona.
    
    Args:
        body: Profil de persona
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation
    """
    if body.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: org_id mismatch"
        )
    
    db = get_core_db()
    
    try:
        await db["persona_profiles"].update_one(
            {"org_id": body.org_id, "muse_id": body.muse_id},
            {"$set": body.model_dump()},
            upsert=True
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la sauvegarde: {str(e)}"
        )


@router.post("/knowledge", status_code=status.HTTP_201_CREATED)
async def add_knowledge(
    chunk: KnowledgeChunk,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Ajoute un chunk de connaissance.
    
    Args:
        chunk: Chunk de connaissance
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation
    """
    if chunk.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: org_id mismatch"
        )
    
    db = get_core_db()
    
    try:
        chunk_dict = chunk.model_dump()
        if not chunk_dict.get("ts"):
            from datetime import datetime, timezone
            chunk_dict["ts"] = datetime.now(timezone.utc)
        
        await db["knowledge_chunks"].insert_one(chunk_dict)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'ajout: {str(e)}"
        )


@router.post("/policies", status_code=status.HTTP_200_OK)
async def upsert_policies(
    pol: ChatPolicies,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Crée ou met à jour les politiques de chat.
    
    Args:
        pol: Politiques
        current_user: Utilisateur actuel
        
    Returns:
        Confirmation
    """
    if pol.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: org_id mismatch"
        )
    
    db = get_core_db()
    
    try:
        await db["chat_policies"].update_one(
            {"org_id": pol.org_id, "muse_id": pol.muse_id},
            {"$set": pol.model_dump()},
            upsert=True
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la sauvegarde: {str(e)}"
        )



