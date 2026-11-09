"""
CineMetrics — Upcoming Releases & Dashboard Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class UpcomingMovieItem(BaseModel):
    id: str
    canonical_id: str
    primary_title: str
    release_date: str
    release_year: int
    industry: str
    genres: List[str]
    director: str
    lead_actor: str
    budget_usd: float
    budget_inr_crores: float
    readiness_score: int
    lifecycle_stage: str
    status_badge: str
    expected_gross_usd: float
    expected_gross_formatted_usd: str
    expected_gross_formatted_inr: str
    pessimistic_bound_80_usd: float
    optimistic_bound_80_usd: float
    risk_assessment_tier: str
    risk_badge: str
    buzz_score: float = 0.0
    trailer_view_count: int = 0
    youtube_trailer_id: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None


class DashboardSection(BaseModel):
    key: str
    title: str
    description: str
    item_count: int
    items: List[UpcomingMovieItem]


class UpcomingDashboardResponse(BaseModel):
    total_upcoming_tracked: int
    last_updated: str
    sections: Dict[str, DashboardSection]

