# api/services/ai_marketing/data_collector.py
"""
Pipeline de collecte et structuration des données multi-plateformes
via Apify et autres scrapers.
"""

import asyncio
import httpx
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from api.services.ai_marketing.logger import logger

class PlatformType(str, Enum):
    """Types de plateformes supportées."""
    ONLYFANS = "onlyfans"
    FANSLY = "fansly"
    FANVUE = "fanvue"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    REDDIT = "reddit"
    THREADS = "threads"

@dataclass
class CreatorProfile:
    """Profil d'un créateur."""
    creator_id: str
    username: str
    niche: str
    platforms: List[PlatformType]
    followers: Dict[str, int]
    engagement_rate: Dict[str, float]
    pricing: Dict[str, float]
    content_types: List[str]
    demographics: Dict[str, Any]
    performance_metrics: Dict[str, Any]

@dataclass
class ContentData:
    """Données de contenu."""
    content_id: str
    platform: PlatformType
    creator_id: str
    content_type: str
    title: str
    description: str
    hashtags: List[str]
    engagement: Dict[str, int]
    performance: Dict[str, float]
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class FanData:
    """Données des fans."""
    fan_id: str
    creator_id: str
    platform: PlatformType
    subscription_status: str
    spending_history: List[Dict[str, Any]]
    engagement_level: str
    demographics: Dict[str, Any]
    last_activity: datetime

class DataCollector:
    """Collecteur de données multi-plateformes."""
    
    def __init__(self):
        self.apify_api_key = os.getenv("APIFY_API_KEY")
        self.apify_base_url = "https://api.apify.com/v2"
        self.session = None
        
    async def __aenter__(self):
        self.session = httpx.AsyncClient()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

    async def collect_onlyfans_data(self, creator_username: str) -> Dict[str, Any]:
        """Collecte les données OnlyFans via Apify."""
        try:
            # Configuration du scraper Apify OnlyFans
            scraper_config = {
                "usernames": [creator_username],
                "maxPosts": 100,
                "maxComments": 50,
                "includeComments": True,
                "includeMedia": True
            }
            
            # Lancement du scraper
            run_id = await self._start_apify_scraper("onlyfans-scraper", scraper_config)
            
            # Récupération des résultats
            results = await self._get_apify_results(run_id)
            
            # Structuration des données
            structured_data = self._structure_onlyfans_data(results)
            
            logger.info(f"Données OnlyFans collectées pour {creator_username}: {len(structured_data.get('posts', []))} posts")
            return structured_data
            
        except Exception as e:
            logger.error(f"Erreur collecte OnlyFans {creator_username}: {e}")
            return {}

    async def collect_instagram_data(self, creator_username: str) -> Dict[str, Any]:
        """Collecte les données Instagram via Apify."""
        try:
            scraper_config = {
                "usernames": [creator_username],
                "resultsType": "posts",
                "resultsLimit": 100,
                "includeStories": True,
                "includeHighlights": True
            }
            
            run_id = await self._start_apify_scraper("instagram-scraper", scraper_config)
            results = await self._get_apify_results(run_id)
            structured_data = self._structure_instagram_data(results)
            
            logger.info(f"Données Instagram collectées pour {creator_username}: {len(structured_data.get('posts', []))} posts")
            return structured_data
            
        except Exception as e:
            logger.error(f"Erreur collecte Instagram {creator_username}: {e}")
            return {}

    async def collect_tiktok_data(self, creator_username: str) -> Dict[str, Any]:
        """Collecte les données TikTok via Apify."""
        try:
            scraper_config = {
                "usernames": [creator_username],
                "resultsLimit": 100,
                "includeComments": True,
                "includeUserInfo": True
            }
            
            run_id = await self._start_apify_scraper("tiktok-scraper", scraper_config)
            results = await self._get_apify_results(run_id)
            structured_data = self._structure_tiktok_data(results)
            
            logger.info(f"Données TikTok collectées pour {creator_username}: {len(structured_data.get('videos', []))} vidéos")
            return structured_data
            
        except Exception as e:
            logger.error(f"Erreur collecte TikTok {creator_username}: {e}")
            return {}

    async def collect_reddit_data(self, subreddits: List[str], keywords: List[str]) -> Dict[str, Any]:
        """Collecte les données Reddit via Apify."""
        try:
            scraper_config = {
                "subreddits": subreddits,
                "searchTerms": keywords,
                "resultsLimit": 200,
                "includeComments": True,
                "sort": "hot"
            }
            
            run_id = await self._start_apify_scraper("reddit-scraper", scraper_config)
            results = await self._get_apify_results(run_id)
            structured_data = self._structure_reddit_data(results)
            
            logger.info(f"Données Reddit collectées: {len(structured_data.get('posts', []))} posts")
            return structured_data
            
        except Exception as e:
            logger.error(f"Erreur collecte Reddit: {e}")
            return {}

    async def collect_twitter_data(self, creator_username: str) -> Dict[str, Any]:
        """Collecte les données Twitter/X via Apify."""
        try:
            scraper_config = {
                "usernames": [creator_username],
                "resultsLimit": 100,
                "includeReplies": True,
                "includeRetweets": False
            }
            
            run_id = await self._start_apify_scraper("twitter-scraper", scraper_config)
            results = await self._get_apify_results(run_id)
            structured_data = self._structure_twitter_data(results)
            
            logger.info(f"Données Twitter collectées pour {creator_username}: {len(structured_data.get('tweets', []))} tweets")
            return structured_data
            
        except Exception as e:
            logger.error(f"Erreur collecte Twitter {creator_username}: {e}")
            return {}

    async def _start_apify_scraper(self, scraper_id: str, config: Dict[str, Any]) -> str:
        """Lance un scraper Apify."""
        if not self.session:
            raise Exception("Session HTTP non initialisée")
            
        url = f"{self.apify_base_url}/acts/{scraper_id}/runs"
        headers = {
            "Authorization": f"Bearer {self.apify_api_key}",
            "Content-Type": "application/json"
        }
        
        response = await self.session.post(url, headers=headers, json=config)
        response.raise_for_status()
        
        run_data = response.json()
        return run_data["data"]["id"]

    async def _get_apify_results(self, run_id: str) -> List[Dict[str, Any]]:
        """Récupère les résultats d'un scraper Apify."""
        if not self.session:
            raise Exception("Session HTTP non initialisée")
            
        # Attendre la completion du scraper
        await self._wait_for_completion(run_id)
        
        # Récupérer les résultats
        url = f"{self.apify_base_url}/actor-runs/{run_id}/dataset/items"
        headers = {"Authorization": f"Bearer {self.apify_api_key}"}
        
        response = await self.session.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()

    async def _wait_for_completion(self, run_id: str, timeout: int = 300):
        """Attend la completion d'un scraper Apify."""
        if not self.session:
            raise Exception("Session HTTP non initialisée")
            
        url = f"{self.apify_base_url}/actor-runs/{run_id}"
        headers = {"Authorization": f"Bearer {self.apify_api_key}"}
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            response = await self.session.get(url, headers=headers)
            response.raise_for_status()
            
            run_data = response.json()
            status = run_data["data"]["status"]
            
            if status == "SUCCEEDED":
                return
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                raise Exception(f"Scraper échoué avec le statut: {status}")
                
            await asyncio.sleep(5)

    def _structure_onlyfans_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure les données OnlyFans."""
        structured = {
            "profile": {},
            "posts": [],
            "analytics": {},
            "fans": []
        }
        
        for item in raw_data:
            if item.get("type") == "profile":
                structured["profile"] = {
                    "username": item.get("username"),
                    "display_name": item.get("displayName"),
                    "subscriber_count": item.get("subscriberCount", 0),
                    "subscription_price": item.get("subscriptionPrice", 0),
                    "bio": item.get("bio", ""),
                    "verified": item.get("verified", False)
                }
            elif item.get("type") == "post":
                structured["posts"].append({
                    "post_id": item.get("id"),
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "price": item.get("price", 0),
                    "likes": item.get("likesCount", 0),
                    "comments": item.get("commentsCount", 0),
                    "timestamp": item.get("createdAt"),
                    "media_type": item.get("mediaType"),
                    "is_premium": item.get("isPremium", False)
                })
        
        return structured

    def _structure_instagram_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure les données Instagram."""
        structured = {
            "profile": {},
            "posts": [],
            "stories": [],
            "analytics": {}
        }
        
        for item in raw_data:
            if item.get("type") == "profile":
                structured["profile"] = {
                    "username": item.get("username"),
                    "full_name": item.get("fullName"),
                    "followers": item.get("followersCount", 0),
                    "following": item.get("followingCount", 0),
                    "posts_count": item.get("postsCount", 0),
                    "bio": item.get("biography", ""),
                    "verified": item.get("isVerified", False)
                }
            elif item.get("type") == "post":
                structured["posts"].append({
                    "post_id": item.get("id"),
                    "caption": item.get("caption", ""),
                    "likes": item.get("likesCount", 0),
                    "comments": item.get("commentsCount", 0),
                    "timestamp": item.get("timestamp"),
                    "media_type": item.get("mediaType"),
                    "hashtags": self._extract_hashtags(item.get("caption", "")),
                    "mentions": self._extract_mentions(item.get("caption", ""))
                })
        
        return structured

    def _structure_tiktok_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure les données TikTok."""
        structured = {
            "profile": {},
            "videos": [],
            "analytics": {}
        }
        
        for item in raw_data:
            if item.get("type") == "profile":
                structured["profile"] = {
                    "username": item.get("username"),
                    "display_name": item.get("displayName"),
                    "followers": item.get("followersCount", 0),
                    "following": item.get("followingCount", 0),
                    "videos_count": item.get("videosCount", 0),
                    "bio": item.get("signature", ""),
                    "verified": item.get("verified", False)
                }
            elif item.get("type") == "video":
                structured["videos"].append({
                    "video_id": item.get("id"),
                    "description": item.get("description", ""),
                    "likes": item.get("likesCount", 0),
                    "comments": item.get("commentsCount", 0),
                    "shares": item.get("sharesCount", 0),
                    "views": item.get("viewsCount", 0),
                    "timestamp": item.get("timestamp"),
                    "hashtags": self._extract_hashtags(item.get("description", "")),
                    "audio": item.get("music", {}).get("title", "")
                })
        
        return structured

    def _structure_reddit_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure les données Reddit."""
        structured = {
            "posts": [],
            "comments": [],
            "trends": {}
        }
        
        for item in raw_data:
            if item.get("type") == "post":
                structured["posts"].append({
                    "post_id": item.get("id"),
                    "title": item.get("title", ""),
                    "content": item.get("text", ""),
                    "subreddit": item.get("subreddit"),
                    "upvotes": item.get("upvotes", 0),
                    "comments_count": item.get("commentsCount", 0),
                    "timestamp": item.get("createdAt"),
                    "author": item.get("author"),
                    "url": item.get("url")
                })
            elif item.get("type") == "comment":
                structured["comments"].append({
                    "comment_id": item.get("id"),
                    "content": item.get("text", ""),
                    "upvotes": item.get("upvotes", 0),
                    "timestamp": item.get("createdAt"),
                    "author": item.get("author"),
                    "post_id": item.get("postId")
                })
        
        return structured

    def _structure_twitter_data(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure les données Twitter/X."""
        structured = {
            "profile": {},
            "tweets": [],
            "analytics": {}
        }
        
        for item in raw_data:
            if item.get("type") == "profile":
                structured["profile"] = {
                    "username": item.get("username"),
                    "display_name": item.get("displayName"),
                    "followers": item.get("followersCount", 0),
                    "following": item.get("followingCount", 0),
                    "tweets_count": item.get("tweetsCount", 0),
                    "bio": item.get("description", ""),
                    "verified": item.get("verified", False)
                }
            elif item.get("type") == "tweet":
                structured["tweets"].append({
                    "tweet_id": item.get("id"),
                    "content": item.get("text", ""),
                    "likes": item.get("likesCount", 0),
                    "retweets": item.get("retweetsCount", 0),
                    "replies": item.get("repliesCount", 0),
                    "timestamp": item.get("timestamp"),
                    "hashtags": self._extract_hashtags(item.get("text", "")),
                    "mentions": self._extract_mentions(item.get("text", ""))
                })
        
        return structured

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extrait les hashtags d'un texte."""
        import re
        hashtags = re.findall(r'#\w+', text)
        return [tag.lower() for tag in hashtags]

    def _extract_mentions(self, text: str) -> List[str]:
        """Extrait les mentions d'un texte."""
        import re
        mentions = re.findall(r'@\w+', text)
        return [mention.lower() for mention in mentions]

    async def collect_all_platform_data(self, creator_username: str, platforms: List[PlatformType]) -> Dict[str, Any]:
        """Collecte les données de toutes les plateformes spécifiées."""
        all_data = {
            "creator_username": creator_username,
            "collection_timestamp": utcnow().isoformat(),
            "platforms": {}
        }
        
        tasks = []
        
        if PlatformType.ONLYFANS in platforms:
            tasks.append(self.collect_onlyfans_data(creator_username))
        if PlatformType.INSTAGRAM in platforms:
            tasks.append(self.collect_instagram_data(creator_username))
        if PlatformType.TIKTOK in platforms:
            tasks.append(self.collect_tiktok_data(creator_username))
        if PlatformType.TWITTER in platforms:
            tasks.append(self.collect_twitter_data(creator_username))
        
        # Exécuter toutes les collectes en parallèle
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Structurer les résultats
        platform_index = 0
        for platform in platforms:
            if platform_index < len(results):
                result = results[platform_index]
                if isinstance(result, Exception):
                    logger.error(f"Erreur collecte {platform}: {result}")
                    all_data["platforms"][platform.value] = {}
                else:
                    all_data["platforms"][platform.value] = result
                platform_index += 1
        
        return all_data

    async def analyze_content_performance(self, content_data: List[ContentData]) -> Dict[str, Any]:
        """Analyse les performances de contenu."""
        analysis = {
            "top_performing_content": [],
            "content_trends": {},
            "engagement_patterns": {},
            "optimal_posting_times": {},
            "hashtag_performance": {}
        }
        
        # Analyse des contenus les plus performants
        sorted_content = sorted(content_data, key=lambda x: x.engagement.get("total", 0), reverse=True)
        analysis["top_performing_content"] = sorted_content[:10]
        
        # Analyse des tendances de contenu
        content_types = {}
        for content in content_data:
            content_type = content.content_type
            if content_type not in content_types:
                content_types[content_type] = []
            content_types[content_type].append(content.engagement.get("total", 0))
        
        for content_type, engagements in content_types.items():
            analysis["content_trends"][content_type] = {
                "avg_engagement": sum(engagements) / len(engagements),
                "count": len(engagements),
                "max_engagement": max(engagements)
            }
        
        return analysis

    async def detect_trending_topics(self, reddit_data: Dict[str, Any], tiktok_data: Dict[str, Any]) -> List[str]:
        """Détecte les sujets tendance."""
        trending_topics = []
        
        # Analyse Reddit
        if "posts" in reddit_data:
            reddit_keywords = {}
            for post in reddit_data["posts"]:
                # Extraction de mots-clés (simplifié)
                words = post.get("title", "").lower().split()
                for word in words:
                    if len(word) > 3:  # Filtrer les mots courts
                        reddit_keywords[word] = reddit_keywords.get(word, 0) + 1
            
            # Top mots-clés Reddit
            top_reddit = sorted(reddit_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            trending_topics.extend([word for word, count in top_reddit if count > 2])
        
        # Analyse TikTok
        if "videos" in tiktok_data:
            tiktok_hashtags = {}
            for video in tiktok_data["videos"]:
                for hashtag in video.get("hashtags", []):
                    tiktok_hashtags[hashtag] = tiktok_hashtags.get(hashtag, 0) + 1
            
            # Top hashtags TikTok
            top_tiktok = sorted(tiktok_hashtags.items(), key=lambda x: x[1], reverse=True)[:10]
            trending_topics.extend([tag for tag, count in top_tiktok if count > 1])
        
        return list(set(trending_topics))  # Supprimer les doublons




