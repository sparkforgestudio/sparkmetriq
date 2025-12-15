# api/services/compat_env.py
from __future__ import annotations

import os


def getenv_first(*names: str, default: str | None = None) -> str | None:
    """Return the first non-empty env var among names; else default."""
    for n in names:
        v = os.getenv(n)
        if v is not None and str(v).strip() != "":
            return v
    return default


def core_secret_key() -> str:
    # New -> legacy -> safe dev default
    return (
        getenv_first("CORE_SECRET_KEY", "MUSAI_SECRET_KEY", default=None)
        or "dev_insecure_change_me"
    )


def core_db_uri() -> str:
    # New -> legacy aliases -> generic -> default
    return (
        getenv_first(
            "CORE_DB_URI",
            "MONGO_URI",
            "MUSAI_CORE_DB_URI",
            default=None,
        )
        or "mongodb://localhost:27017"
    )


def core_db_name() -> str:
    return (
        getenv_first(
            "CORE_DB_NAME",
            "MUSAI_CORE_DB_NAME",
            "DB_NAME_CORE",
            default=None,
        )
        or "core"
    )


def bi_db_uri() -> str:
    return (
        getenv_first(
            "BI_DB_URI",
            "MONGO_URI_BI",
            "MUSAI_BI_DB_URI",
            default=None,
        )
        or "mongodb://localhost:27017"
    )


def bi_db_name() -> str:
    return (
        getenv_first(
            "BI_DB_NAME",
            "MUSAI_BI_DB_NAME",
            "DB_NAME_BI",
            default=None,
        )
        or "bi"
    )
