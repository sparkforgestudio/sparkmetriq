from typing import List, Dict
from services.content_distributor.connectors.instagram import publish_to_instagram
from services.content_distributor.connectors.tiktok import publish_to_tiktok
from services.content_distributor.connectors.threads import publish_to_threads
from services.content_distributor.connectors.snapchat import publish_to_snapchat
from services.content_distributor.connectors.reddit import publish_to_reddit
from services.content_distributor.connectors.twitter import publish_to_twitter
from services.content_distributor.connectors.telegram import publish_to_telegram
from services.content_distributor.connectors.facebook import publish_to_facebook
from services.content_distributor.connectors.onlyfans import publish_to_onlyfans

from services.content_distributor.logger import logger, log_step


@log_step
async def dispatch_content(content: Dict, platforms: List[str], model_info: Dict) -> Dict:
    """
    Orchestration principale pour publier le contenu sur plusieurs plateformes.
    
    :param content: Données du contenu à publier (caption, media, etc.)
    :param platforms: Liste des plateformes cibles (e.g., ["instagram", "tiktok"])
    :param model_info: Informations de la muse / agence (id, tokens, etc.)
    :return: Dictionnaire des résultats de publication par plateforme.
    """
    results = {}

    for platform in platforms:
        try:
            if platform == "instagram":
                results[platform] = await publish_to_instagram(content, model_info)

            elif platform == "tiktok":
                results[platform] = await publish_to_tiktok(content, model_info)

            elif platform == "threads":
                results[platform] = await publish_to_threads(content, model_info)

            elif platform == "snapchat":
                results[platform] = await publish_to_snapchat(content, model_info)

            elif platform == "reddit":
                results[platform] = await publish_to_reddit(content, model_info)

            elif platform == "twitter":
                results[platform] = await publish_to_twitter(content, model_info)

            elif platform == "telegram":
                results[platform] = await publish_to_telegram(content, model_info)

            elif platform == "facebook":
                results[platform] = await publish_to_facebook(content, model_info)

            elif platform == "onlyfans":
                results[platform] = await publish_to_onlyfans(content, model_info)

            else:
                results[platform] = {
                    "status": "skipped",
                    "reason": f"Unsupported platform: {platform}"
                }

       
