from datetime import datetime, timezone

def utcnow_iso() -> str:
    """Retourne un timestamp ISO 8601 en UTC (timezone-aware)."""
    return datetime.now(timezone.utc).isoformat()

def utcnow() -> datetime:
    """Retourne un datetime timezone-aware en UTC."""
    return datetime.now(timezone.utc)
