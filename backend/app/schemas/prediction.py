"""
CineMetrics — ML Prediction & Financial Risk Schemas
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ConformalForecast(BaseModel):
    expected_gross_usd: float
    expected_gross_inr_crores: float
    expected_usd_formatted: str
    expected_inr_formatted: str
    pessimistic_bound_80_usd: float
    pessimistic_bound_80_inr: float
    pessimistic_formatted_usd: str
    pessimistic_formatted_inr: str
    optimistic_bound_80_usd: float
    optimistic_bound_80_inr: float
    optimistic_formatted_usd: str
    optimistic_formatted_inr: str
    extreme_downside_95_usd: Optional[float] = None
    extreme_upside_95_usd: Optional[float] = None
    conformal_confidence: float = 0.80


class SuccessClassification(BaseModel):
    predicted_category: str
    probabilities: Dict[str, float]


class FinancialRiskAudit(BaseModel):
    estimated_budget_usd: float
    estimated_budget_inr_crores: float
    recovery_ratio_expected: float
    break_even_status: str
    risk_assessment_tier: str
    risk_badge: str
    prob_break_even: float
    prob_commercial_profit: float
    prob_catastrophic_disaster: float


class ActivePredictionResponse(BaseModel):
    movie_id: str
    canonical_id: str
    title: str
    prediction_stage: str
    readiness_score: int
    status_badge: str
    model_version: str
    last_updated: str
    currency_display: str = "USD/INR"
    forecast: ConformalForecast
    success_classification: SuccessClassification
    financial_risk: FinancialRiskAudit
    top_positive_driver: Optional[str] = None
    top_negative_driver: Optional[str] = None
    narrative_summary: Optional[str] = None
    days_to_release: Optional[int] = None
    is_stage4_active: bool = False
    stage4_details: Optional[Dict[str, Any]] = None


class PredictionHistoryItem(BaseModel):
    id: str
    prediction_stage: str
    readiness_score: int
    expected_gross_usd: float
    delta_usd: float
    delta_pct: float
    change_attribution: str
    evaluated_at: str

