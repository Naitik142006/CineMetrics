"""
CineMetrics — OMDb (Open Movie Database / IMDb) API Service
Provides high-speed metadata, official IMDb poster resolution, Rotten Tomatoes ratings,
and theatrical box office actuals.
"""

import json
import logging
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any, List

from backend.app.core.config import settings

logger = logging.getLogger("OMDbService")


class OMDbService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OMDB_API_KEY or "4f4653ff"
        self.base_url = "http://www.omdbapi.com/"
        self._cache: Dict[str, Dict[str, Any]] = {}

    def fetch_movie_by_title(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches movie metadata, official IMDb theatrical poster, ratings, and box office by title.
        """
        if not title or not title.strip():
            return None

        clean_title = title.strip()
        cache_key = f"{clean_title.lower()}_{year}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        params = {
            "t": clean_title,
            "apikey": self.api_key,
        }
        if year:
            params["y"] = str(year)

        encoded_params = urllib.parse.urlencode(params)
        full_url = f"{self.base_url}?{encoded_params}"

        try:
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "CineMetrics-Intelligence/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            if payload.get("Response") != "True":
                logger.debug(f"OMDb lookup returned False for '{title}': {payload.get('Error')}")
                # Try search without year if year was passed and failed
                if year:
                    return self.fetch_movie_by_title(title, year=None)
                return None

            result = self._parse_omdb_payload(payload)
            self._cache[cache_key] = result
            return result

        except Exception as e:
            logger.warning(f"OMDb API request failed for '{title}': {e}")
            return None

    def fetch_movie_by_imdb_id(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """Fetches movie metadata by canonical IMDb tconst (e.g. tt1375666)."""
        if not imdb_id or not imdb_id.strip():
            return None

        clean_id = imdb_id.strip()
        if clean_id in self._cache:
            return self._cache[clean_id]

        params = {"i": clean_id, "apikey": self.api_key}
        encoded_params = urllib.parse.urlencode(params)
        full_url = f"{self.base_url}?{encoded_params}"

        try:
            req = urllib.request.Request(
                full_url,
                headers={"User-Agent": "CineMetrics-Intelligence/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            if payload.get("Response") != "True":
                return None

            result = self._parse_omdb_payload(payload)
            self._cache[clean_id] = result
            return result
        except Exception as e:
            logger.warning(f"OMDb request failed for IMDb ID '{imdb_id}': {e}")
            return None

    def _parse_omdb_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes raw OMDb response into clean typed dictionary."""
        # Parse Poster
        raw_poster = data.get("Poster")
        poster_url = raw_poster if raw_poster and raw_poster != "N/A" and raw_poster.startswith("http") else None

        # Parse Box Office (e.g. "$292,587,330" -> 292587330.0)
        box_office_usd = None
        raw_bo = data.get("BoxOffice")
        if raw_bo and raw_bo != "N/A":
            clean_bo = raw_bo.replace("$", "").replace(",", "").strip()
            try:
                box_office_usd = float(clean_bo)
            except ValueError:
                box_office_usd = None

        # Parse Ratings
        imdb_rating = None
        try:
            if data.get("imdbRating") and data.get("imdbRating") != "N/A":
                imdb_rating = float(data.get("imdbRating"))
        except ValueError:
            imdb_rating = None

        imdb_votes = None
        try:
            if data.get("imdbVotes") and data.get("imdbVotes") != "N/A":
                imdb_votes = int(data.get("imdbVotes").replace(",", "").strip())
        except ValueError:
            imdb_votes = None

        rotten_tomatoes_pct = None
        for r in data.get("Ratings", []):
            if r.get("Source") == "Rotten Tomatoes":
                val = r.get("Value", "").replace("%", "").strip()
                try:
                    rotten_tomatoes_pct = float(val)
                except ValueError:
                    pass

        metascore = None
        try:
            if data.get("Metascore") and data.get("Metascore") != "N/A":
                metascore = int(data.get("Metascore"))
        except ValueError:
            metascore = None

        # Parse Genres
        genres = []
        raw_genre = data.get("Genre")
        if raw_genre and raw_genre != "N/A":
            genres = [g.strip() for g in raw_genre.split(",") if g.strip()]

        # Parse Cast
        actors = []
        raw_actors = data.get("Actors")
        if raw_actors and raw_actors != "N/A":
            actors = [a.strip() for a in raw_actors.split(",") if a.strip()]

        return {
            "title": data.get("Title"),
            "year": data.get("Year"),
            "rated": data.get("Rated"),
            "released_date": data.get("Released") if data.get("Released") != "N/A" else None,
            "runtime": data.get("Runtime") if data.get("Runtime") != "N/A" else None,
            "genres": genres,
            "director": data.get("Director") if data.get("Director") != "N/A" else None,
            "actors": actors,
            "lead_actor": actors[0] if actors else None,
            "plot": data.get("Plot") if data.get("Plot") != "N/A" else None,
            "poster_url": poster_url,
            "imdb_id": data.get("imdbID"),
            "imdb_rating": imdb_rating,
            "imdb_votes": imdb_votes,
            "box_office_usd": box_office_usd,
            "metascore": metascore,
            "rotten_tomatoes_pct": rotten_tomatoes_pct,
            "production": data.get("Production") if data.get("Production") != "N/A" else None,
            "awards": data.get("Awards") if data.get("Awards") != "N/A" else None,
        }


omdb_service = OMDbService()
