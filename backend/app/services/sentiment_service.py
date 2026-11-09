"""
CineMetrics — Backend Sentiment & Trailer Intelligence Service
Provides asynchronous API interfaces for trailer buzz analytics, comment sentiment evaluation,
and digital anticipation index scoring for the FastAPI backend.
"""

import logging
from typing import Dict, List, Optional, Any

from ml.nlp.sentiment_engine import CinemaSentimentEngine, calculate_composite_buzz_score
from ml.nlp.trailer_buzz_harvester import TrailerBuzzHarvester

logger = logging.getLogger("SentimentService")


class SentimentService:
    """Production service for trailer intelligence and audience sentiment."""

    def __init__(self):
        self.sentiment_engine = CinemaSentimentEngine()
        self.harvester = TrailerBuzzHarvester()
        logger.info("Initialized SentimentService with CinemaSentimentEngine and TrailerBuzzHarvester.")

    async def analyze_comments(self, comments: List[str]) -> Dict[str, Any]:
        """Analyzes a batch of audience comments and returns aggregated sentiment metrics."""
        return self.sentiment_engine.aggregate_movie_comments(comments)

    async def get_trailer_buzz(
        self,
        movie_title: str,
        release_year: Optional[int] = None,
        release_date: Optional[str] = None,
        video_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves real-time trailer metrics, audience sentiment, and composite buzz index.
        Falls back to neutral prior if trailer is unavailable.
        """
        try:
            return self.harvester.process_movie_trailer_buzz(
                movie_title=movie_title,
                release_year=release_year,
                release_date=release_date,
                video_id=video_id,
            )
        except Exception as e:
            logger.error(f"Error fetching trailer buzz for '{movie_title}': {e}")
            return {
                "movie_title": movie_title,
                "release_year": release_year,
                "has_trailer_data": False,
                "composite_buzz_score": 50.0,
                "error": str(e),
            }


# Singleton instance for backend FastAPI dependency injection
sentiment_service = SentimentService()

