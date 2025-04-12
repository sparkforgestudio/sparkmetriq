# services/content_distributor/logger.py

import logging
from logging.handlers import RotatingFileHandler
import os
import datetime
import requests

# ➜ Créer le dossier de logs s'il n'existe pas
LOG_DIR = os.path.join(os.path.dirname(__file__), '../../logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOG_DIR, 'dispatcher.log')

class TelegramLogHandler(logging.Handler):
    def __init__(self, bot_token: str, chat_id: str):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": log_entry}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception:
            pass  # Ne pas crasher le logger si Telegram est indisponible

# Configuration du logger principal
logger = logging.getLogger("dispatcher")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=1000000, backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Exemple d'intégration Telegram (remplacer par vos vraies clés définitives)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_LOG_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_LOG_CHAT_ID")

if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    telegram_handler = TelegramLogHandler(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    telegram_handler.setFormatter(formatter)
    telegram_handler.setLevel(logging.INFO)
    logger.addHandler(telegram_handler)

# Utilisation recommandée dans le code :
# from services.content_distributor.logger import logger
# logger.info("Message standard")
# logger.success("Succès déploiement")
# logger.error("Erreur critique")
