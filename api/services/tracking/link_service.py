# api/services/tracking/link_service.py
"""
Service de création et gestion des liens traqués.
"""

import secrets
import string
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId

from api.core.settings import settings
from api.databases.databases import get_core_db
from api.schemas.tracking import LinkCreate

CORE = get_core_db()


def _gen_code(n: int) -> str:
    """
    Génère un code aléatoire pour le lien court.
    
    Args:
        n: Longueur du code
        
    Returns:
        Code généré
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


async def create_link(payload: LinkCreate) -> Dict[str, Any]:
    """
    Crée un lien traqué.
    
    Args:
        payload: Requête de création
        
    Returns:
        Lien créé avec short_url
        
    Raises:
        RuntimeError: Si feature disabled
    """
    if not settings.feature_link_tracking_enabled:
        raise RuntimeError("Link tracking disabled")
    
    # Générer un code unique
    max_attempts = 10
    code = None
    for _ in range(max_attempts):
        candidate = _gen_code(settings.track_code_length)
        existing = await CORE["tracking_links"].find_one({"code": candidate})
        if not existing:
            code = candidate
            break
    
    if not code:
        raise RuntimeError("Failed to generate unique code")
    
    # Construire le dictionnaire UTM
    utm = {}
    if payload.utm_source:
        utm["utm_source"] = payload.utm_source
    if payload.utm_medium:
        utm["utm_medium"] = payload.utm_medium
    if payload.utm_campaign:
        utm["utm_campaign"] = payload.utm_campaign
    if payload.utm_content:
        utm["utm_content"] = payload.utm_content
    
    # Construire le document
    doc = {
        "org_id": payload.org_id,
        "muse_id": payload.muse_id,
        "code": code,
        "destination_url": str(payload.destination_url),
        "utm": utm,
        "campaign_id": payload.campaign_id,
        "promo_code": payload.promo_code,
        "created_at": datetime.now(timezone.utc),
        "expires_at": payload.expires_at,
        "max_clicks": payload.max_clicks,
        "clicks_total": 0,
        "meta": payload.meta or {},
    }
    
    # Insérer dans la base
    result = await CORE["tracking_links"].insert_one(doc)
    
    # Construire l'URL courte
    short_url = f"{settings.tracking_domain_base}/r/{code}"
    
    doc["_id"] = result.inserted_id
    doc["id"] = str(result.inserted_id)
    doc["short_url"] = short_url
    
    return doc


async def ensure_tracked_url(
    org_id: str,
    destination_url: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Helper pour Message Builder : crée un lien court avec UTM + campaign + user_ref.
    
    Args:
        org_id: ID de l'organisation
        destination_url: URL de destination
        context: Contexte (utm_source, campaign_id, user_ref, etc.)
        
    Returns:
        Lien traqué créé (ou existant si logique de déduplication)
    """
    # Construire le payload depuis le contexte
    payload = LinkCreate(
        org_id=org_id,
        destination_url=destination_url,
        utm_source=context.get("utm_source"),
        utm_medium=context.get("utm_medium"),
        utm_campaign=context.get("utm_campaign") or context.get("campaign_id"),
        utm_content=context.get("utm_content"),
        campaign_id=context.get("campaign_id"),
        promo_code=context.get("promo_code"),
        muse_id=context.get("muse_id")
    )
    
    # Créer le lien
    link = await create_link(payload)
    
    # Option: ajouter user_ref en query param si présent
    if context.get("user_ref"):
        link["short_url"] = f"{link['short_url']}?u={context['user_ref']}"
    
    return link



