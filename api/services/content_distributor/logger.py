import logging
from datetime import datetime
from typing import Any, Dict, Callable, Coroutine, TypeVar

# Configuration du logger pour le module content_distributor
logger = logging.getLogger("content_distributor")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Typing pour le décorateur
F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])

async def log_platform_event(
    platform: str,
    agency_id: str,
    muse_id: str,
    content_id: str,
    status: str,
    message: str,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enregistre un événement lié à la publication sur une plateforme.

    Retourne le dictionnaire de l'événement pour un stockage ou traitement ultérieur.
    """
    event: Dict[str, Any] = {
        "platform": platform,
        "agency_id": agency_id,
        "muse_id": muse_id,
        "content_id": content_id,
        "status": status,
        "message": message,
        "metadata": metadata,
        "timestamp": utcnow().isoformat()
    }
    logger.info(f"Platform event: {event}")
    return event

def log_step(func: F) -> F:
    """
    Décorateur pour logger le début et la fin d'une fonction asynchrone.

    Usage:
        @log_step
        async def ma_fonction(...):
            ...
    """
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info(f"Starting function: {func.__name__}")
        result = await func(*args, **kwargs)
        logger.info(f"Finished function: {func.__name__}")
        return result

    return wrapper  # type: ignore
