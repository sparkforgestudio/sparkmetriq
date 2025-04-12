# logger/telegram_handler.py
import logging
import os
import requests

class TelegramLogHandler(logging.Handler):
    def __init__(self, level=logging.INFO):
        super().__init__(level)
        self.token = os.getenv("TELEGRAM_LOGGER_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_LOGGER_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def emit(self, record):
        if not self.token or not self.chat_id:
            return

        log_entry = self.format(record)
        try:
            requests.post(
                self.base_url,
                data={"chat_id": self.chat_id, "text": f"[{record.levelname}] {log_entry}"}
            )
        except Exception as e:
            print(f"Failed to send log to Telegram: {e}")
