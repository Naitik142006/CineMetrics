"""
CineMetrics — Production Backend ML Explainability & Serving Service
Provides unified high-performance API serving for:
1. CatBoost Revenue Predictions
2. Conformal Prediction Intervals (Pessimistic, Expected, Optimistic)
3. TreeSHAP Local Feature Attributions & Dollar Impacts
4. Financial Risk Probabilities
5. Dual-Currency Formatted Output (USD Millions & INR Crores)
"""

import time
import logging
from typing import Dict, Any, Optional

import pandas as pd

from ml.explainability.explainer import CineMetricsExplainer
from ml.explainability.risk_engine import FinancialRiskCalculator

logger = logging.getLogger("ExplainerService")


class ExplainerService:
    """
    Singleton service initialized at FastAPI application startup.
    Keeps CatBoost model and TreeSHAP explainer in-memory for sub-100ms inference.
    """

    def __init__(self):
        logger.info("Initializing ExplainerService...")
        self.explainer = CineMetricsExplainer()
        self.risk_calculator = FinancialRiskCalculator()
        logger.info("ExplainerService successfully initialized and ready for queries.")

    async def generate_full_prediction_dossier(
        self,
        features: Dict[str, Any],
        movie_title: str = "Upcoming Title",
        budget_usd: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end forward inference, TreeSHAP attribution,
        conformal interval generation, and financial risk calculation.
        """
        t0 = time.perf_counter()
        df_row = pd.DataFrame([features])

        # 1. TreeSHAP Explanation & Forward Pass
        explanation = self.explainer.explain_instance(df_row, movie_title=movie_title)
        pred_log10 = explanation["predicted_value_log10"]

        # Budget extraction: use argument if given, else check features
        effective_budget = budget_usd or features.get("budget_clean_usd") or features.get("budget_usd")

        # 2. Conformal Uncertainty & Financial Risk
        risk_profile = self.risk_calculator.evaluate_financial_risk(
            predicted_log10=pred_log10,
            budget_usd=effective_budget,
            movie_title=movie_title,
        )

        total_latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return {
            "movie_title": movie_title,
            "prediction_status": "success",
            "total_inference_latency_ms": total_latency_ms,
            "revenue_forecast": {
                "predicted_log10": pred_log10,
                "expected_gross": risk_profile["forecast_scenarios"]["expected_scenario"],
                "pessimistic_bound_80": risk_profile["forecast_scenarios"]["pessimistic_scenario"],
                "optimistic_bound_80": risk_profile["forecast_scenarios"]["optimistic_scenario"],
                "extreme_downside_95": risk_profile["forecast_scenarios"]["extreme_downside_95"],
                "extreme_upside_95": risk_profile["forecast_scenarios"]["extreme_upside_95"],
            },
            "financial_risk_audit": risk_profile,
            "shap_explanation": {
                "base_value_log10": explanation["base_value_log10"],
                "base_revenue_usd": explanation["base_revenue_usd"],
                "additivity_axiom_verified": explanation["additivity_axiom_verified"],
                "additivity_error": explanation["additivity_error"],
                "top_positive_drivers": explanation["top_positive_drivers"],
                "top_negative_drivers": explanation["top_negative_drivers"],
                "waterfall_breakdown": explanation["waterfall_breakdown"],
                "narrative_summary": explanation["narrative_summary"],
            },
        }


# Global singleton instance for FastAPI dependency injection
explainer_service = ExplainerService()

