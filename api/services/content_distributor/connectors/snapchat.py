from typing import Dict, Any

from api.services.content_distributor.logger import logger, log_step, log_platform_event


@log_step
async def publish_to_snapchat(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simule la publication de contenu sur Snapchat (simulation).
    """
    agency_id: str = model_info.get("agency_id", "")
    muse_id: str = model_info.get("muse_id", "")
    content_id: str = content.get("id", "undefined")
    caption: str = content.get("text", content.get("caption", ""))
    media_list = content.get("media", [])

    try:
        # Simulation de la publication
        result = {
            "status": "success",
            "platform": "snapchat",
            "media_count": len(media_list),
            "message": "Contenu publié avec succès sur Snapchat (simulation)."
        }

        await log_platform_event(
            platform="snapchat",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="success",
            message="Publication Snapchat simulée réussie",
            metadata={"caption": caption, "media_count": len(media_list)}
        )

        return result

    except Exception as e:
        await log_platform_event(
            platform="snapchat",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="error",
            message="Erreur lors de la publication sur Snapchat",
            metadata={"error": str(e)}
        )
        logger.error(f"Erreur publish_to_snapchat: {e}")
        return {"status": "error", "reason": str(e)}
