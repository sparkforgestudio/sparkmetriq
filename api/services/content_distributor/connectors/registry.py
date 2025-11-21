# api/services/content_distributor/connectors/registry.py
"""
Registry unifié des connecteurs de plateformes.
"""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime

class BaseConnector(ABC):
    """Classe de base pour tous les connecteurs."""
    
    @abstractmethod
    async def send_post(self, *, muse_id: str, caption: str, media: list, link_out: str, story: bool, reel: bool, nsfw_filter: bool) -> dict:
        """Envoie un post sur la plateforme."""
        pass
    
    @abstractmethod
    async def send_dm(self, *, muse_id: str, user_id: str, message: str, media: list = None) -> dict:
        """Envoie un message privé."""
        pass

class InstagramConnector(BaseConnector):
    """Connecteur Instagram."""
    
    async def send_post(self, *, muse_id: str, caption: str, media: list, link_out: str, story: bool, reel: bool, nsfw_filter: bool) -> dict:
        # TODO: Implémenter l'intégration Instagram réelle
        return {
            "ok": True,
            "post_id": f"ig_{muse_id}_{int(datetime.now().timestamp())}",
            "url": f"https://instagram.com/p/mock_{muse_id}",
            "metrics": {
                "views": 150,
                "likes": 25,
                "comments": 5,
                "ctr": 0.08
            }
        }
    
    async def send_dm(self, *, muse_id: str, user_id: str, message: str, media: list = None) -> dict:
        return {
            "ok": True,
            "message_id": f"ig_dm_{user_id}",
            "sent_at": datetime.now().isoformat()
        }

class TwitterConnector(BaseConnector):
    """Connecteur Twitter/X."""
    
    async def send_post(self, *, muse_id: str, caption: str, media: list, link_out: str, story: bool, reel: bool, nsfw_filter: bool) -> dict:
        # TODO: Implémenter l'intégration Twitter réelle
        return {
            "ok": True,
            "post_id": f"tw_{muse_id}_{int(datetime.now().timestamp())}",
            "url": f"https://twitter.com/user/status/mock_{muse_id}",
            "metrics": {
                "views": 200,
                "likes": 15,
                "comments": 3,
                "ctr": 0.06
            }
        }
    
    async def send_dm(self, *, muse_id: str, user_id: str, message: str, media: list = None) -> dict:
        return {
            "ok": True,
            "message_id": f"tw_dm_{user_id}",
            "sent_at": datetime.now().isoformat()
        }

class RedditConnector(BaseConnector):
    """Connecteur Reddit."""
    
    async def send_post(self, *, muse_id: str, caption: str, media: list, link_out: str, story: bool, reel: bool, nsfw_filter: bool) -> dict:
        # TODO: Implémenter l'intégration Reddit réelle
        return {
            "ok": True,
            "post_id": f"rd_{muse_id}_{int(datetime.now().timestamp())}",
            "url": f"https://reddit.com/r/mock/post_{muse_id}",
            "metrics": {
                "views": 300,
                "likes": 40,
                "comments": 8,
                "ctr": 0.12
            }
        }
    
    async def send_dm(self, *, muse_id: str, user_id: str, message: str, media: list = None) -> dict:
        return {
            "ok": True,
            "message_id": f"rd_dm_{user_id}",
            "sent_at": datetime.now().isoformat()
        }

class TikTokConnector(BaseConnector):
    """Connecteur TikTok."""
    
    async def send_post(self, *, muse_id: str, caption: str, media: list, link_out: str, story: bool, reel: bool, nsfw_filter: bool) -> dict:
        # TODO: Implémenter l'intégration TikTok réelle
        return {
            "ok": True,
            "post_id": f"tt_{muse_id}_{int(datetime.now().timestamp())}",
            "url": f"https://tiktok.com/@mock/video/{muse_id}",
            "metrics": {
                "views": 500,
                "likes": 80,
                "comments": 12,
                "ctr": 0.15
            }
        }
    
    async def send_dm(self, *, muse_id: str, user_id: str, message: str, media: list = None) -> dict:
        return {
            "ok": True,
            "message_id": f"tt_dm_{user_id}",
            "sent_at": datetime.now().isoformat()
        }

class TelegramConnector(BaseConnector):
    """Connecteur Telegram."""
    
    async def send_post(self, *, muse_id: str, caption: str, media: list, link_out: str, story: bool, reel: bool, nsfw_filter: bool) -> dict:
        # TODO: Implémenter l'intégration Telegram réelle
        return {
            "ok": True,
            "post_id": f"tg_{muse_id}_{int(datetime.now().timestamp())}",
            "url": f"https://t.me/mock/{muse_id}",
            "metrics": {
                "views": 100,
                "likes": 20,
                "comments": 4,
                "ctr": 0.10
            }
        }
    
    async def send_dm(self, *, muse_id: str, user_id: str, message: str, media: list = None) -> dict:
        return {
            "ok": True,
            "message_id": f"tg_dm_{user_id}",
            "sent_at": datetime.now().isoformat()
        }

class OnlyFansConnector(BaseConnector):
    """Connecteur OnlyFans (mock pour V1)."""
    
    async def send_post(self, *, muse_id: str, caption: str, media: list, link_out: str, story: bool, reel: bool, nsfw_filter: bool) -> dict:
        # Mock pour V1 - sera remplacé par webdriver plus tard
        return {
            "ok": True,
            "post_id": f"of_{muse_id}_{int(datetime.now().timestamp())}",
            "url": f"https://onlyfans.com/mock/posts/{muse_id}",
            "metrics": {
                "views": 80,
                "likes": 30,
                "comments": 2,
                "ctr": 0.20
            }
        }
    
    async def send_dm(self, *, muse_id: str, user_id: str, message: str, media: list = None) -> dict:
        return {
            "ok": True,
            "message_id": f"of_dm_{user_id}",
            "sent_at": datetime.now().isoformat()
        }

class ThreadsConnector(BaseConnector):
    """Connecteur Threads."""
    
    async def send_post(self, *, muse_id: str, caption: str, media: list, link_out: str, story: bool, reel: bool, nsfw_filter: bool) -> dict:
        # TODO: Implémenter l'intégration Threads réelle
        return {
            "ok": True,
            "post_id": f"th_{muse_id}_{int(datetime.now().timestamp())}",
            "url": f"https://threads.net/@mock/post/{muse_id}",
            "metrics": {
                "views": 120,
                "likes": 18,
                "comments": 3,
                "ctr": 0.07
            }
        }
    
    async def send_dm(self, *, muse_id: str, user_id: str, message: str, media: list = None) -> dict:
        return {
            "ok": True,
            "message_id": f"th_dm_{user_id}",
            "sent_at": datetime.now().isoformat()
        }

# Registry des connecteurs
registry = {
    "instagram": InstagramConnector(),
    "twitter": TwitterConnector(),
    "reddit": RedditConnector(),
    "tiktok": TikTokConnector(),
    "telegram": TelegramConnector(),
    "onlyfans": OnlyFansConnector(),
    "threads": ThreadsConnector(),
}

def get(name: str) -> Optional[BaseConnector]:
    """Récupère un connecteur par nom."""
    return registry.get(name)

def list_available() -> list:
    """Liste les plateformes disponibles."""
    return list(registry.keys())

def register(name: str, connector: BaseConnector):
    """Enregistre un nouveau connecteur."""
    registry[name] = connector

def unregister(name: str):
    """Désenregistre un connecteur."""
    if name in registry:
        del registry[name]
