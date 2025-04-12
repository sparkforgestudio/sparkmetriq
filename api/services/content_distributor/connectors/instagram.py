import httpx
import os
from datetime import datetime
from services.content_distributor.logger import logger

INSTAGRAM_TOKEN = os.getenv("INSTAGRAM_GRAPH_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

GRAPH_URL = "https://graph.facebook.com/v18.0"

async def upload_instagram_photo(image_url: str, caption: str) -> dict:
    async with httpx.AsyncClient() as client:
        # Étape 1: Créer le conteneur de média
        create_url = f"{GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
        create_resp = await client.post(create_url, params={
            "image_url": image_url,
            "caption": caption,
            "access_token": INSTAGRAM_TOKEN
        })
        create_data = create_resp.json()
        if "id" not in create_data:
            raise Exception(f"Erreur lors de la création du média : {create_data}")

        creation_id = create_data["id"]

        # Étape 2: Publier le conteneur
        publish_url = f"{GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        publish_resp = await client.post(publish_url, params={
            "creation_id": creation_id,
            "access_token": INSTAGRAM_TOKEN
        })

        return publish_resp.json()

# instagram.py
from ...logger import log_step

@log_step
async def publish_to_instagram(content, model_info):
    # implémentation réelle ici
    pass

await log_platform_event(
    platform="instagram",
    agency_id=model_info.get("agency_id"),
    muse_id=model_info.get("muse_id"),
    content_id=content.get("id"),
    status="success",
    message="Publication Instagram réussie.",
    metadata={
        "caption": content.get("caption"),
        "media_count": len(content.get("media", [])),
        "tags": content.get("tags"),
    }
)