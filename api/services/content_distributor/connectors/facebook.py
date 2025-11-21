import httpx
from typing import Dict, Any
from api.core.configs import SECRET_KEY, ALGORITHM
from api.services.content_distributor.logger import logger, log_step, log_platform_event

@log_step
async def publish_to_facebook(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie un post texte ou image sur une page Facebook via Graph API et journalise l'événement.

    :param content: Contenu à publier. Doit contenir 'caption' et optionnellement 'media_url'.
    :param model_info: Doit contenir 'page_id' et 'page_access_token', ainsi que facultativement 'agency_id' et 'muse_id'.

    :return: Dictionnaire de statut avec données ou erreur.
    """
    page_id = model_info.get("page_id")
    access_token = model_info.get("page_access_token")
    agency_id = model_info.get("agency_id", "")
    muse_id = model_info.get("muse_id", "")
    content_id = content.get("id", "")

    if not page_id or not access_token:
        raise ValueError("page_id et page_access_token sont requis dans model_info.")

    message = content.get("caption", "")
    media_url = content.get("media_url")

    try:
        if media_url:
            # Publication d'une photo
            url = f"https://graph.facebook.com/{page_id}/photos"
            params = {"url": media_url, "caption": message, "access_token": access_token}
        else:
            # Publication d'un post texte
            url = f"https://graph.facebook.com/{page_id}/feed"
            params = {"message": message, "access_token": access_token}

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, params=params)

        if resp.status_code == 200:
            data = resp.json()
            await log_platform_event(
                platform="facebook",
                agency_id=agency_id,
                muse_id=muse_id,
                content_id=content_id,
                status="success",
                message="Publication Facebook réussie",
                metadata={"response": data}
            )
            return {"status": "success", "data": data}
        else:
            error_text = resp.text
            await log_platform_event(
                platform="facebook",
                agency_id=agency_id,
                muse_id=muse_id,
                content_id=content_id,
                status="error",
                message="Erreur publication Facebook",
                metadata={"status_code": resp.status_code, "error": error_text}
            )
            return {"status": "error", "code": resp.status_code, "error": error_text}

    except Exception as e:
        await log_platform_event(
            platform="facebook",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="error",
            message=str(e),
            metadata={}
        )
        logger.error(f"Erreur publish_to_facebook: {e}")
        return {"status": "error", "reason": str(e)}
