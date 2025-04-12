import logging
from pathlib import Path
from services.logger.telegram_handler import TelegramLogHandler


# Créer un dossier de logs s’il n’existe pas
Path("logs").mkdir(exist_ok=True)

scheduler_logger = logging.getLogger("scheduler_logger")
scheduler_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/scheduler.log", encoding="utf-8")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

scheduler_logger.addHandler(file_handler)
telegram_handler = TelegramLogHandler()
telegram_handler.setLevel(logging.INFO)
telegram_handler.setFormatter(formatter)
logger.addHandler(telegram_handler)