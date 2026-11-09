"""
CineMetrics — Movie Pydantic Schemas
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class MovieSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_id: str
    primary_title: str
    original_title: Optional[str] = None
    release_date: Optional[str] = None
    release_year: Optional[int] = None
    industry: Optional[str] = None
    genres: List[str] = []
    director: Optional[str] = None
    lead_actor: Optional[str] = None
    budget_usd: float = 0.0
    budget_inr_crores: float = 0.0
    box_office_gross_usd: Optional[float] = None
    box_office_gross_inr_crores: Optional[float] = None
    is_released: bool = False
    youtube_trailer_id: Optional[str] = None


class MovieDetail(MovieSummary):
    model_config = ConfigDict(from_attributes=True)

    runtime_minutes: Optional[int] = None
    original_language: Optional[str] = None
    cast_members: List[str] = []
    overview: Optional[str] = None
    production_company: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    active_prediction: Optional[Any] = None
    buzz_metrics: Optional[Any] = None


class SimilarMovie(BaseModel):
    id: str
    canonical_id: str
    primary_title: str
    release_year: int
    industry: str
    genres: List[str]
    director: str
    lead_actor: str
    budget_usd: float
    gross_usd: float
    gross_formatted_usd: str
    gross_formatted_inr: str
    similarity_score: float


class MovieSearchResponse(BaseModel):
    query: str
    total_results: int
    latency_ms: float
    movies: List[MovieSummary]
