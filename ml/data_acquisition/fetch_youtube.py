"""
CineMetrics — YouTube Trailer Intelligence Ingestion Module
Harvests trailer metrics (views, likes, comments, publication date) using YouTube Data API v3.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import httpx
import pandas as pd

from ml.data_acquisition.config import BASE_DIR, YOUTUBE_DATA_API_KEY

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("YouTubeAcquisition")

YOUTUBE_RAW_DIR = BASE_DIR / "data" / "raw" / "youtube"
YOUTUBE_RAW_DIR.mkdir(parents=True, exist_ok=True)

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def check_youtube_credentials() -> bool:
    """Verifies that YouTube Data API Key is configured."""
    return bool(YOUTUBE_DATA_API_KEY and YOUTUBE_DATA_API_KEY != "your_youtube_data_api_key")


def search_movie_trailer(title: str, year: Optional[int] = None, api_key: str = YOUTUBE_DATA_API_KEY) -> Optional[Dict]:
    """
    Searches YouTube for the official trailer of a movie and returns video ID & snippet metadata.
    """
    if not check_youtube_credentials():
        logger.warning("YouTube Data API key is not configured.")
        return None

    query = f"{title} {year or ''} official trailer".strip()
    search_url = f"{YOUTUBE_API_BASE}/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "relevanceLanguage": "en",
        "key": api_key,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(search_url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if not items:
                    return None
                item = items[0]
                video_id = item["id"].get("videoId")
                snippet = item.get("snippet", {})
                return {
                    "video_id": video_id,
                    "channel_title": snippet.get("channelTitle"),
                    "published_at": snippet.get("publishedAt"),
                    "title": snippet.get("title"),
                    "description": snippet.get("description"),
                }
            elif resp.status_code == 403:
                logger.error(f"YouTube API Quota exceeded or invalid key: {resp.text}")
                return None
            else:
                logger.warning(f"YouTube search returned status {resp.status_code}: {resp.text}")
                return None
    except Exception as e:
        logger.error(f"Error querying YouTube search for '{title}': {e}")
        return None


def fetch_video_statistics(video_ids: List[str], api_key: str = YOUTUBE_DATA_API_KEY) -> Dict[str, Dict]:
    """
    Fetches engagement statistics (views, likes, comments) for up to 50 video IDs in a single batch call.
    """
    if not check_youtube_credentials() or not video_ids:
        return {}

    videos_url = f"{YOUTUBE_API_BASE}/videos"
    results = {}

    # Batch in chunks of 50 (YouTube API limit)
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        params = {
            "part": "statistics,contentDetails",
            "id": ",".join(chunk),
            "key": api_key,
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(videos_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("items", []):
                        vid = item["id"]
                        stats = item.get("statistics", {})
                        results[vid] = {
                            "view_count": int(stats.get("viewCount", 0)),
                            "like_count": int(stats.get("likeCount", 0)),
                            "comment_count": int(stats.get("commentCount", 0)),
                            "duration": item.get("contentDetails", {}).get("duration", ""),
                        }
                else:
                    logger.error(f"YouTube video stats query failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Error querying YouTube video statistics: {e}")

    return results


def harvest_trailer_metrics_sample(movie_titles: List[Dict]) -> Path:
    """
    Given a list of movie dicts with 'title' and optional 'year', harvests trailer metrics and saves to Parquet.
    """
    records = []
    logger.info(f"Harvesting YouTube trailer metrics for {len(movie_titles)} movies...")

    for m in movie_titles:
        title = m.get("title")
        year = m.get("year")
        meta = search_movie_trailer(title, year)
        if meta and meta.get("video_id"):
            vid = meta["video_id"]
            stats_dict = fetch_video_statistics([vid])
            stats = stats_dict.get(vid, {})
            records.append({
                "movie_title": title,
                "release_year": year,
                "youtube_video_id": vid,
                "trailer_title": meta.get("title"),
                "channel_title": meta.get("channel_title"),
                "published_at": meta.get("published_at"),
                "view_count": stats.get("view_count", 0),
                "like_count": stats.get("like_count", 0),
                "comment_count": stats.get("comment_count", 0),
                "harvested_at": datetime.now(timezone.utc).isoformat(),
            })

    output_file = YOUTUBE_RAW_DIR / "trailer_metrics.parquet"
    if records:
        df = pd.DataFrame(records)
        df.to_parquet(output_file, engine="pyarrow", compression="snappy", index=False)
        logger.info(f"Saved {len(df)} trailer metric records to {output_file}.")
    else:
        logger.warning("No trailer metrics were harvested.")

    return output_file


if __name__ == "__main__":
    if check_youtube_credentials():
        logger.info("Testing YouTube Data API v3 with benchmark movies...")
        sample_movies = [
            {"title": "Kalki 2898 AD", "year": 2024},
            {"title": "Jawan", "year": 2023},
            {"title": "Oppenheimer", "year": 2023},
            {"title": "Dune: Part Two", "year": 2024},
        ]
        harvest_trailer_metrics_sample(sample_movies)
    else:
        logger.warning("YouTube Data API credentials not configured.")
