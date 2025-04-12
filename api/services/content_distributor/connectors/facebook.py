import requests
from typing import Dict
from services.content_distributor.logger import log_step
from services.content_distributor.logger import logger

@log_step("Publication d'un post Facebook")
async def publish_to_facebook(content: Dict, model_info: Dict):
    """
    Publie un post avec texte et/ou image sur une page Facebook.
    :param content: Contenu à publier.
    :param model_info: Doit contenir page_access_token et page_id.
    """
    page_id = model_info.get("page_id")
    access_token = model_info.get("page_access_token")

    if not page_id or not access_token:
        raise ValueError("page_id et page_access_token sont requis dans model_info.")

    message = content.get("caption", "")
    media_url = content.get("media_url")

    # Cas 1 : Publication avec image
    if media_url:
        post_url = f"https://graph.facebook.com/{page_id}/photos"
        payload = {
            "url": media_url,
            "caption": message,
            "access_token": access_token
        }
    else:
        # Cas 2 : Publication texte simple
        post_url = f"https://graph.facebook.com/{page_id}/feed"
        payload = {
            "message": message,
            "access_token": access_token
        }

    response = requests.post(post_url, data=payload)

    if response.status_code == 200:
        return {"status": "success", "response": response.json()}
    else:
        return {
            "status": "error",
            "error": response.text,
            "code": response.status_code
        }
