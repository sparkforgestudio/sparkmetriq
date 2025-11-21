# api/services/tracking/redirect_service.py
"""
Service de redirection et log des clics.
"""

import hashlib
import urllib.parse
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from api.core.settings import settings
from api.databases.databases import get_core_db

CORE = get_core_db()


def _hash_ip(ip: str) -> str:
    """
    Hash l'IP pour la sécurité (pas de stockage en clair).
    
    Args:
        ip: Adresse IP
        
    Returns:
        Hash de l'IP
    """
    salt = settings.click_ip_hash_salt.encode()
    return hashlib.sha256(salt + ip.encode()).hexdigest()[:32]


async def resolve_and_log(
    code: str,
    user_ref: Optional[str] = None,
    ip: str = "",
    ua: str = "",
    ref: str = "",
    q: Optional[Dict[str, Any]] = None
) -> str:
    """
    Résout un code de lien, log le clic et retourne l'URL de destination finale.
    
    Args:
        code: Code du lien court
        user_ref: Référence utilisateur (optionnel, peut aussi venir de query)
        ip: Adresse IP du client
        ua: User agent
        ref: Referrer
        q: Paramètres de query (dict)
        
    Returns:
        URL de destination finale avec UTM préservés
        
    Raises:
        LookupError: Si lien non trouvé
        PermissionError: Si lien expiré ou quota atteint
    """
    # Récupérer le lien
    link = await CORE["tracking_links"].find_one({"code": code})
    if not link:
        raise LookupError("Link not found")
    
    # Vérifier expiration
    now = datetime.now(timezone.utc)
    if link.get("expires_at") and now > link["expires_at"]:
        raise PermissionError("Link expired")
    
    # Vérifier quota de clics
    if link.get("max_clicks") and link.get("clicks_total", 0) >= link["max_clicks"]:
        raise PermissionError("Max clicks reached")
    
    # Extraire user_ref depuis query si non fourni
    if not user_ref and q and q.get("u"):
        user_ref = q.get("u")
    
    # Log du clic
    utm = link.get("utm") or {}
    rec = {
        "org_id": link["org_id"],
        "code": code,
        "campaign_id": link.get("campaign_id"),
        "utm": utm,
        "ts": now,
        "ip_hash": _hash_ip(ip) if ip else None,
        "ua": (ua[:512] if ua else None),
        "ref": (ref[:512] if ref else None),
        "user_ref": user_ref,
    }
    
    await CORE["tracking_clicks"].insert_one(rec)
    
    # Incrémenter le compteur de clics
    await CORE["tracking_links"].update_one(
        {"_id": link["_id"]},
        {"$inc": {"clicks_total": 1}}
    )
    
    # Construire l'URL de destination finale avec UTM préservés
    dest = link["destination_url"]
    parsed = urllib.parse.urlparse(dest)
    params = dict(urllib.parse.parse_qsl(parsed.query))
    
    # Ajouter les UTM si pas déjà présents
    for k, v in utm.items():
        params.setdefault(k, v)
    
    # Propager promo_code si présent
    if link.get("promo_code"):
        params.setdefault("promo", link["promo_code"])
    
    # Propager user_ref si présent (pour deep links)
    if user_ref:
        params.setdefault("uid", user_ref)
    
    # Reconstruire l'URL
    dest_final = urllib.parse.urlunparse(
        parsed._replace(query=urllib.parse.urlencode(params))
    )
    
    return dest_final



