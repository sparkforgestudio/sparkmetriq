from __future__ import annotations

import dataclasses
import re
from datetime import date, datetime
from typing import Any, Dict, Mapping, Optional

REDACTED = "[REDACTED]"
REDACTED_TOKEN = "[REDACTED_TOKEN]"

ALWAYS_REDACT_KEYS = {
    "password",
    "passwd",
    "pass",
    "secret",
    "client_secret",
    "private_key",
    "refresh_token",
    "access_token",
    "authorization",
    "auth",
    "email",  # dans un dict, email => [REDACTED] (tests)
}

TOKEN_LIKE_KEYS = {
    "token",
    "api_key",
    "apikey",
    "key",
    "bearer",
}

_EMAIL_RE = re.compile(r"([a-zA-Z0-9._%+\-]+)@([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})")

_TOKEN_RE = re.compile(
    r"""
    (?:
        sk_(?:live|test)_[A-Za-z0-9]{10,} |
        long_token_[A-Za-z0-9]{10,} |
        (?:[A-Za-z0-9_\-]{24,})
    )
    """,
    re.VERBOSE,
)


def _mask_emails_in_text(text: str) -> str:
    def repl(m: re.Match) -> str:
        local, domain = m.group(1), m.group(2)
        return f"{local}***@{domain}"

    return _EMAIL_RE.sub(repl, text)


def _looks_like_sensitive_token(s: str) -> bool:
    s2 = s.strip()
    if len(s2) < 20:
        return False
    return bool(_TOKEN_RE.search(s2))


def _redact_tokens_in_text(text: str) -> str:
    return _TOKEN_RE.sub(REDACTED_TOKEN, text)


def _dump_object(obj: Any) -> Any:
    """
    Convertit les objets non-JSON (Principal, TenantContext, etc.) en dict.
    - Pydantic v2: model_dump
    - dataclass: asdict
    - objets classiques: __dict__
    """
    if obj is None:
        return None

    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")

    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)

    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:
            pass

    if hasattr(obj, "__dict__"):
        try:
            return dict(obj.__dict__)
        except Exception:
            pass

    return obj


def _json_safe_scalar(v: Any) -> Any:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def redact_pii(data: Any, *, key: Optional[str] = None) -> Any:
    """
    Règles tests :
    - dict["email"] => "[REDACTED]"
    - string libre => email masqué user***@domain, tokens => [REDACTED_TOKEN]
    - clés sensibles => [REDACTED]
    - tokens longs => [REDACTED_TOKEN]
    - doit fonctionner avec objets (Principal...) en les dumpant récursivement
    """
    k = (key or "").lower()

    # Convertir objets (Principal, TenantContext, etc.) avant d'analyser
    data = _dump_object(data)

    # dict / mapping
    if isinstance(data, Mapping):
        out: Dict[str, Any] = {}
        for kk, vv in data.items():
            out[str(kk)] = redact_pii(vv, key=str(kk))
        return out

    # list / tuple / set
    if isinstance(data, (list, tuple, set)):
        if k == "tokens":
            items = []
            for item in data:
                if isinstance(item, str) and _looks_like_sensitive_token(item):
                    items.append(REDACTED_TOKEN)
                else:
                    items.append(redact_pii(item, key=key))
            return list(items)

        return [redact_pii(x, key=key) for x in data]

    # datetime/date
    if isinstance(data, (datetime, date)):
        return data.isoformat()

    # string
    if isinstance(data, str):
        # clé sensible => redaction stricte
        if k in ALWAYS_REDACT_KEYS or "email" in k:
            return REDACTED

        # token-like key => token si long, sinon redacted
        if k in TOKEN_LIKE_KEYS:
            return REDACTED_TOKEN if _looks_like_sensitive_token(data) else REDACTED

        # texte libre => masque emails + redaction tokens
        s = _mask_emails_in_text(data)
        s = _redact_tokens_in_text(s)
        return s

    # si c'est encore un objet non-serializable, on retente dump
    if hasattr(data, "__dict__") or dataclasses.is_dataclass(data):
        return redact_pii(_dump_object(data), key=key)

    return _json_safe_scalar(data)


def to_audit_dict(event: Any) -> Dict[str, Any]:
    """
    Doit renvoyer un dict subscriptable + JSON-serializable,
    avec redaction appliquée partout (actor.claims inclus).
    """
    raw = _dump_object(event)

    if isinstance(raw, Mapping):
        raw_dict = dict(raw)
    elif hasattr(raw, "__dict__"):
        raw_dict = dict(raw.__dict__)
    else:
        raw_dict = {"event": str(raw)}

    redacted = redact_pii(raw_dict)

    if not isinstance(redacted, dict):
        return {"event": redacted}

    return redacted
