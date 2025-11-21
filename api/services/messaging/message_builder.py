# api/services/messaging/message_builder.py
"""
Orchestrateur pour le Message Builder.
Gère preview, création de campagne, materialization et queue des messages.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
from bson import ObjectId
import logging

from api.core.settings import settings
from api.databases.databases import get_core_db, get_bi_db
from api.schemas.message_builder import (
    CampaignCreate, PreviewOut, PreviewOutItem, CampaignOut, SegmentationRule, Platform
)
from api.services.messaging.template_engine import render_template
from api.services.messaging.segmentation import build_targets

logger = logging.getLogger(__name__)


async def _load_template(org_id: str, template_id: str) -> Dict[str, Any]:
    """
    Charge un template depuis la base de données.
    
    Args:
        org_id: ID de l'organisation
        template_id: ID du template
        
    Returns:
        Document template
        
    Raises:
        ValueError: Si template non trouvé
    """
    db = get_core_db()
    
    try:
        doc = await db["message_templates"].find_one({
            "org_id": org_id,
            "_id": ObjectId(template_id)
        })
    except Exception:
        # Si ObjectId invalide
        doc = None
    
    if not doc:
        raise ValueError("Template not found")
    
    return doc


def _variables_from_target(
    target: Dict[str, Any],
    tracking: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extrait les variables depuis une cible pour le rendu du template.
    
    Args:
        target: Données de la cible
        tracking: Paramètres de tracking optionnels
        
    Returns:
        Dictionnaire de variables
    """
    variables = {
        "first_name": target.get("first_name") or "",
        "avg_spend": target.get("avg_spend") or 0.0,
        "total_spent": target.get("total_spent") or 0.0,
        "last_purchase_at": target.get("last_purchase_at"),
        "last_active_at": target.get("last_active_at"),
    }
    
    if tracking:
        variables["tracking"] = tracking
    
    return variables


async def _maybe_inject_tracking(
    org_id: str,
    body: str,
    vars: Dict[str, Any],
    tracking_params: Optional[Dict[str, Any]],
    user_ref: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Injecte un lien traqué dans les variables si destination_url est présent dans tracking_params.
    
    Args:
        org_id: ID de l'organisation
        body: Corps du template
        vars: Variables actuelles
        tracking_params: Paramètres de tracking
        user_ref: Référence utilisateur (si disponible)
        
    Returns:
        Tuple (body, vars) potentiellement modifiés
    """
    if not tracking_params or "destination_url" not in tracking_params:
        return body, vars
    
    try:
        from api.services.tracking.link_service import ensure_tracked_url
        
        # Ajouter user_ref au contexte si disponible
        context = tracking_params.copy()
        if user_ref:
            context["user_ref"] = user_ref
        
        tracked = await ensure_tracked_url(
            org_id=org_id,
            destination_url=tracking_params["destination_url"],
            context=context
        )
        
        # Exposer dans les variables
        vars["tracking"] = tracked  # {short_url, code, ...}
        
    except Exception as e:
        logger.warning(f"Error injecting tracking link: {e}")
        # On continue sans tracking si échec
    
    return body, vars


def _make_dedupe(org_id: str, campaign_id: str, user_ref: str) -> str:
    """
    Crée une clé de déduplication.
    
    Args:
        org_id: ID de l'organisation
        campaign_id: ID de la campagne
        user_ref: Référence utilisateur
        
    Returns:
        Clé de déduplication
    """
    return f"{org_id}:{campaign_id}:{user_ref}"


async def preview_campaign(payload: CampaignCreate) -> PreviewOut:
    """
    Génère un preview d'une campagne (messages rendus pour quelques cibles).
    
    Args:
        payload: Requête de campagne
        
    Returns:
        Preview avec messages rendus
        
    Raises:
        RuntimeError: Si feature disabled
        ValueError: Si template non trouvé
    """
    if not settings.feature_message_builder_enabled:
        raise RuntimeError("Message builder disabled")
    
    # Charger le template
    template = await _load_template(payload.org_id, payload.template_id)
    
    # Construire les cibles
    targets, total = await build_targets(
        payload.org_id,
        payload.segmentation,
        payload.platform
    )
    
    # Limiter pour preview
    max_preview = settings.mb_max_targets_preview
    targets_preview = targets[:max_preview]
    
    items: List[PreviewOutItem] = []
    
    for target in targets_preview:
        # Extraire les variables
        variables = _variables_from_target(target, payload.tracking_params)
        
        # Injecter le tracking si nécessaire
        body_rendered, variables = await _maybe_inject_tracking(
            payload.org_id,
            template["body"],
            variables,
            payload.tracking_params,
            target.get("user_ref")
        )
        
        # Rendre le template
        try:
            rendered = render_template(body_rendered, variables)
        except Exception as e:
            logger.warning(f"Error rendering template for {target['user_ref']}: {e}")
            rendered = f"[ERROR: {str(e)}]"
        
        items.append(PreviewOutItem(
            user_ref=target["user_ref"],
            platform=target["platform"],
            variables=variables,
            rendered=rendered
        ))
    
    return PreviewOut(
        items=items,
        count_total=total,
        truncated=(total > max_preview)
    )


async def create_campaign(payload: CampaignCreate) -> CampaignOut:
    """
    Crée une campagne.
    
    Args:
        payload: Requête de création
        
    Returns:
        Campagne créée
    """
    if not settings.feature_message_builder_enabled:
        raise RuntimeError("Message builder disabled")
    
    db = get_core_db()
    now = datetime.now(timezone.utc)
    
    doc = {
        "org_id": payload.org_id,
        "name": payload.name,
        "template_id": payload.template_id,
        "platform": payload.platform,
        "segmentation": payload.segmentation.model_dump(),
        "status": "scheduled" if payload.scheduled_at else "draft",
        "totals": {
            "targets": 0,
            "queued": 0,
            "sent": 0,
            "failed": 0
        },
        "scheduled_at": payload.scheduled_at,
        "created_at": now,
        "updated_at": now,
        "tracking_params": payload.tracking_params or {}
    }
    
    result = await db["campaigns"].insert_one(doc)
    doc["id"] = str(result.inserted_id)
    
    return CampaignOut(**doc)


async def materialize_targets(campaign_id: str) -> int:
    """
    Matérialise les cibles d'une campagne (insère dans campaign_targets).
    
    Args:
        campaign_id: ID de la campagne
        
    Returns:
        Nombre de cibles matérialisées
        
    Raises:
        ValueError: Si campagne non trouvée
    """
    db = get_core_db()
    
    try:
        camp = await db["campaigns"].find_one({"_id": ObjectId(campaign_id)})
    except Exception:
        camp = None
    
    if not camp:
        raise ValueError("Campaign not found")
    
    org_id = camp["org_id"]
    
    # Charger le template pour validation
    await _load_template(org_id, camp["template_id"])
    
    # Construire les cibles
    rule = SegmentationRule(**camp["segmentation"])
    platform: Platform = camp["platform"]
    
    targets, total = await build_targets(org_id, rule, platform)
    
    # Limiter par MB_MAX_TARGETS_SEND
    if total > settings.mb_max_targets_send:
        targets = targets[:settings.mb_max_targets_send]
        logger.warning(
            f"Campaign {campaign_id}: targets limited from {total} to {settings.mb_max_targets_send}"
        )
    
    # Insérer dans campaign_targets (avec déduplication)
    docs = []
    for target in targets:
        docs.append({
            "campaign_id": str(camp["_id"]),
            "org_id": org_id,
            "user_ref": target["user_ref"],
            "platform": target["platform"],
            "vars": _variables_from_target(target, camp.get("tracking_params")),
            "created_at": datetime.now(timezone.utc),
        })
    
    if docs:
        # Utiliser ordered=False pour ignorer les doublons
        try:
            await db["campaign_targets"].insert_many(docs, ordered=False)
        except Exception as e:
            # Certains documents peuvent déjà exister (déduplication)
            logger.warning(f"Some campaign_targets already exist: {e}")
            # Insérer un par un pour ignorer les doublons
            inserted = 0
            for doc in docs:
                try:
                    await db["campaign_targets"].insert_one(doc)
                    inserted += 1
                except Exception:
                    # Doublon, ignorer
                    pass
            count = inserted
        else:
            count = len(docs)
    else:
        count = 0
    
    # Mettre à jour le total dans la campagne
    await db["campaigns"].update_one(
        {"_id": camp["_id"]},
        {
            "$set": {
                "totals.targets": count,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return count


async def queue_messages(campaign_id: str) -> int:
    """
    Met les messages en queue (outbox_messages) pour envoi.
    
    Args:
        campaign_id: ID de la campagne
        
    Returns:
        Nombre de messages mis en queue
        
    Raises:
        ValueError: Si campagne non trouvée
    """
    db = get_core_db()
    
    try:
        camp = await db["campaigns"].find_one({"_id": ObjectId(campaign_id)})
    except Exception:
        camp = None
    
    if not camp:
        raise ValueError("Campaign not found")
    
    org_id = camp["org_id"]
    
    # Charger le template
    template = await _load_template(org_id, camp["template_id"])
    body = template["body"]
    
    # Itérer sur les cibles et créer les messages dans l'outbox
    cursor = db["campaign_targets"].find({"campaign_id": str(camp["_id"])})
    
    queued = 0
    scheduled_at = camp.get("scheduled_at") or datetime.now(timezone.utc)
    
    async for target in cursor:
        # Variables de base
        vars_current = target["vars"].copy()
        
        # Injecter le tracking si nécessaire
        body_rendered, vars_current = await _maybe_inject_tracking(
            org_id,
            body,
            vars_current,
            camp.get("tracking_params"),
            target.get("user_ref")
        )
        
        # Rendre le template
        try:
            rendered = render_template(body_rendered, vars_current)
        except Exception as e:
            logger.error(f"Error rendering message for {target['user_ref']}: {e}")
            continue
        
        # Clé de déduplication
        dedupe = _make_dedupe(org_id, str(camp["_id"]), target["user_ref"])
        
        doc = {
            "org_id": org_id,
            "campaign_id": str(camp["_id"]),
            "user_ref": target["user_ref"],
            "platform": target["platform"],
            "message": rendered,
            "status": "queued",
            "scheduled_at": scheduled_at,
            "created_at": datetime.now(timezone.utc),
            "dedupe_key": dedupe
        }
        
        try:
            await db["outbox_messages"].insert_one(doc)
            queued += 1
        except Exception:
            # Doublon (dedupe_key unique), ignorer
            pass
    
    # Mettre à jour la campagne
    await db["campaigns"].update_one(
        {"_id": camp["_id"]},
        {
            "$set": {
                "totals.queued": queued,
                "status": "running",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Émettre événement analytics
    from api.services.analytics.events import emit_campaign_event
    try:
        await emit_campaign_event(org_id, str(camp["_id"]), "queued", queued)
    except Exception as e:
        logger.warning(f"Error emitting campaign event: {e}")
    
    return queued
