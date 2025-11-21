import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from aiogram import Bot, types

from api.services.content_distributor.logger import logger, log_step, log_platform_event

# Récupérer le token Telegram depuis les variables d'environnement
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

@log_step
async def publish_to_telegram(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu sur Telegram (texte ou groupe média) et journalise l'événement.
    Bot est instancié au moment de l'appel pour éviter les erreurs de token invalide à l'import.
    """
    # Instanciation dynamique du bot
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    agency_id: str = model_info.get("agency_id", "")
    muse_id: str = model_info.get("muse_id", "")
    content_id: str = content.get("id", "")
    chat_id: Optional[str] = content.get("chat_id")
    caption: str = content.get("text") or content.get("caption", "")
    media_list: List[Dict[str, Any]] = content.get("media", [])
    cta_buttons: List[Dict[str, str]] = content.get("cta_buttons", [])

    try:
        # Publication différée si scheduled_time fourni
        scheduled_time = content.get("scheduled_time")
        if scheduled_time:
            publish_at = datetime.fromisoformat(scheduled_time)
            delay = (publish_at - utcnow()).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)

        # Envoi des médias si présents
        if media_list and chat_id:
            media_group: List[types.InputMedia] = []
            for idx, item in enumerate(media_list):
                media_type = item.get("type")
                url = item.get("url")
                caption_first = caption if idx == 0 else None
                if media_type == "photo":
                    media_group.append(types.InputMediaPhoto(media=url, caption=caption_first))
                else:
                    media_group.append(types.InputMediaVideo(media=url, caption=caption_first))
            await bot.send_media_group(chat_id=chat_id, media=media_group)
        elif chat_id:
            # Envoi d'un simple message texte
            keyboard = None
            if cta_buttons:
                inline_buttons = [[types.InlineKeyboardButton(text=b["text"], url=b["url"])] for b in cta_buttons]
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_buttons)
            await bot.send_message(chat_id=chat_id, text=caption, reply_markup=keyboard)
        else:
            raise ValueError("chat_id is required for Telegram publishing")

        # Logging de l'événement réussi
        await log_platform_event(
            platform="telegram",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="success",
            message="Publication Telegram réussie",
            metadata={"media_count": len(media_list), "cta_buttons": cta_buttons}
        )
        return {"status": "success"}

    except Exception as e:
        # Logging de l'erreur
        await log_platform_event(
            platform="telegram",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="error",
            message=str(e),
            metadata={}
        )
        logger.error(f"Erreur publish_to_telegram: {e}")
        return {"status": "error", "reason": str(e)}

    finally:
        # Fermer proprement la connexion du bot
        await bot.session.close()
