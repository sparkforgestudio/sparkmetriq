import requests
import logging
from api.schemas.payload_schema import PublicContentPayload
from services.content_distributor.logger import logger

logger = logging.getLogger(__name__)

class RedditConnector:
    def __init__(self, client_id: str, client_secret: str, username: str, password: str, user_agent: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.user_agent = user_agent
        self.access_token = self._authenticate()

    def _authenticate(self):
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        data = {
            'grant_type': 'password',
            'username': self.username,
            'password': self.password
        }
        headers = {'User-Agent': self.user_agent}

        response = requests.post("https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers=headers)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            logger.error(f"Reddit auth failed: {response.text}")
            return None

    def publish(self, payload: PublicContentPayload):
        if not self.access_token:
            raise ValueError("Authentication to Reddit failed")

        headers = {
            "Authorization": f"bearer {self.access_token}",
            "User-Agent": self.user_agent
        }

        post_data = {
            "sr": payload.muse_id,  # Nom du subreddit
            "title": payload.caption or "New Post",
            "kind": "link" if payload.type in ["image", "video"] else "self",
        }

        # Reddit ne supporte pas directement les carrousels, stories ou shorts
        if payload.type in ["image", "video"] and payload.media:
            post_data["url"] = payload.media[0].url
        elif payload.type == "text":
            post_data["text"] = payload.caption or ""
        else:
            raise NotImplementedError(f"RedditConnector: Unsupported type {payload.type}")

        res = requests.post("https://oauth.reddit.com/api/submit", headers=headers, data=post_data)

        if res.status_code != 200:
            logger.error(f"Failed to publish to Reddit: {res.text}")
            return {"status": "error", "detail": res.text}

        return {"status": "success", "response": res.json()}


async def publish_to_reddit(content, model_info):
    # implémentation réelle ici
    pass