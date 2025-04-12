import requests
from services.content_distributor.logger import logger, log_step, log_platform_event
from core.configs import META_ACCESS_TOKEN, THREADS_USER_ID

GRAPH_API_URL = "https://graph.facebook.com/v19.0"


@log_step
async def publish_to_threads(content: dict, model_info: dict) -> dict:
    """
    Publie du contenu sur Threads via l'API officielle Meta.
    """
    try:
        caption = content.get("caption", "")
        media_url = content.get("media")[0]["url"]  # Supposé image unique
        agency_id = model_info.get("agency_id")
        muse_id = model_info.get("muse_id")
        content_id = content.get("id", "unknown")

        # Étape 1 : Création de l'objet media
        media_endpoint = f"{GRAPH_API_URL}/{THREADS_USER_ID}/media"
        media_payload = {
            "image_url": media_url,
            "caption": caption,
            "access_token": META_ACCESS_TOKEN
        }

        media_response = requests.post(media_endpoint, data=media_payload)

        if media_response.status_code != 200:
            error_msg = f"Erreur création media : {media_response.text}"
            await log_platform_event(
                platform="threads",
                agency_id=agency_id,
                muse_id=muse_id,
                content_id=content_id,
                status="error",
                message=error_msg,
                metadata={"media_url": media_url}
            )
            return {"status": "error", "details": error_msg}

        media_id = media_response.json().get("id")

        # Étape 2 : Publication
        publish_endpoint = f"{GRAPH_API_URL}/{THREADS_USER_ID}/media_publish"
        publish_response = requests.post(publish_endpoint, data={
            "creation_id": media_id,
            "access_token": META_ACCESS_TOKEN
        })

        if publish_response.status_code == 200:
            await log_platform_event(
                platform="threads",
                agency_id=agency_id,
                muse_id=muse_id,
                content_id=content_id,
                status="success",
                message="Publication réussie sur Threads",
                metadata={"media_id": media_id}
            )
            return publish_response.json()

        else:
            error_msg = f"Erreur publication : {publish_response.text}"
            await log_platform_event(
                platform="threads",
                agency_id=agency_id,
                muse_id=muse_id,
                content_id=content_id,
                status="error",
                message=error_msg,
                metadata={"media_url": media_url}
            )
            return {"status": "error", "details": error_msg}

    except Exception as e:
        await log_platform_event(
            platform="threads",
            agency_id=model_info.get("agency_id"),
            muse_id=model_info.get("muse_id"),
            content_id=content.get("id", "unknown"),
            status="error",
            message="Exception lors de la publication sur Threads",
            metadata={"error": str(e)}
        )
        return {"status": "error", "exception": str(e)}
