# api/routes/message_builder.py
"""
Routes REST pour le système Message Builder (Mass DM + Variables dynamiques).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List
from bson import ObjectId
from datetime import datetime, timezone

from api.core.settings import settings
from api.schemas.users import UserResponse
from api.core.auth import get_current_user
from api.schemas.message_builder import (
    MessageTemplateIn, MessageTemplateOut, CampaignCreate, CampaignOut,
    PreviewOut, SendRequest, CampaignStatusOut
)
from api.databases.databases import get_core_db
from api.services.messaging.message_builder import (
    preview_campaign, create_campaign, materialize_targets, queue_messages
)
from api.services.messaging.template_engine import validate_template
from api.services.observability.activity import log_message_builder_action

router = APIRouter(prefix="/message-builder", tags=["Message Builder"])


def _ensure_enabled():
    """Vérifie que le feature flag est activé."""
    if not settings.feature_message_builder_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Message builder disabled"
        )


@router.post("/templates", response_model=MessageTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: MessageTemplateIn,
    current_user: UserResponse = Depends(get_current_user)
) -> MessageTemplateOut:
    """
    Crée un template de message.
    
    Args:
        payload: Requête de création
        current_user: Utilisateur actuel
        
    Returns:
        Template créé
    """
    _ensure_enabled()
    
    # Vérifier la longueur
    if len(payload.body) > settings.mb_template_max_chars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template too long (max {settings.mb_template_max_chars} chars)"
        )
    
    # Valider le template (syntaxe + liens)
    is_valid, error_msg = validate_template(payload.body, settings.mb_allow_links)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    db = get_core_db()
    now = datetime.now(timezone.utc)
    
    doc = {
        "org_id": payload.org_id,
        "name": payload.name,
        "body": payload.body,
        "variables_hint": payload.variables_hint or [],
        "meta": payload.meta or {},
        "created_at": now,
        "updated_at": now
    }
    
    try:
        result = await db["message_templates"].insert_one(doc)
        doc["id"] = str(result.inserted_id)
    except Exception as e:
        # Probablement un doublon (unique index sur org_id+name)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Template name already exists: {str(e)}"
        )
    
    await log_message_builder_action(
        payload.org_id,
        getattr(current_user, "email", "system"),
        "create_template",
        "success",
        payload.name
    )
    
    return MessageTemplateOut(**doc)


@router.get("/templates", response_model=List[MessageTemplateOut])
async def list_templates(
    org_id: str = Query(..., description="ID de l'organisation"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[MessageTemplateOut]:
    """
    Liste les templates d'une organisation.
    
    Args:
        org_id: ID de l'organisation
        current_user: Utilisateur actuel
        
    Returns:
        Liste des templates
    """
    _ensure_enabled()
    
    db = get_core_db()
    cursor = (
        db["message_templates"]
        .find({"org_id": org_id})
        .sort("updated_at", -1)
        .limit(100)
    )
    
    docs = await cursor.to_list(length=100)
    
    out = []
    for d in docs:
        d["id"] = str(d["_id"])
        del d["_id"]
        out.append(MessageTemplateOut(**d))
    
    return out


@router.post("/preview", response_model=PreviewOut, status_code=status.HTTP_200_OK)
async def preview(
    payload: CampaignCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> PreviewOut:
    """
    Génère un preview d'une campagne (messages rendus pour quelques cibles).
    
    Args:
        payload: Requête de campagne (dry_run peut être True)
        current_user: Utilisateur actuel
        
    Returns:
        Preview avec messages rendus
    """
    _ensure_enabled()
    
    try:
        res = await preview_campaign(payload)
        await log_message_builder_action(
            payload.org_id,
            getattr(current_user, "email", "system"),
            "preview",
            "success",
            payload.name
        )
        return res
    except Exception as e:
        await log_message_builder_action(
            payload.org_id,
            getattr(current_user, "email", "system"),
            "preview",
            "failed",
            str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/campaigns", response_model=CampaignOut, status_code=status.HTTP_201_CREATED)
async def create_campaign_route(
    payload: CampaignCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> CampaignOut:
    """
    Crée une campagne.
    
    Args:
        payload: Requête de création
        current_user: Utilisateur actuel
        
    Returns:
        Campagne créée
    """
    _ensure_enabled()
    
    try:
        camp = await create_campaign(payload)
        await log_message_builder_action(
            payload.org_id,
            getattr(current_user, "email", "system"),
            "create_campaign",
            "success",
            payload.name
        )
        return camp
    except Exception as e:
        await log_message_builder_action(
            payload.org_id,
            getattr(current_user, "email", "system"),
            "create_campaign",
            "failed",
            str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/campaigns/{campaign_id}/materialize", response_model=CampaignStatusOut)
async def materialize(
    campaign_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> CampaignStatusOut:
    """
    Matérialise les cibles d'une campagne.
    
    Args:
        campaign_id: ID de la campagne
        current_user: Utilisateur actuel
        
    Returns:
        Statut de la campagne
    """
    _ensure_enabled()
    
    try:
        n = await materialize_targets(campaign_id)
        await log_message_builder_action(
            "n/a",
            getattr(current_user, "email", "system"),
            "materialize_targets",
            "success",
            str(n)
        )
        
        db = get_core_db()
        try:
            camp = await db["campaigns"].find_one({"_id": ObjectId(campaign_id)})
        except Exception:
            camp = None
        
        if not camp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return CampaignStatusOut(
            id=str(camp["_id"]),
            status=camp["status"],
            totals=camp.get("totals", {})
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        await log_message_builder_action(
            "n/a",
            getattr(current_user, "email", "system"),
            "materialize_targets",
            "failed",
            str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/campaigns/{campaign_id}/queue", response_model=CampaignStatusOut)
async def queue(
    campaign_id: str,
    req: SendRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> CampaignStatusOut:
    """
    Met les messages en queue pour envoi.
    
    Args:
        campaign_id: ID de la campagne
        req: Requête d'envoi (confirm requis)
        current_user: Utilisateur actuel
        
    Returns:
        Statut de la campagne
    """
    _ensure_enabled()
    
    if not req.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="confirm=true required for queue operation"
        )
    
    try:
        n = await queue_messages(campaign_id)
        await log_message_builder_action(
            "n/a",
            getattr(current_user, "email", "system"),
            "queue_messages",
            "success",
            str(n)
        )
        
        db = get_core_db()
        try:
            camp = await db["campaigns"].find_one({"_id": ObjectId(campaign_id)})
        except Exception:
            camp = None
        
        if not camp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return CampaignStatusOut(
            id=str(camp["_id"]),
            status=camp["status"],
            totals=camp.get("totals", {})
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        await log_message_builder_action(
            "n/a",
            getattr(current_user, "email", "system"),
            "queue_messages",
            "failed",
            str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/campaigns/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> CampaignOut:
    """
    Récupère une campagne.
    
    Args:
        campaign_id: ID de la campagne
        current_user: Utilisateur actuel
        
    Returns:
        Campagne trouvée
    """
    _ensure_enabled()
    
    db = get_core_db()
    try:
        camp = await db["campaigns"].find_one({"_id": ObjectId(campaign_id)})
    except Exception:
        camp = None
    
    if not camp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    camp["id"] = str(camp["_id"])
    del camp["_id"]
    
    return CampaignOut(**camp)



