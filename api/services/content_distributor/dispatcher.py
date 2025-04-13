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
from services.config.funnel_config import get_config

class ContentDispatcher:
    async def dispatch(self, platform: str, content: dict, agency_id: str, muse_id: str = None) -> None:
        """
        Détermine le funnel_stage en se basant sur la configuration dynamique et
        effectue l'envoi du contenu vers la plateforme spécifiée.

        :param platform: Nom de la plateforme (e.g., "instagram", "tiktok", etc.)
        :param content: Dictionnaire contenant les données du contenu.
        :param agency_id: Identifiant de l'agence.
        :param muse_id: (Optionnel) Identifiant de la muse.
        """
        config = await get_config(agency_id, muse_id)
        if config:
            if platform in config.mappings.source:
                stage = "source"
            elif platform in config.mappings.intermediate:
                stage = "intermediate"
            elif platform in config.mappings.closing:
                stage = "closing"
            else:
                stage = "non spécifié"
        else:
            stage = "non spécifié"
        
        # Insérer le résultat dans le contenu à dispatcher
        content["funnel_stage"] = stage
        logger.info(f"Dispatching on {platform} with funnel_stage '{stage}'")
        await self.send_to_platform(platform, content)
    
    async def send_to_platform(self, platform: str, content: dict) -> None:
        """
        Envoie le contenu vers la plateforme spécifiée. La logique réelle d'envoi devra
        être adaptée à chaque connecteur.

        :param platform: Nom de la plateforme.
        :param content: Données du contenu incluant le funnel_stage.
        """
        # Exemple d'appel générique ; à remplacer par la logique concrète pour chaque plateforme.
        print(f"Envoi de contenu vers {platform} avec le stage {content.get('funnel_stage')}")
        # Ici, implémentez la logique réelle ou effectuez une redirection vers un autre service.

# Mapping des plateformes aux fonctions de publication
PLATFORM_DISPATCHERS = {
    "instagram": publish_to_instagram,
    "tiktok": publish_to_tiktok,
    "threads": publish_to_threads,
    "snapchat": publish_to_snapchat,
    "reddit": publish_to_reddit,
    "twitter": publish_to_twitter,
    "telegram": publish_to_telegram,
    "facebook": publish_to_facebook,
    "onlyfans": publish_to_onlyfans,
}

@log_step
async def dispatch_content(content: Dict, platforms: List[str], model_info: Dict) -> Dict:
    """
    Orchestration principale pour publier le contenu sur plusieurs plateformes.

    :param content: Données du contenu à publier (caption, media, etc.)
    :param platforms: Liste des plateformes cibles (e.g., ["instagram", "tiktok"])
    :param model_info: Informations de la muse et/ou de l'agence (id, tokens, configuration, etc.)
    :return: Dictionnaire des résultats de publication par plateforme.
    """
    results = {}

    # Itération sur la liste des plateformes demandées
    for platform in platforms:
        try:
            # Vérifier s'il existe une fonction de publication associée
            if platform in PLATFORM_DISPATCHERS:
                dispatch_func = PLATFORM_DISPATCHERS[platform]
                results[platform] = await dispatch_func(content, model_info)
            else:
                results[platform] = {
                    "status": "skipped",
                    "reason": f"Plateforme non prise en charge: {platform}"
                }
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur {platform}: {e}")
            results[platform] = {
                "status": "error",
                "reason": str(e)
            }
    return results
