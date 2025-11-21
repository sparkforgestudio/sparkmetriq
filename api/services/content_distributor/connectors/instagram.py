import httpx
import os
from datetime import datetime
from typing import Dict, Any, Optional

from api.services.content_distributor.logger import logger, log_platform_event, log_step

INSTAGRAM_TOKEN = os.getenv("INSTAGRAM_GRAPH_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
GRAPH_URL = "https://graph.facebook.com/v18.0"

async def upload_instagram_photo(image_url: str, caption: str) -> Dict[str, Any]:
    """
    Upload d'une photo sur Instagram via l'API Graph.
    """
    async with httpx.AsyncClient() as client:
        # Étape 1: créer le conteneur média
        create_url = f"{GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
        create_resp = await client.post(
            create_url,
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": INSTAGRAM_TOKEN
            }
        )
        create_data = create_resp.json()
        if "id" not in create_data:
            raise Exception(f"Erreur création média Instagram : {create_data}")

        creation_id = create_data["id"]
        # Étape 2: publier le conteneur
        publish_url = f"{GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        publish_resp = await client.post(
            publish_url,
            params={"creation_id": creation_id, "access_token": INSTAGRAM_TOKEN}
        )
        return publish_resp.json()

@log_step
async def publish_to_instagram(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu sur Instagram et log l'événement.
    """
    image_url = content.get("media_url")
    caption = content.get("text", "")
    agency_id = model_info.get("agency_id")
    muse_id = model_info.get("muse_id")
    content_id = content.get("id") or content.get("content_id")
    try:
        response = await upload_instagram_photo(image_url, caption)
        # Log de l'événement réussie
        await log_platform_event(
            platform="instagram",
            agency_id=agency_id or "",
            muse_id=muse_id or "",
            content_id=content_id or "",
            status="success",
            message="Publication Instagram réussie",
            metadata={"response": response}
        )
        return {"status": "success", "platform_response": response}
    except Exception as e:
        # Log de l'erreur
        await log_platform_event(
            platform="instagram",
            agency_id=agency_id or "",
            muse_id=muse_id or "",
            content_id=content_id or "",
            status="error",
            message=str(e),
            metadata={}
        )
        logger.error(f"Publication Instagram échouée : {e}")
        return {"status": "error", "reason": str(e)}
