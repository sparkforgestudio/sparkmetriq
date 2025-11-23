# api/services/tracking/attribution_service.py
"""
Service d'attribution des revenus aux sources de trafic.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from api.core.settings import settings
from api.databases.databases import get_core_db, get_bi_db

CORE = get_core_db()
BI = get_bi_db()


async def attribute_payment(
    org_id: str,
    user_ref: str,
    amount: float,
    ts: datetime
) -> Dict[str, Any]:
    """
    Attribue un paiement à une source de trafic selon le modèle d'attribution.
    
    Modèles :
    - last_touch : prend le dernier clic avant le paiement
    - first_touch : prend le premier clic historisé
    
    Args:
        org_id: ID de l'organisation
        user_ref: Référence utilisateur (fan)
        amount: Montant du paiement
        ts: Timestamp du paiement
        
    Returns:
        Attribution créée
    """
    model = settings.attribution_model
    
    # Chercher le clic pertinent selon le modèle
    query = {
        "org_id": org_id,
        "user_ref": user_ref,
        "ts": {"$lte": ts}
    }
    
    # Trier selon le modèle
    if model == "last_touch":
        sort = [("ts", -1)]  # Plus récent d'abord
    else:  # first_touch
        sort = [("ts", 1)]  # Plus ancien d'abord
    
    click = await CORE["tracking_clicks"].find_one(query, sort=sort)
    
    # Si pas de clic connu, on attribue à "direct/none"
    if click:
        source = click["utm"].get("utm_source", "direct")
        medium = click["utm"].get("utm_medium", "none")
        campaign = click["utm"].get("utm_campaign")
        content = click["utm"].get("utm_content")
    else:
        source = "direct"
        medium = "none"
        campaign = None
        content = None
    
    # Créer l'enregistrement d'attribution
    attrib = {
        "org_id": org_id,
        "day": ts.date().isoformat(),
        "ts": ts,
        "amount": float(amount),
        "source": source,
        "medium": medium,
        "campaign": campaign,
        "content": content,
        "user_ref": user_ref,
        "model": model,
        "created_at": datetime.now(timezone.utc)
    }
    
    await BI["revenue_attribution_daily"].insert_one(attrib)
    
    return attrib




