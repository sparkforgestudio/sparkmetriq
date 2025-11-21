# api/services/auth/__init__.py
"""
Services d'authentification.
"""

try:
    from api.services.auth.google_oauth import verify_google_token, get_or_create_google_user
    __all__ = ["verify_google_token", "get_or_create_google_user"]
except ImportError:
    __all__ = []


