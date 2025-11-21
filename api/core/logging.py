# api/core/logging.py
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

DEFAULT_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

SENSITIVE_KEYS = {"password", "authorization", "token", "secret", "api_key"}


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


def setup_logging() -> None:
    """
    Initialise le logging structuré JSON pour l’app.
    - Respecte les handlers existants (évite de doubler les logs sous Uvicorn).
    - Aligne uvicorn.access / uvicorn.error sur le même formatter.
    """
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
        # Important: laisser la propagation pour centraliser sur root (ou mettez False si vous préférez)
        lg.propagate = True


