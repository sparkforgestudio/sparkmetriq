import os
import httpx
from typing import Dict, Any, Optional
from api.services.content_distributor.logger import logger, log_step, log_platform_event

# Charger les variables d'environnement Reddit
REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME: str = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASSWORD: str = os.getenv("REDDIT_PASSWORD", "")
REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "content-distributor-bot/0.1")

OAUTH_URL = "https://www.reddit.com/api/v1/access_token"
SUBMIT_URL = "https://oauth.reddit.com/api/submit"

class RedditConnector:
    def __init__(self) -> None:
        self.client_id = REDDIT_CLIENT_ID
        self.client_secret = REDDIT_CLIENT_SECRET
        self.username = REDDIT_USERNAME
        self.password = REDDIT_PASSWORD
        self.user_agent = REDDIT_USER_AGENT
        self.access_token: Optional[str] = None

    async def authenticate(self) -> str:
        """
        Obtient un jeton d'accès OAuth2 via grant_type=password.
        """
        auth = (self.client_id, self.client_secret)
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password
        }
        headers = {"User-Agent": self.user_agent}
        async with httpx.AsyncClient() as client:
            resp = await client.post(OAUTH_URL, auth=auth, data=data, headers=headers)
            resp.raise_for_status()
            token = resp.json().get("access_token")
            self.access_token = token
            return token  # type: ignore

    async def submit_post(
        self,
        sr: str,
        title: str,
        kind: str,
        media_url: Optional[str] = None,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Soumet un post sur Reddit (self ou link post).
        """
        headers = {
            "Authorization": f"bearer {self.access_token}",
            "User-Agent": self.user_agent
        }
        payload: Dict[str, Any] = {"sr": sr, "title": title, "kind": kind}
        if media_url:
            payload["url"] = media_url
        if text and kind == "self":
            payload["text"] = text
        async with httpx.AsyncClient() as client:
            resp = await client.post(SUBMIT_URL, headers=headers, data=payload)
            resp.raise_for_status()
            return resp.json()

@log_step
async def publish_to_reddit(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie du contenu sur Reddit et journalise l'événement.
    """
    connector = RedditConnector()
    agency_id = model_info.get("agency_id", "")
    muse_id = model_info.get("muse_id", "")
    content_id = content.get("id", "")
    sr = content.get("platform") or muse_id
    title = content.get("text") or content.get("caption", "")
    media_list = content.get("media", [])

    try:
        if not connector.access_token:
            await connector.authenticate()

        kind = "self"
        media_url = None
        text_body = None
        if media_list:
            media_url = media_list[0].get("url")
            kind = "link"
        else:
            text_body = title

        response = await connector.submit_post(
            sr=sr,
            title=title,
            kind=kind,
            media_url=media_url,
            text=text_body
        )

        await log_platform_event(
            platform="reddit",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="success",
            message="Publication réussie sur Reddit",
            metadata={"response": response}
        )
        return {"status": "success", "data": response}
    except Exception as e:
        await log_platform_event(
            platform="reddit",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="error",
            message=str(e),
            metadata={}
        )
        logger.error(f"Erreur publish_to_reddit: {e}")
        return {"status": "error", "reason": str(e)}
