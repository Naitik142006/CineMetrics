"""
CineMetrics — YouTube Trailer Buzz & Engagement Harvester
Fetches quantitative video metrics and audience comments via YouTube Data API v3,
fusing scale analytics with multilingual sentiment.
"""

import os
import math
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

import httpx
import pandas as pd
from dotenv import load_dotenv

from ml.nlp.sentiment_engine import CinemaSentimentEngine, calculate_composite_buzz_score

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TrailerBuzzHarvester")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY") or os.getenv("YOUTUBE_API_KEY")
YOUTUBE_BASE_URL = "https://www.googleapis.com/youtube/v3"


class TrailerBuzzHarvester:
    """
    Harvester for trailer engagement stats (views, likes, comments, velocity)
    and audience sentiment analysis.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or YOUTUBE_API_KEY
        self.sentiment_engine = CinemaSentimentEngine()
        if not self.api_key:
            logger.warning("No YouTube API Key found in environment.")

    def search_trailer(self, title: str, release_year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Searches YouTube for official theatrical trailer."""
        if not self.api_key:
            return None

        query = f"{title} {release_year or ''} official trailer".strip()
        url = f"{YOUTUBE_BASE_URL}/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 1,
            "relevanceLanguage": "en",
            "key": self.api_key,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    if items:
                        item = items[0]
                        vid = item["id"].get("videoId")
                        snippet = item.get("snippet", {})
                        return {
                            "video_id": vid,
                            "trailer_title": snippet.get("title"),
                            "channel_title": snippet.get("channelTitle"),
                            "published_at": snippet.get("publishedAt"),
                        }
                else:
                    logger.warning(f"YouTube search error ({resp.status_code}): {resp.text[:100]}")
        except Exception as e:
            logger.error(f"Failed to search trailer for {title}: {e}")
        return None

    def fetch_video_stats(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Fetches video engagement statistics (views, likes, comments)."""
        if not self.api_key or not video_id:
            return None

        url = f"{YOUTUBE_BASE_URL}/videos"
        params = {
            "part": "statistics,snippet,contentDetails",
            "id": video_id,
            "key": self.api_key,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    if items:
                        item = items[0]
                        stats = item.get("statistics", {})
                        snippet = item.get("snippet", {})
                        return {
                            "video_id": video_id,
                            "trailer_title": snippet.get("title"),
                            "channel_title": snippet.get("channelTitle"),
                            "published_at": snippet.get("publishedAt"),
                            "view_count": int(stats.get("viewCount", 0)),
                            "like_count": int(stats.get("likeCount", 0)),
                            "comment_count": int(stats.get("commentCount", 0)),
                            "duration": item.get("contentDetails", {}).get("duration", ""),
                        }
        except Exception as e:
            logger.error(f"Failed to fetch stats for video {video_id}: {e}")
        return None

    def fetch_video_comments(self, video_id: str, max_comments: int = 100) -> List[str]:
        """Fetches up to max_comments top-level audience comments."""
        if not self.api_key or not video_id:
            return []

        url = f"{YOUTUBE_BASE_URL}/commentThreads"
        comments = []
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(max_comments, 100),
            "textFormat": "plainText",
            "order": "relevance",
            "key": self.api_key,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    for item in items:
                        top = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                        text = top.get("textDisplay", "").strip()
                        if text:
                            comments.append(text)
                else:
                    logger.warning(f"Comments fetch error for {video_id} ({resp.status_code}): {resp.text[:100]}")
        except Exception as e:
            logger.error(f"Failed to fetch comments for video {video_id}: {e}")

        return comments

    def process_movie_trailer_buzz(
        self,
        movie_title: str,
        release_year: Optional[int] = None,
        release_date: Optional[str] = None,
        video_id: Optional[str] = None,
        max_comments: int = 50,
    ) -> Dict[str, Any]:
        """
        Complete pipeline for a single movie:
        1. Resolves trailer video ID
        2. Fetches engagement stats (views, likes, comments)
        3. Computes quantitative ratios & velocity
        4. Fetches and scores audience comments
        5. Computes composite Digital Buzz & Audience Anticipation Index
        """
        logger.info(f"Processing trailer buzz for '{movie_title}' ({release_year or 'N/A'})...")

        # 1. Video Discovery
        meta = None
        if video_id:
            meta = self.fetch_video_stats(video_id)
        if not meta:
            search_res = self.search_trailer(movie_title, release_year)
            if search_res and search_res.get("video_id"):
                meta = self.fetch_video_stats(search_res["video_id"])

        if not meta:
            logger.warning(f"Could not retrieve trailer for '{movie_title}'")
            return {
                "movie_title": movie_title,
                "release_year": release_year,
                "has_trailer_data": False,
                "composite_buzz_score": 50.0,
            }

        # 2. Quantitative Metrics
        views = meta.get("view_count", 0)
        likes = meta.get("like_count", 0)
        num_comments = meta.get("comment_count", 0)
        published_at_str = meta.get("published_at")

        log_views = round(math.log10(max(views, 1)), 4)
        like_ratio = round(likes / max(views, 1), 6)
        comment_ratio = round(num_comments / max(views, 1), 6)

        # Days elapsed since trailer drop
        days_since_trailer = 30.0
        if published_at_str:
            try:
                pub_dt = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                now_dt = datetime.now(timezone.utc)
                days_since_trailer = max((now_dt - pub_dt).days, 1.0)
            except Exception:
                days_since_trailer = 30.0

        daily_velocity = round(views / max(days_since_trailer, 1.0), 2)

        # Lead time: days between trailer and theatrical release
        trailer_lead_time_days = None
        if release_date and published_at_str:
            try:
                rel_dt = datetime.fromisoformat(release_date)
                pub_dt = datetime.fromisoformat(published_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
                trailer_lead_time_days = max((rel_dt - pub_dt).days, 0)
            except Exception:
                trailer_lead_time_days = None

        # 3. Comments & Sentiment Analysis
        comments = self.fetch_video_comments(meta["video_id"], max_comments=max_comments)
        sentiment_metrics = self.sentiment_engine.aggregate_movie_comments(comments)

        # 4. Composite Digital Buzz Index
        composite_buzz = calculate_composite_buzz_score(
            view_count=views,
            like_count=likes,
            comment_count=num_comments,
            net_polarity=sentiment_metrics["comment_sentiment_net_polarity"],
            days_since_trailer=days_since_trailer,
        )

        return {
            "movie_title": movie_title,
            "release_year": release_year,
            "youtube_video_id": meta["video_id"],
            "trailer_title": meta.get("trailer_title"),
            "channel_title": meta.get("channel_title"),
            "published_at": published_at_str,
            "has_trailer_data": True,
            # Quantitative Scale Features
            "trailer_view_count": views,
            "log_trailer_views": log_views,
            "trailer_like_count": likes,
            "trailer_comment_count": num_comments,
            "like_to_view_ratio": like_ratio,
            "comment_to_view_ratio": comment_ratio,
            "daily_view_velocity": daily_velocity,
            "trailer_lead_time_days": trailer_lead_time_days,
            # Qualitative Sentiment Features
            "total_comments_harvested": len(comments),
            "comment_sentiment_positive_ratio": sentiment_metrics["comment_sentiment_positive_ratio"],
            "comment_sentiment_negative_ratio": sentiment_metrics["comment_sentiment_negative_ratio"],
            "comment_sentiment_neutral_ratio": sentiment_metrics["comment_sentiment_neutral_ratio"],
            "comment_sentiment_net_polarity": sentiment_metrics["comment_sentiment_net_polarity"],
            "comment_sentiment_controversy_score": sentiment_metrics["comment_sentiment_controversy_score"],
            "dominant_language": sentiment_metrics["dominant_language"],
            "top_positive_keywords": sentiment_metrics["top_positive_keywords"],
            "top_negative_keywords": sentiment_metrics["top_negative_keywords"],
            # Unified Index
            "composite_buzz_score": composite_buzz,
        }

