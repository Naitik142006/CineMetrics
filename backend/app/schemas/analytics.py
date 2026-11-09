"""
CineMetrics — Cinema Analytics & Talent Dossier Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class FilmCredit(BaseModel):
    title: str
    year: int
    gross_usd: float
    gross_formatted_usd: str
    roi_multiplier: float
    success_category: str


class TalentDossierResponse(BaseModel):
    person_name: str
    role: str  # "Actor" or "Director"
    total_films_tracked: int
    career_cumulative_gross_usd: float
    career_cumulative_gross_formatted_usd: str
    career_average_gross_formatted_usd: str
    career_average_gross_formatted_inr: str
    career_median_roi: float
    commercial_hit_rate: float
    star_power_tier: str
    filmography_highlights: List[FilmCredit]


class MarketSegmentMetric(BaseModel):
    segment_name: str
    film_count: int
    total_box_office_usd: float
    total_box_office_formatted: str
    average_budget_formatted: str
    hit_rate_pct: float
    market_share_pct: float


class MarketTrendResponse(BaseModel):
    reporting_period: str
    total_films_analyzed: int
    segments: List[MarketSegmentMetric]


class ModelPerformanceResponse(BaseModel):
    production_model: str
    model_version: str
    evaluation_dataset: str
    test_r2_score: float
    test_rmse_log10: float
    test_mae_log10: float
    quadratic_weighted_kappa: float
    classification_macro_f1: float
    conformal_coverage_80_target: float
    conformal_coverage_80_empirical: float
    conformal_coverage_95_target: float
    conformal_coverage_95_empirical: float
    inference_p95_latency_ms: float
    shap_additivity_pass_rate: float

