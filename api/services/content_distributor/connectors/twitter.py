import os
import httpx
import tweepy
from tempfile import NamedTemporaryFile
from typing import Dict, Any

from api.services.content_distributor.logger import logger, log_step, log_platform_event


def create_twitter_client(model_info: Dict[str, Any]) -> tweepy.Client:
    """
    Initialise le client Twitter via Tweepy avec OAuth credentials.
    """
    bearer_token = model_info.get("bearer_token") or os.getenv("TWITTER_BEARER_TOKEN")
    consumer_key = model_info.get("api_key") or os.getenv("TWITTER_API_KEY")
    consumer_secret = model_info.get("api_key_secret") or os.getenv("TWITTER_API_KEY_SECRET")
    access_token = model_info.get("access_token") or os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = model_info.get("access_token_secret") or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    
    return tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

@log_step
async def publish_to_twitter(content: Dict[str, Any], model_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publie un tweet, optionnellement avec média, puis log l'événement.
    """
    client = create_twitter_client(model_info)
    text = content.get("text") or content.get("caption", "")
    media_url = content.get("media_url")
    agency_id = model_info.get("agency_id", "")
    muse_id = model_info.get("muse_id", "")
    content_id = content.get("id", "")

    try:
        if media_url:
            # Télécharger le média
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.get(media_url)
                resp.raise_for_status()
                suffix = os.path.splitext(media_url)[1] or ".jpg"
                with NamedTemporaryFile(delete=False, suffix=suffix) as tmpfile:
                    tmpfile.write(resp.content)
                    tmpfile.flush()
                    media = client.media_upload(filename=tmpfile.name)
                    tweet = client.create_tweet(text=text, media_ids=[media.media_id])
            os.unlink(tmpfile.name)
        else:
            tweet = client.create_tweet(text=text)

        tweet_id = tweet.data.get("id")
        # Log de l'événement
        await log_platform_event(
            platform="twitter",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="success",
            message=f"Tweet publié: {tweet_id}",
            metadata={"tweet_id": tweet_id}
        )
        return {"status": "success", "tweet_id": tweet_id}

    except Exception as e:
        # Log de l'erreur
        await log_platform_event(
            platform="twitter",
            agency_id=agency_id,
            muse_id=muse_id,
            content_id=content_id,
            status="error",
            message=str(e),
            metadata={}
        )
        logger.error(f"Erreur publish_to_twitter: {e}")
        return {"status": "error", "reason": str(e)}
