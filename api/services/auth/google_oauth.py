# api/services/auth/google_oauth.py
"""
Service pour l'authentification Google OAuth 2.0.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

try:
    from google.auth.transport import requests
    from google.oauth2 import id_token
    GOOGLE_OAUTH_AVAILABLE = True
except ImportError:
    GOOGLE_OAUTH_AVAILABLE = False
    logging.warning("google-auth not installed. Google OAuth will not work.")

from api.databases.databases import get_core_db
from api.core.configs import GOOGLE_CLIENT_ID

logger = logging.getLogger(__name__)


async def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """Vérifie un token Google ID et retourne les informations utilisateur.
    
    Args:
        token: Token ID Google à vérifier.
        
    Returns:
        Dict avec les informations utilisateur Google (sub, email, name, etc.)
        ou None si le token est invalide.
        
    Raises:
        ValueError: Si google-auth n'est pas installé.
    """
    if not GOOGLE_OAUTH_AVAILABLE:
        raise ValueError("google-auth package not installed. Install with: pip install google-auth")
    
    if not GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID not configured in environment variables")
        raise ValueError("GOOGLE_CLIENT_ID not configured in environment variables")
    
    try:
        # Vérifier le token avec Google
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        # Vérifier que le token vient de Google
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        logger.info(f"Google token verified for user: {idinfo.get('email')}")
        return idinfo
        
    except ValueError as e:
        logger.warning(f"Invalid Google token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error verifying Google token: {str(e)}")
        return None


async def get_or_create_google_user(google_info: Dict[str, Any], org_id: Optional[str] = None) -> Dict[str, Any]:
    """Récupère ou crée un utilisateur à partir des informations Google.
    
    Args:
        google_info: Informations utilisateur depuis Google (résultat de verify_google_token).
        org_id: ID de l'organisation (optionnel, généré si absent).
        
    Returns:
        Dict avec les données utilisateur (id, email, google_id, etc.).
        
    Raises:
        ValueError: Si l'email est manquant dans google_info.
    """
    if not google_info.get('email'):
        raise ValueError("Email not found in Google token")
    
    db_instance = get_core_db()
    google_id = google_info.get('sub')
    email = google_info.get('email')
    name = google_info.get('name', '')
    picture = google_info.get('picture')
    
    # Chercher un utilisateur existant par email ou google_id
    existing_user = await db_instance["users"].find_one({
        "$or": [
            {"email": email},
            {"google_id": google_id}
        ]
    })
    
    if existing_user:
        # Mettre à jour si nécessaire (google_id manquant, ou info mise à jour)
        update_data = {}
        if not existing_user.get('google_id') and google_id:
            update_data['google_id'] = google_id
        if name and existing_user.get('name') != name:
            update_data['name'] = name
        if picture and existing_user.get('picture') != picture:
            update_data['picture'] = picture
        if org_id and not existing_user.get('org_id'):
            update_data['org_id'] = org_id
        
        if update_data:
            update_data['updated_at'] = datetime.now(timezone.utc)
            await db_instance["users"].update_one(
                {"_id": existing_user["_id"]},
                {"$set": update_data}
            )
            existing_user.update(update_data)
        
        existing_user["id"] = str(existing_user.pop("_id"))
        logger.info(f"Google user found: {email}")
        return existing_user
    
    # Créer un nouvel utilisateur
    # Générer org_id si non fourni (pour MVP, utiliser email hash ou générer UUID)
    if not org_id:
        import hashlib
        org_id = hashlib.sha256(email.encode()).hexdigest()[:16]
    
    new_user = {
        "email": email,
        "google_id": google_id,
        "name": name,
        "picture": picture,
        "org_id": org_id,
        "is_admin": False,
        "auth_provider": "google",
        "password": None,  # Pas de mot de passe pour OAuth
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    result = await db_instance["users"].insert_one(new_user)
    new_user["id"] = str(result.inserted_id)
    logger.info(f"Google user created: {email}, org_id={org_id}")
    
    return new_user
