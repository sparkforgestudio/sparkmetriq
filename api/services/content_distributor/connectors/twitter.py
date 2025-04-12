import os
import tweepy
from typing import Dict
from services.content_distributor.logger import log_step

@log_step("Connexion à l'API Twitter")
def create_twitter_client(model_info: Dict):
    return tweepy.Client(
        bearer_token=model_info["bearer_token"],
        consumer_key=model_info["api_key"],
        consumer_secret=model_info["api_key_secret"],
        access_token=model_info["access_token"],
        access_token_secret=model_info["access_token_secret"]
    )

@log_step("Publication sur Twitter")
async def publish_to_twitter(content: Dict, model_info: Dict):
    client = create_twitter_client(model_info)
    text = content.get("caption", "")
    media_url = content.get("media_url")

    if media_url:
        import requests
        from tempfile import NamedTemporaryFile

        # Télécharger le fichier temporairement
        response = requests.get(media_url)
        if response.status_code != 200:
            raise Exception("Erreur de téléchargement du média")

        with NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(response.content)
            tmp.flush()

            media = client.media_upload(filename=tmp.name)
            tweet = client.create_tweet(text=text, media_ids=[media.media_id])
            os.unlink(tmp.name)

        return {"status": "success", "tweet_id": tweet.data["id"]}
    else:
        tweet = client.create_tweet(text=text)
        return {"status": "success", "tweet_id": tweet.data["id"]}
