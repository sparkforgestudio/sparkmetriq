# api/core/platform_configs.py
import os
from typing import Dict, Any, List
from enum import Enum

class PlatformConfig:
    """Configuration pour une plateforme."""
    
    def __init__(self, name: str, api_base_url: str, required_env_vars: List[str], 
                 optional_env_vars: List[str] = None, webhook_supported: bool = True):
        self.name = name
        self.api_base_url = api_base_url
        self.required_env_vars = required_env_vars
        self.optional_env_vars = optional_env_vars or []
        self.webhook_supported = webhook_supported

# Configuration des plateformes supportées
PLATFORM_CONFIGS = {
    "instagram": PlatformConfig(
        name="Instagram",
        api_base_url="https://graph.facebook.com/v18.0",
        required_env_vars=["INSTAGRAM_GRAPH_TOKEN", "INSTAGRAM_ACCOUNT_ID"],
        optional_env_vars=["INSTAGRAM_WEBHOOK_SECRET"]
    ),
    
    "tiktok": PlatformConfig(
        name="TikTok",
        api_base_url="https://open.tiktokapis.com/v2",
        required_env_vars=["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REDIRECT_URI"],
        optional_env_vars=["TIKTOK_WEBHOOK_SECRET", "TIKTOK_VERIFY_TOKEN"]
    ),
    
    "telegram": PlatformConfig(
        name="Telegram",
        api_base_url="https://api.telegram.org",
        required_env_vars=["TELEGRAM_BOT_TOKEN"],
        optional_env_vars=["TELEGRAM_WEBHOOK_SECRET"]
    ),
    
    "threads": PlatformConfig(
        name="Threads",
        api_base_url="https://graph.facebook.com/v19.0",
        required_env_vars=["META_ACCESS_TOKEN", "THREADS_USER_ID"],
        optional_env_vars=["THREADS_WEBHOOK_SECRET"]
    ),
    
    "snapchat": PlatformConfig(
        name="Snapchat",
        api_base_url="https://adsapi.snapchat.com/v1",
        required_env_vars=["SNAPCHAT_CLIENT_ID", "SNAPCHAT_CLIENT_SECRET"],
        optional_env_vars=["SNAPCHAT_WEBHOOK_SECRET"]
    ),
    
    "reddit": PlatformConfig(
        name="Reddit",
        api_base_url="https://oauth.reddit.com",
        required_env_vars=["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"],
        optional_env_vars=["REDDIT_WEBHOOK_SECRET"]
    ),
    
    "twitter": PlatformConfig(
        name="Twitter",
        api_base_url="https://api.twitter.com/2",
        required_env_vars=["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET"],
        optional_env_vars=["TWITTER_WEBHOOK_SECRET"]
    ),
    
    "facebook": PlatformConfig(
        name="Facebook",
        api_base_url="https://graph.facebook.com/v18.0",
        required_env_vars=["FACEBOOK_ACCESS_TOKEN", "FACEBOOK_PAGE_ID"],
        optional_env_vars=["FACEBOOK_WEBHOOK_SECRET"]
    ),
    
    "onlyfans": PlatformConfig(
        name="OnlyFans",
        api_base_url="https://onlyfans.com/api/v1",
        required_env_vars=["ONLYFANS_API_KEY", "ONLYFANS_API_SECRET"],
        optional_env_vars=["ONLYFANS_WEBHOOK_SECRET", "ONLYFANS_VERIFY_TOKEN"]
    ),
    
    "fanvue": PlatformConfig(
        name="Fanvue",
        api_base_url="https://api.fanvue.com/v1",
        required_env_vars=["FANVUE_API_KEY", "FANVUE_API_SECRET"],
        optional_env_vars=["FANVUE_WEBHOOK_SECRET", "FANVUE_VERIFY_TOKEN"]
    ),
    
    "whatsapp": PlatformConfig(
        name="WhatsApp",
        api_base_url="https://graph.facebook.com/v18.0",
        required_env_vars=["WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"],
        optional_env_vars=["WHATSAPP_WEBHOOK_SECRET", "WHATSAPP_VERIFY_TOKEN"]
    ),
    
    "fansly": PlatformConfig(
        name="Fansly",
        api_base_url="https://api.fansly.com/v1",
        required_env_vars=["FANSLY_API_KEY", "FANSLY_API_SECRET"],
        optional_env_vars=["FANSLY_WEBHOOK_SECRET", "FANSLY_VERIFY_TOKEN"]
    ),
    
    "loyalfans": PlatformConfig(
        name="LoyalFans",
        api_base_url="https://api.loyalfans.com/v1",
        required_env_vars=["LOYALFANS_API_KEY", "LOYALFANS_API_SECRET"],
        optional_env_vars=["LOYALFANS_WEBHOOK_SECRET", "LOYALFANS_VERIFY_TOKEN"]
    ),
    
    "patreon": PlatformConfig(
        name="Patreon",
        api_base_url="https://www.patreon.com/api/oauth2/v2",
        required_env_vars=["PATREON_ACCESS_TOKEN", "PATREON_CLIENT_ID", "PATREON_CLIENT_SECRET"],
        optional_env_vars=["PATREON_WEBHOOK_SECRET", "PATREON_VERIFY_TOKEN"]
    ),
    
    "discord": PlatformConfig(
        name="Discord",
        api_base_url="https://discord.com/api/v10",
        required_env_vars=["DISCORD_BOT_TOKEN", "DISCORD_CLIENT_ID"],
        optional_env_vars=["DISCORD_CLIENT_SECRET", "DISCORD_WEBHOOK_SECRET"]
    ),
    
    "mymfans": PlatformConfig(
        name="MYM.fans",
        api_base_url="https://api.mym.fans/v1",
        required_env_vars=["MYMFANS_API_KEY", "MYMFANS_API_SECRET"],
        optional_env_vars=["MYMFANS_WEBHOOK_SECRET", "MYMFANS_VERIFY_TOKEN"]
    ),
    
    "manyvids": PlatformConfig(
        name="ManyVids",
        api_base_url="https://api.manyvids.com/v1",
        required_env_vars=["MANYVIDS_API_KEY", "MANYVIDS_API_SECRET"],
        optional_env_vars=["MANYVIDS_WEBHOOK_SECRET", "MANYVIDS_VERIFY_TOKEN"]
    )
}

def get_platform_config(platform_name: str) -> PlatformConfig:
    """Récupère la configuration d'une plateforme."""
    if platform_name not in PLATFORM_CONFIGS:
        raise ValueError(f"Plateforme non supportée: {platform_name}")
    return PLATFORM_CONFIGS[platform_name]

def get_platform_credentials(platform_name: str) -> Dict[str, Any]:
    """Récupère les credentials d'une plateforme depuis les variables d'environnement."""
    config = get_platform_config(platform_name)
    credentials = {}
    
    # Vérification des variables requises
    for var in config.required_env_vars:
        value = os.getenv(var)
        if not value:
            raise ValueError(f"Variable d'environnement requise manquante: {var}")
        credentials[var.lower()] = value
    
    # Ajout des variables optionnelles
    for var in config.optional_env_vars:
        value = os.getenv(var)
        if value:
            credentials[var.lower()] = value
    
    return credentials

def validate_platform_credentials(platform_name: str, credentials: Dict[str, Any]) -> bool:
    """Valide les credentials d'une plateforme."""
    try:
        config = get_platform_config(platform_name)
        
        # Vérification des champs requis
        for var in config.required_env_vars:
            if var.lower() not in credentials:
                return False
        
        return True
    except ValueError:
        return False

def get_supported_platforms() -> List[str]:
    """Retourne la liste des plateformes supportées."""
    return list(PLATFORM_CONFIGS.keys())

def get_platforms_with_webhooks() -> List[str]:
    """Retourne la liste des plateformes supportant les webhooks."""
    return [name for name, config in PLATFORM_CONFIGS.items() if config.webhook_supported]

def get_platform_status() -> Dict[str, Dict[str, Any]]:
    """Retourne le statut de configuration de toutes les plateformes."""
    status = {}
    
    for platform_name, config in PLATFORM_CONFIGS.items():
        platform_status = {
            "name": config.name,
            "api_base_url": config.api_base_url,
            "webhook_supported": config.webhook_supported,
            "configured": True,
            "missing_vars": [],
            "optional_vars": []
        }
        
        # Vérification des variables requises
        for var in config.required_env_vars:
            if not os.getenv(var):
                platform_status["configured"] = False
                platform_status["missing_vars"].append(var)
        
        # Vérification des variables optionnelles
        for var in config.optional_env_vars:
            if os.getenv(var):
                platform_status["optional_vars"].append(var)
        
        status[platform_name] = platform_status
    
    return status

# Configuration des webhooks
WEBHOOK_ENDPOINTS = {
    "instagram": "/webhook/instagram",
    "tiktok": "/webhook/tiktok",
    "telegram": "/webhook/telegram",
    "threads": "/webhook/threads",
    "snapchat": "/webhook/snapchat",
    "reddit": "/webhook/reddit",
    "twitter": "/webhook/twitter",
    "facebook": "/webhook/facebook",
    "onlyfans": "/webhook/onlyfans",
    "fanvue": "/webhook/fanvue",
    "whatsapp": "/webhook/whatsapp",
    "fansly": "/webhook/fansly",
    "loyalfans": "/webhook/loyalfans",
    "patreon": "/webhook/patreon",
    "discord": "/webhook/discord",
    "mymfans": "/webhook/mymfans",
    "manyvids": "/webhook/manyvids"
}

def get_webhook_endpoint(platform_name: str) -> str:
    """Récupère l'endpoint webhook d'une plateforme."""
    if platform_name not in WEBHOOK_ENDPOINTS:
        raise ValueError(f"Webhook non supporté pour la plateforme: {platform_name}")
    return WEBHOOK_ENDPOINTS[platform_name]

# Configuration des limites de taux (rate limiting)
RATE_LIMITS = {
    "instagram": {"requests_per_hour": 200, "requests_per_day": 4800},
    "tiktok": {"requests_per_hour": 100, "requests_per_day": 2400},
    "telegram": {"requests_per_hour": 30, "requests_per_day": 720},
    "threads": {"requests_per_hour": 200, "requests_per_day": 4800},
    "snapchat": {"requests_per_hour": 100, "requests_per_day": 2400},
    "reddit": {"requests_per_hour": 60, "requests_per_day": 1440},
    "twitter": {"requests_per_hour": 300, "requests_per_day": 7200},
    "facebook": {"requests_per_hour": 200, "requests_per_day": 4800},
    "onlyfans": {"requests_per_hour": 50, "requests_per_day": 1200},
    "fanvue": {"requests_per_hour": 100, "requests_per_day": 2400},
    "whatsapp": {"requests_per_hour": 1000, "requests_per_day": 24000},
    "fansly": {"requests_per_hour": 100, "requests_per_day": 2400},
    "loyalfans": {"requests_per_hour": 100, "requests_per_day": 2400},
    "patreon": {"requests_per_hour": 60, "requests_per_day": 1440},
    "discord": {"requests_per_hour": 50, "requests_per_day": 1200},
    "mymfans": {"requests_per_hour": 100, "requests_per_day": 2400},
    "manyvids": {"requests_per_hour": 100, "requests_per_day": 2400}
}

def get_rate_limit(platform_name: str) -> Dict[str, int]:
    """Récupère les limites de taux d'une plateforme."""
    if platform_name not in RATE_LIMITS:
        return {"requests_per_hour": 100, "requests_per_day": 2400}  # Valeurs par défaut
    return RATE_LIMITS[platform_name]

# Configuration des types de contenu supportés
SUPPORTED_CONTENT_TYPES = {
    "instagram": ["image", "video", "carousel", "story", "reel"],
    "tiktok": ["video"],
    "telegram": ["text", "image", "video", "document", "audio", "voice", "sticker"],
    "threads": ["text", "image", "video"],
    "snapchat": ["image", "video", "story"],
    "reddit": ["text", "image", "video", "link"],
    "twitter": ["text", "image", "video", "poll"],
    "facebook": ["text", "image", "video", "link"],
    "onlyfans": ["image", "video", "text"],
    "fanvue": ["image", "video", "text"],
    "whatsapp": ["text", "image", "video", "document", "audio"],
    "fansly": ["image", "video", "text"],
    "loyalfans": ["image", "video", "text"],
    "patreon": ["text", "image", "video"],
    "discord": ["text", "image", "video", "file", "embed"],
    "mymfans": ["image", "video", "text"],
    "manyvids": ["video", "image"]
}

def get_supported_content_types(platform_name: str) -> List[str]:
    """Récupère les types de contenu supportés par une plateforme."""
    if platform_name not in SUPPORTED_CONTENT_TYPES:
        return ["text", "image", "video"]  # Types par défaut
    return SUPPORTED_CONTENT_TYPES[platform_name]

# Configuration des tailles de fichiers maximales (en MB)
MAX_FILE_SIZES = {
    "instagram": {"image": 8, "video": 100},
    "tiktok": {"video": 500},
    "telegram": {"image": 5, "video": 50, "document": 2},
    "threads": {"image": 8, "video": 100},
    "snapchat": {"image": 5, "video": 100},
    "reddit": {"image": 20, "video": 100},
    "twitter": {"image": 5, "video": 512},
    "facebook": {"image": 8, "video": 100},
    "onlyfans": {"image": 10, "video": 200},
    "fanvue": {"image": 10, "video": 200},
    "whatsapp": {"image": 5, "video": 16, "document": 100},
    "fansly": {"image": 10, "video": 200},
    "loyalfans": {"image": 10, "video": 200},
    "patreon": {"image": 8, "video": 100},
    "discord": {"image": 8, "video": 25, "file": 8},
    "mymfans": {"image": 10, "video": 200},
    "manyvids": {"image": 10, "video": 500}
}

def get_max_file_size(platform_name: str, content_type: str) -> int:
    """Récupère la taille maximale de fichier pour une plateforme et un type de contenu."""
    if platform_name not in MAX_FILE_SIZES:
        return 10  # Taille par défaut en MB
    
    platform_limits = MAX_FILE_SIZES[platform_name]
    if content_type not in platform_limits:
        return 10  # Taille par défaut en MB
    
    return platform_limits[content_type]
