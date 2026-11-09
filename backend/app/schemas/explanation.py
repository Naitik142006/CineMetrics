"""
CineMetrics — TreeSHAP Explainability Schemas
"""

from typing import List, Optional
from pydantic import BaseModel


class SHAPFactor(BaseModel):
    feature_name: str
    feature_label: str
    shap_value_log10: float
    shap_impact_usd: float
    shap_impact_inr_crores: float
    direction: str  # "positive" or "negative"


class SHAPWaterfallResponse(BaseModel):
    movie_id: str
    movie_title: str
    base_value_log10: float
    base_value_usd: float
    base_value_inr_crores: float
    final_predicted_log10: float
    final_predicted_revenue_usd: float
    final_predicted_revenue_inr_crores: float
    additivity_axiom_verified: bool
    additivity_error: float
    top_positive_factors: List[SHAPFactor]
    top_negative_factors: List[SHAPFactor]
    waterfall_breakdown: List[SHAPFactor]
    narrative_summary: str
