from telegram import Bot, InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from datetime import datetime
import asyncio
from services.content_distributor.logger import logger

TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # à externaliser via config

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def publish_telegram_post(content: dict) -> bool:
    try:
        chat_id = content["chat_id"]
        caption = content.get("caption", "")
        media = content.get("media", [])
        cta_buttons = content.get("cta_buttons", [])
        scheduled_time = content.get("scheduled_time")  # format ISO 8601

        if scheduled_time:
            # attendre jusqu'à la date planifiée
            delay = (datetime.fromisoformat(scheduled_time) - datetime.utcnow()).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)

        # Création de groupe media si plusieurs éléments
        if media:
            media_group = []
            for i, item in enumerate(media):
                if item["type"] == "photo":
                    media_group.append(InputMediaPhoto(media=item["url"], caption=caption if i == 0 else None))
                elif item["type"] == "video":
                    media_group.append(InputMediaVideo(media=item["url"], caption=caption if i == 0 else None))
            await bot.send_media_group(chat_id=chat_id, media=media_group)
        else:
            # Message texte seul
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(text=btn["text"], url=btn["url"])] for btn in cta_buttons]
            ) if cta_buttons else None
            await bot.send_message(chat_id=chat_id, text=caption, reply_markup=keyboard)

        return True

    except TelegramError as e:
        print(f"Telegram API error: {e}")
        return False

# telegram.py
from ...logger import log_step

@log_step
async def publish_to_telegram(content, model_info):
    # implémentation réelle ici
    pass