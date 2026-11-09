"""
CineMetrics — Counterfactual What-If Simulation Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WhatIfSimulationRequest(BaseModel):
    base_movie_id: str
    budget_usd_override: Optional[float] = None
    director_override: Optional[str] = None
    lead_actor_override: Optional[str] = None
    release_month_override: Optional[int] = Field(None, ge=1, le=12)
    is_franchise_override: Optional[bool] = None
    simulated_trailer_views: Optional[int] = None
    simulated_sentiment_polarity: Optional[float] = Field(None, ge=-1.0, le=1.0)


class ScenarioMetrics(BaseModel):
    expected_gross_usd: float
    expected_gross_formatted_usd: str
    expected_gross_formatted_inr: str
    pessimistic_bound_80_usd: float
    optimistic_bound_80_usd: float
    prob_break_even: float
    prob_commercial_profit: float
    risk_assessment_tier: str
    risk_badge: str


class CounterfactualDelta(BaseModel):
    delta_revenue_usd: float
    delta_revenue_inr_crores: float
    percentage_change: float
    roi_impact: str
    risk_shift: str
    strategic_verdict: str


class WhatIfSimulationResponse(BaseModel):
    simulation_id: str
    base_movie_id: str
    base_movie_title: str
    execution_latency_ms: float
    applied_perturbations: Dict[str, Any]
    baseline_scenario: ScenarioMetrics
    simulated_scenario: ScenarioMetrics
    delta_analysis: CounterfactualDelta

