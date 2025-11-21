from typing import List, Dict
from .connectors.instagram import publish_to_instagram
from .connectors.tiktok import publish_to_tiktok
from .connectors.threads import publish_to_threads
from .connectors.snapchat import publish_to_snapchat
from .connectors.reddit import publish_to_reddit
from .connectors.twitter import publish_to_twitter
from .connectors.telegram import publish_to_telegram
from .connectors.facebook import publish_to_facebook
from .connectors.onlyfans import publish_to_onlyfans
from .connectors.fanvue import publish_to_fanvue
from .connectors.fansly import publish_to_fansly
from .connectors.loyalfans import publish_to_loyalfans
from .connectors.whatsapp import publish_to_whatsapp
from .connectors.patreon import publish_to_patreon
from .connectors.discord import publish_to_discord
from .connectors.mymfans import publish_to_mymfans
from .connectors.manyvids import publish_to_manyvids

from .logger import logger, log_step
from ..config.funnel_config import get_config


class ContentDispatcher:
    async def dispatch(self, platform: str, content: dict, agency_id: str, muse_id: str = None) -> None:
        """
        Détermine le funnel_stage en se basant sur la configuration dynamique et
        effectue l'envoi du contenu vers la plateforme spécifiée.

        :param platform: Nom de la plateforme (ex.: "instagram", "tiktok", etc.).
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

        # Insérer le funnel_stage dans le contenu à dispatcher
        content["funnel_stage"] = stage
        logger.info(f"Dispatching on {platform} with funnel_stage '{stage}'")
        await self.send_to_platform(platform, content)

    async def send_to_platform(self, platform: str, content: dict) -> None:
        """
        Envoie le contenu vers la plateforme spécifiée.
        Cette méthode doit être adaptée pour réaliser l'envoi effectif via l'API du connecteur.
        
        :param platform: Nom de la plateforme.
        :param content: Dictionnaire contenant le contenu, y compris le funnel_stage.
        """
        print(f"Envoi de contenu vers {platform} avec le stage {content.get('funnel_stage')}")
        # Implémentez ici la logique réelle d'envoi.


def get_dispatcher() -> ContentDispatcher:
    """
    Renvoie une instance de ContentDispatcher.
    """
    return ContentDispatcher()


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
    "fanvue": publish_to_fanvue,
    "fansly": publish_to_fansly,
    "loyalfans": publish_to_loyalfans,
    "whatsapp": publish_to_whatsapp,
    "patreon": publish_to_patreon,
    "discord": publish_to_discord,
    "mymfans": publish_to_mymfans,
    "manyvids": publish_to_manyvids,
}


@log_step
async def dispatch_content(content: Dict, platforms: List[str], model_info: Dict) -> Dict:
    """
    Orchestre la publication du contenu sur plusieurs plateformes.

    :param content: Données du contenu à publier (ex.: caption, media, etc.).
    :param platforms: Liste des plateformes cibles (ex.: ["instagram", "tiktok"]).
    :param model_info: Informations de la muse et/ou de l'agence (contenant au minimum les identifiants et tokens si nécessaire).
    :return: Dictionnaire regroupant les résultats de publication par plateforme.
    """
    results = {}

    for platform in platforms:
        try:
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
