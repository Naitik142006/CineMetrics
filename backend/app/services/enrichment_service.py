"""
CineMetrics — Movie Metadata & Feature Enrichment Service
Enriches newly discovered TMDB movie candidates with credits, directors, cast, genres,
franchise detection, industry classification, and official YouTube trailer keys.
"""

import re
import logging
from typing import Dict, List, Optional, Any

from backend.app.services.tmdb_client import ProductionTMDBClient

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("EnrichmentService")

# Regional Indian Cinema Language Mapping
INDIAN_LANG_INDUSTRY_MAP: Dict[str, str] = {
    "hi": "Bollywood",
    "te": "Tollywood",
    "ta": "Kollywood",
    "ml": "Mollywood",
    "kn": "Sandalwood",
    "bn": "Bengali Cinema",
    "pa": "Punjabi Cinema",
    "mr": "Marathi Cinema",
}


class EnrichmentService:
    """
    Enriches raw TMDB candidate records into fully qualified CineMetrics movie entities.
    """

    def __init__(self, tmdb_client: Optional[ProductionTMDBClient] = None):
        self.tmdb_client = tmdb_client or ProductionTMDBClient()

    def detect_industry(self, original_language: str, production_countries: List[str]) -> str:
        """Determines cinematic territory industry."""
        lang = (original_language or "").lower()
        if lang in INDIAN_LANG_INDUSTRY_MAP:
            return INDIAN_LANG_INDUSTRY_MAP[lang]
        if "IN" in production_countries:
            return "Indian Cinema"
        if lang == "en":
            return "Hollywood"
        return "Global"

    def detect_franchise(self, title: str, belongs_to_collection: Optional[Dict]) -> bool:
        """Determines if the film is part of a franchise or sequel."""
        if belongs_to_collection is not None:
            return True
        title_lower = title.lower()
        patterns = [
            r"\bpart\s*(\d+|two|three|four|ii|iii|iv)\b",
            r"\bchapter\s*(\d+|two|three|four|ii|iii|iv)\b",
            r"\b\d+\b",  # e.g., "Krrish 3", "Dhoom 2"
            r"\b(returns|reloaded|revolution|resurrection|awakens|forever|legacy|begins)\b",
            r"\b(volume|vol\.?)\s*\d+\b",
        ]
        return any(re.search(p, title_lower) for p in patterns)

    def extract_trailer_key(self, videos_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extracts the best official YouTube trailer video key."""
        if not videos_data:
            return None
        results = videos_data.get("results", [])
        # Prioritize official theatrical trailers
        trailers = [
            v for v in results
            if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser")
        ]
        if not trailers:
            return None

        # Prefer official Trailer over Teaser
        for v in trailers:
            if v.get("type") == "Trailer" and v.get("official") is True:
                return v.get("key")
        for v in trailers:
            if v.get("type") == "Trailer":
                return v.get("key")
        return trailers[0].get("key")

    def enrich_movie(self, raw_candidate: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enriches a discovered candidate via TMDB details, credits, and videos.
        """
        tmdb_id = raw_candidate.get("id") or raw_candidate.get("tmdb_id")
        if not tmdb_id:
            return None

        details = self.tmdb_client.get_movie_details(int(tmdb_id))
        if not details:
            logger.warning(f"Failed to fetch details for TMDB ID {tmdb_id}")
            return None

        # Basic metadata
        title = details.get("title") or raw_candidate.get("title", "Unknown")
        original_title = details.get("original_title", title)
        release_date = details.get("release_date") or raw_candidate.get("release_date", "")
        release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

        # Genres
        genres = [g.get("name") for g in details.get("genres", [])]
        primary_genre = genres[0] if genres else "Drama"
        genre_count = len(genres)

        # Production & Geography
        prod_countries = [c.get("iso_3166_1") for c in details.get("production_countries", [])]
        orig_lang = details.get("original_language", "en")
        industry = self.detect_industry(orig_lang, prod_countries)

        # Budget & Financials
        raw_budget = float(details.get("budget", 0) or 0)
        runtime = float(details.get("runtime", 0) or 120.0)
        # Clean budget: if reported budget is unrealistically small or 0, flag for Stage 1 imputation
        budget_clean_usd = raw_budget if raw_budget >= 100_000 else None

        # Budget tier categorization
        if budget_clean_usd is not None:
            if budget_clean_usd >= 100_000_000:
                budget_tier = "Tentpole"
            elif budget_clean_usd >= 40_000_000:
                budget_tier = "High"
            elif budget_clean_usd >= 10_000_000:
                budget_tier = "Medium"
            elif budget_clean_usd >= 2_000_000:
                budget_tier = "Low"
            else:
                budget_tier = "Micro"
        else:
            budget_tier = "Medium"  # Default prior

        # Credits: Director and Cast
        credits = details.get("credits", {})
        crew = credits.get("crew", [])
        cast = credits.get("cast", [])

        directors = [m.get("name") for m in crew if m.get("job") == "Director"]
        primary_director = directors[0] if directors else "Unknown"

        top_cast = [c.get("name") for c in cast[:5]]
        lead_actor = top_cast[0] if top_cast else "Unknown"

        # Franchise Detection
        is_franchise = self.detect_franchise(title, details.get("belongs_to_collection"))

        # Videos: Official YouTube Trailer Key
        youtube_trailer_key = self.extract_trailer_key(details.get("videos"))

        # Data Readiness Score (0 to 100)
        readiness = 0
        if title and release_date:
            readiness += 25
        if primary_director != "Unknown":
            readiness += 20
        if lead_actor != "Unknown":
            readiness += 20
        if genres and runtime > 0:
            readiness += 15
        if youtube_trailer_key:
            readiness += 15
        if budget_clean_usd:
            readiness += 5

        # Lifecycle Stage
        if youtube_trailer_key:
            stage = "Stage 2 (Trailer Released)"
        elif readiness >= 65:
            stage = "Stage 1 (Pre-Trailer Announcement)"
        else:
            stage = "Stage 0 (Early Discovery)"

        return {
            "canonical_id": f"tmdb_{tmdb_id}",
            "tmdb_id": int(tmdb_id),
            "primary_title": title,
            "original_title": original_title,
            "release_date": release_date,
            "release_year": release_year,
            "primary_genre": primary_genre,
            "genre_count": genre_count,
            "industry": industry,
            "original_language": orig_lang,
            "budget_clean_usd": budget_clean_usd,
            "budget_tier": budget_tier,
            "runtime_minutes_clean": runtime,
            "director": primary_director,
            "lead_actor": lead_actor,
            "top_cast": ", ".join(top_cast),
            "is_sequel_or_franchise": 1.0 if is_franchise else 0.0,
            "youtube_trailer_id": youtube_trailer_key,
            "prediction_readiness_score": readiness,
            "prediction_lifecycle_stage": stage,
            "popularity": float(details.get("popularity", 0.0)),
            "overview": details.get("overview", ""),
        }
