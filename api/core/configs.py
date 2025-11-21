# api/core/configs.py
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# 🔐 Configuration JWT
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_in_production")
secret_key = SECRET_KEY  # alias pour compatibilité
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# 🔌 Meta / Graph API (Threads, Instagram, Facebook)
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID", "")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET", "")
INSTAGRAM_PAGE_ID = os.getenv("INSTAGRAM_PAGE_ID", "")
INSTAGRAM_VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN", "")
THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")

# 📱 WhatsApp Business API
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

# 🐦 Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# 🐦 Twitter API
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

# 🐙 Reddit API
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "")

# Clé privée NOWPayments (Account → Settings → API Keys)
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "")

# URL de base (optionnel, vous pouvez hardcoder)
NOWPAYMENTS_URL = os.getenv("NOWPAYMENTS_URL", "https://api.nowpayments.io")

# 🤖 DeepSeek LLM
DEESEEK_MODEL_PATH = os.getenv("DEESEEK_MODEL_PATH", "/models/deepseek/")

# 🔐 Google OAuth 2.0
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")  # Optionnel pour backend (id_token only)