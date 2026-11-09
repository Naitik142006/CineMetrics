"""
CineMetrics — Production TMDB API Client with DoH Sinkhole Bypass
Integrates TMDB v3 API with rate-limiting, retries, and Google DNS-over-HTTPS (DoH)
resolution to bypass Indian ISP DNS blocks (e.g., Reliance Jio, Airtel).
"""

import os
import time
import socket
import logging
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TMDBClient")

TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# DNS-over-HTTPS (DoH) Fallback Engine for Indian ISPs
_RESOLVED_TMDB_IPS = ["13.224.245.47", "13.224.245.92", "13.224.245.44", "13.224.245.63"]
try:
    _doh_resp = requests.get("https://dns.google/resolve?name=api.themoviedb.org", timeout=3.0)
    if _doh_resp.status_code == 200:
        _answers = _doh_resp.json().get("Answer", [])
        _ips = [a["data"] for a in _answers if a.get("type") == 1]
        if _ips:
            _RESOLVED_TMDB_IPS = _ips
except Exception:
    pass

_orig_getaddrinfo = socket.getaddrinfo


def _tmdb_custom_getaddrinfo(host, port, *args, **kwargs):
    if host in ("api.themoviedb.org", "themoviedb.org"):
        return _orig_getaddrinfo(_RESOLVED_TMDB_IPS[0], port, *args, **kwargs)
    return _orig_getaddrinfo(host, port, *args, **kwargs)


socket.getaddrinfo = _tmdb_custom_getaddrinfo


class ProductionTMDBClient:
    """
    Robust TMDB client with connection pooling, keep-alive, and automatic retries.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or TMDB_API_KEY
        if not self.api_key or self.api_key == "your_tmdb_api_key_here":
            raise ValueError("Missing TMDB_API_KEY in environment or constructor.")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "CineMetrics-Discovery/1.0",
        })
        # Configure connection pooling and retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.delay_seconds = 0.20

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Performs rate-limited GET request with keep-alive and retry backoff."""
        url = f"{TMDB_API_BASE_URL}{endpoint}"
        query_params = {"api_key": self.api_key}
        if params:
            query_params.update(params)

        for attempt in range(3):
            try:
                time.sleep(self.delay_seconds)
                resp = self.session.get(url, params=query_params, timeout=10.0)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 2))
                    logger.warning(f"Rate limited (429). Backing off for {retry_after}s...")
                    time.sleep(retry_after)
                elif resp.status_code == 404:
                    return None
                else:
                    logger.warning(f"TMDB {endpoint} returned status {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {endpoint}: {e}")
                time.sleep(0.5 * (attempt + 1))
        return None

    def get_upcoming_movies(self, region: str = "IN", page: int = 1) -> Dict[str, Any]:
        """Queries /movie/upcoming for a specific region and page."""
        params = {"region": region, "page": page, "language": "en-US"}
        return self._get("/movie/upcoming", params) or {}

    def discover_movies_in_range(
        self,
        start_date: str,
        end_date: str,
        original_language: Optional[str] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """Queries /discover/movie with release date range and optional language."""
        params = {
            "primary_release_date.gte": start_date,
            "primary_release_date.lte": end_date,
            "sort_by": "popularity.desc",
            "page": page,
        }
        if original_language:
            params["with_original_language"] = original_language
        return self._get("/discover/movie", params) or {}

    def get_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """Queries /movie/{id} for runtime, budget, status, genres, production companies."""
        return self._get(f"/movie/{tmdb_id}", {"append_to_response": "credits,videos"})

    def get_trending_movies(self, time_window: str = "week") -> Dict[str, Any]:
        """Queries /trending/movie/{time_window}."""
        return self._get(f"/trending/movie/{time_window}") or {}
