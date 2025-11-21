import httpx
from typing import Dict, Any, Optional
from api.services.content_distributor.logger import logger, log_step, log_platform_event
from api.core.configs import META_ACCESS_TOKEN, THREADS_USER_ID
from api.core.configs import SECRET_KEY, ALGORITHM

GRAPH_API_URL = "https://graph.facebook.com/v19.0"

@log_step
async def publish_to_threads(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu sur Threads via l'API officielle Meta (Graph API).
    """
    agency_id: str = model_info.get("agency_id", "")
    muse_id: str = model_info.get("muse_id", "")
    content_id: str = content.get("id", "")

    caption: str = content.get("text", "")
    media_list: Optional[Any] = content.get("media")
    image_url: Optional[str] = media_list[0]["url"] if media_list else None

    try:
        async with httpx.AsyncClient() as client:
            # Étape 1 : Création du conteneur media
            media_endpoint = f"{GRAPH_API_URL}/{THREADS_USER_ID}/media"
            media_resp = await client.post(
                media_endpoint,
                params={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": META_ACCESS_TOKEN
                }
            )
            media_data = media_resp.json()
            if media_resp.status_code != 200 or "id" not in media_data:
                error_msg = media_data.get("error", media_data)
                await log_platform_event(
                    platform="threads",
                    agency_id=agency_id,
                    muse_id=muse_id,
                    content_id=content_id,
                    status="error",
                    message=f"Erreur création media: {error_msg}",
                    metadata={"media_url": image_url}
                )
                return {"status": "error", "details": error_msg}

            creation_id = media_data["id"]

            # Étape 2 : Publication du conteneur
            publish_endpoint = f"{GRAPH_API_URL}/{THREADS_USER_ID}/media_publish"
            publish_resp = await client.post(
                publish_endpoint,
                params={"creation_id": creation_id, "access_token": META_ACCESS_TOKEN}
            )
            publish_data = publish_resp.json()

            if publish_resp.status_code == 200:
                await log_platform_event(
                    platform="threads",
                    agency_id=agency_id,
                    muse_id=muse_id,
                    content_id=content_id,
                    status="success",
                    message="Publication réussie sur Threads",
                    metadata={"creation_id": creation_id}
                )
                return {"status": "success", "data": publish_data}
            else:
                error_msg = publish_data.get("error", publish_data)
                await log_platform_event(
                    platform="threads",
                    agency_id=agency_id,
                    muse_id=muse_id,
                    content_id=content_id,
                    status="error",
                    message=f"Erreur publication: {error_msg}",
                    metadata={"creation_id": creation_id}
                )
                return {"status": "error", "details": error_msg}

    except Exception as e:
        await log_platform_event(
            platform="threads",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="error",
            message="Exception lors de la publication sur Threads",
            metadata={"exception": str(e)}
        )
        logger.error(f"Exception publish_to_threads: {e}")
        return {"status": "error", "exception": str(e)}
