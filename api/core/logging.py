# api/core/logging.py
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any, Dict

DEFAULT_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

SENSITIVE_KEYS = {"password", "authorization", "token", "secret", "api_key"}

# Configuration de logging par défaut avec dictConfig
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "level": DEFAULT_LEVEL,
        "handlers": ["console"],
    },
}


def _safe_json(obj: Any) -> Any:
    """Fallback de sérialisation JSON (ex: ObjectId, datetime naïf)."""
    try:
        json.dumps(obj)
        return obj
    except Exception:
        if isinstance(obj, datetime):
            # Si naïf → le convertir en UTC
            if obj.tzinfo is None:
                return obj.replace(tzinfo=timezone.utc).isoformat()
            return obj.isoformat()
        return str(obj)


class JsonFormatter(logging.Formatter):
    """Formatter JSON structuré pour logs applicatifs/HTTP."""

    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "level_no": record.levelno,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # Intègre extra fields tout en filtrant les sensibles et internes
        extras: Dict[str, Any] = {}
        for k, v in record.__dict__.items():
            if k in ("args", "msg", "exc_info", "exc_text", "stack_info", "stacklevel",
                     "name", "levelno", "levelname", "pathname", "filename", "module",
                     "lineno", "funcName", "created", "msecs", "relativeCreated",
                     "thread", "threadName", "processName", "process"):
                continue
            if k in SENSITIVE_KEYS:
                extras[k] = "***redacted***"
            else:
                extras[k] = _safe_json(v)

        if extras:
            base["extra"] = extras

        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(base, ensure_ascii=False)


def setup_logging(use_json: bool = False) -> None:
    """
    Configure le logging global de l'application.

    Args:
        use_json: Si True, utilise le formatter JSON structuré.
                  Si False (défaut), utilise la configuration dictConfig simple.
    """
    if use_json:
        # Mode JSON structuré (comportement original)
        root = logging.getLogger()
        # Si déjà configuré (ex: relance ou Uvicorn a posé ses handlers), ne pas dupliquer
        if root.handlers:
            # On harmonise simplement les formatters existants si possible
            for h in root.handlers:
                try:
                    h.setFormatter(JsonFormatter())
                except Exception:
                    pass
            root.setLevel(getattr(logging, DEFAULT_LEVEL, logging.INFO))
            return

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())

        root.setLevel(getattr(logging, DEFAULT_LEVEL, logging.INFO))
        root.addHandler(handler)

        # Harmoniser les loggers uvicorn
        for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
            lg = logging.getLogger(name)
            lg.handlers.clear()
            lg.addHandler(handler)
            lg.setLevel(getattr(logging, DEFAULT_LEVEL, logging.INFO))
            # Important: laisser la propagation pour centraliser sur root
            lg.propagate = True
    else:
        # Mode dictConfig (configuration simple par défaut)
        dictConfig(LOGGING_CONFIG)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Retourne un logger nommé cohérent pour Sparkmetriq.

    Si name est None, on retourne un logger racine 'sparkmetriq'.

    Args:
        name: Nom du logger. Si None, utilise 'sparkmetriq' par défaut.

    Returns:
        Logger configuré avec le nom spécifié.
    """
    if not name:
        name = "sparkmetriq"
    return logging.getLogger(name)



