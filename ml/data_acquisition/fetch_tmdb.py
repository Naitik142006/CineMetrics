"""
CineMetrics — The Movie Database (TMDB) API Acquisition Engine
Pulls upcoming movie releases, regional discovery catalogs, credits, and external IDs.

Source: https://developer.themoviedb.org/docs
Licensing: Free non-commercial with attribution.
Requires: TMDB_API_KEY in .env
"""

import json
import logging
import socket
import time
from pathlib import Path
from typing import Dict, List, Optional
import httpx
import pandas as pd
import requests

from ml.data_acquisition.config import TMDB_API_BASE_URL, TMDB_API_KEY, TMDB_RAW_DIR

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TMDBAcquisition")

# Robust DNS Resolution for TMDB (bypasses ISP sinkholes e.g. Jio/Airtel in India)
_RESOLVED_TMDB_IPS = ["13.224.245.47", "13.224.245.92", "13.224.245.44", "13.224.245.63"]
try:
    with httpx.Client(timeout=3.0) as _dns_client:
        _doh_resp = _dns_client.get("https://dns.google/resolve?name=api.themoviedb.org")
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


class TMDBClient:
    """Client for interacting with TMDB v3 API with rate limiting and retry handling."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or TMDB_API_KEY
        if not self.api_key or self.api_key == "your_tmdb_api_key_here":
            raise ValueError(
                "Missing TMDB_API_KEY!\n"
                "Please obtain a free API key at: https://www.themoviedb.org/signup\n"
                "Then add it to your '.env' file: TMDB_API_KEY=your_key_here\n"
                "Or pass it directly: TMDBClient(api_key='...')"
            )
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.delay_seconds = 0.25  # Max 4 requests/sec (well within 40 req/10s limit)

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Executes rate-limited GET request with retry on 429."""
        url = f"{TMDB_API_BASE_URL}{endpoint}"
        query_params = {"api_key": self.api_key}
        if params:
            query_params.update(params)

        for attempt in range(3):
            time.sleep(self.delay_seconds)
            try:
                response = self.session.get(url, params=query_params, timeout=20)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2))
                    logger.warning(f"Rate limited by TMDB. Backing off for {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    logger.error(f"Failed to fetch {endpoint} after 3 attempts: {e}")
                    raise
                time.sleep(1.0 * (attempt + 1))
        return {}

    def fetch_upcoming(self, region: Optional[str] = None, page: int = 1) -> Dict:
        """Fetches upcoming movies (/movie/upcoming)."""
        params = {"page": page}
        if region:
            params["region"] = region
        return self._get("/movie/upcoming", params)

    def discover_movies(
        self,
        language: str = "hi",
        year: Optional[int] = None,
        sort_by: str = "popularity.desc",
        page: int = 1,
    ) -> Dict:
        """Discovers movies by language, year, and sorting (/discover/movie)."""
        params = {
            "with_original_language": language,
            "sort_by": sort_by,
            "page": page,
        }
        if year:
            params["primary_release_year"] = year
        return self._get("/discover/movie", params)

    def fetch_movie_details(self, movie_id: int) -> Dict:
        """Fetches movie metadata (/movie/{id})."""
        return self._get(f"/movie/{movie_id}")

    def fetch_movie_credits(self, movie_id: int) -> Dict:
        """Fetches movie cast and crew (/movie/{id}/credits)."""
        return self._get(f"/movie/{movie_id}/credits")

    def fetch_movie_external_ids(self, movie_id: int) -> Dict:
        """Fetches external IDs (IMDb tconst, Wikidata, etc.) (/movie/{id}/external_ids)."""
        return self._get(f"/movie/{movie_id}/external_ids")


def harvest_upcoming_movies(regions: List[str] = ["IN", "US"], max_pages: int = 5) -> Path:
    """
    Harvests current upcoming movies across target regions and saves to Parquet.
    """
    client = TMDBClient()
    logger.info(f"Harvesting upcoming movies for regions: {regions}...")
    all_movies = []

    for region in regions:
        for page in range(1, max_pages + 1):
            try:
                data = client.fetch_upcoming(region=region, page=page)
                results = data.get("results", [])
                if not results:
                    break
                for m in results:
                    m["discovered_region"] = region
                    all_movies.append(m)
                total_pages = data.get("total_pages", 1)
                if page >= total_pages:
                    break
            except Exception as e:
                logger.error(f"Error fetching upcoming page {page} for region {region}: {e}")

    df_upcoming = pd.DataFrame(all_movies).drop_duplicates(subset=["id"])
    parquet_path = TMDB_RAW_DIR / "tmdb_upcoming.parquet"
    df_upcoming.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)
    logger.info(f"Saved {len(df_upcoming):,} upcoming movies to {parquet_path.name}.")
    return parquet_path


def harvest_indian_cinema_catalog(
    languages: List[str] = ["hi", "te", "ta", "ml", "kn"],
    start_year: int = 2015,
    end_year: int = 2024,
    pages_per_year: int = 3,
) -> Path:
    """
    Harvests regional Indian cinema catalogs (Bollywood, Tollywood, Kollywood, Mollywood, Sandalwood)
    and saves to Parquet.
    """
    client = TMDBClient()
    logger.info(f"Harvesting Indian cinema catalog ({languages}) from {start_year} to {end_year}...")
    collected = []

    for lang in languages:
        for year in range(start_year, end_year + 1):
            for page in range(1, pages_per_year + 1):
                try:
                    data = client.discover_movies(language=lang, year=year, page=page)
                    results = data.get("results", [])
                    if not results:
                        break
                    for m in results:
                        m["queried_language"] = lang
                        m["queried_year"] = year
                        collected.append(m)
                except Exception as e:
                    logger.warning(f"Error discovering {lang} {year} page {page}: {e}")

    df_indian = pd.DataFrame(collected).drop_duplicates(subset=["id"])
    parquet_path = TMDB_RAW_DIR / "tmdb_indian_catalog.parquet"
    df_indian.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)
    logger.info(f"Saved {len(df_indian):,} Indian cinema records to {parquet_path.name}.")
    return parquet_path


if __name__ == "__main__":
    try:
        harvest_upcoming_movies()
    except ValueError as e:
        logger.error(e)

