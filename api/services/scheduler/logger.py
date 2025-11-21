# api/services/scheduler/logger.py

import logging
from datetime import datetime
from logs.telegram_handler import TelegramLogHandler

# Logger dédié au scheduler
scheduler_logger = logging.getLogger("scheduler")
scheduler_logger.setLevel(logging.INFO)

# Si aucun handler n'est configuré, on ajoute le handler Telegram
if not scheduler_logger.handlers:
    handler = TelegramLogHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    scheduler_logger.addHandler(handler)

def log_scheduler_event(message: str, level: str = "info") -> None:
    """
    Journalise un événement du scheduler via Telegram.
    """
    timestamp = utcnow().isoformat()
    log_msg = f"{timestamp} - {message}"
    if level.lower() == "info":
        scheduler_logger.info(log_msg)
    elif level.lower() == "warning":
        scheduler_logger.warning(log_msg)
    elif level.lower() == "error":
        scheduler_logger.error(log_msg)
    else:
        scheduler_logger.debug(log_msg)
