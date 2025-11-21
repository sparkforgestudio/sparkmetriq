# api/services/ai_marketing/logger.py
"""
Logger pour le module IA Marketing.
"""

import logging
import os
from datetime import datetime

# Configuration du logger
logger = logging.getLogger("ai_marketing")

# Niveau de log basé sur l'environnement
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, log_level))

# Handler pour les logs
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Handler pour les fichiers de log
log_file = os.getenv("AI_MARKETING_LOG_FILE", "logs/ai_marketing.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)



