"""
CineMetrics — Financial Downside Risk & Uncertainty Engine
Integrates Split Conformal Prediction intervals with executive capital risk metrics:
- Break-Even Probability: P(Gross >= Budget)
- Commercial Profitability Probability: P(Gross >= 2.5 * Budget)
- Catastrophic Disaster Risk: P(Gross < 0.5 * Budget)
- Expected Theatrical Net Profit / Loss (Exhibitor-Adjusted)
- Dual-Currency Formatting: USD Millions & INR Crores
"""

import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import joblib
from scipy.stats import norm

from ml.dataset_engineering.config import ML_MODELS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FinancialRiskEngine")

# Standard Foreign Exchange Conversion for Dual-Currency Reporting
DEFAULT_INR_USD_RATE = 84.0  # ₹84.0 INR per 1 USD
CRORE_UNITS = 10_000_000.0   # 1 Crore = 10 Million INR


class FinancialRiskCalculator:
    """
    Evaluates financial risk metrics and conformal prediction intervals for film investments.
    """

    def __init__(self, calibrator_path: Optional[Path] = None):
        self.calibrator_path = calibrator_path or (
            ML_MODELS_DIR / "production" / "conformal_calibrator_v1.joblib"
        )
        self.calibrator = None
        self.sigma_effective = 0.65  # Default empirical residual standard deviation in log10 space

        if self.calibrator_path.exists():
            try:
                self.calibrator = joblib.load(str(self.calibrator_path))
                logger.info(f"Loaded Conformal Calibrator from {self.calibrator_path}")
                # Compute effective residual scale from calibrated 80% quantile: q80 / 1.28155
                q80 = self.calibrator.quantiles.get(80, 0.837)
                self.sigma_effective = max(q80 / 1.28155, 0.20)
                logger.info(f"Derived effective log10 residual scale: sigma = {self.sigma_effective:.4f}")
            except Exception as e:
                logger.warning(f"Could not load conformal calibrator ({e}); using empirical default.")
        else:
            logger.warning(f"Conformal calibrator not found at {self.calibrator_path}; using empirical default.")

    def format_dual_currency(self, usd_amount: float) -> Dict[str, str]:
        """Formats a USD dollar figure into both USD Millions and INR Crores."""
        usd_millions = usd_amount / 1_000_000.0
        inr_crores = (usd_amount * DEFAULT_INR_USD_RATE) / CRORE_UNITS
        return {
            "usd_formatted": f"${usd_millions:.2f}M" if abs(usd_millions) >= 1.0 else f"${usd_amount:,.0f}",
            "inr_formatted": f"₹{inr_crores:.2f} Cr" if abs(inr_crores) >= 1.0 else f"₹{inr_crores * 10:,.0f} Lakh",
            "usd_raw": round(usd_amount, 2),
            "inr_raw": round(usd_amount * DEFAULT_INR_USD_RATE, 2),
        }

    def compute_conformal_intervals(
        self,
        predicted_log10: float,
    ) -> Dict[str, Any]:
        """Generates distribution-free 80% and 95% conformal prediction intervals."""
        if self.calibrator and hasattr(self.calibrator, "predict_intervals"):
            res = self.calibrator.predict_intervals(np.array([predicted_log10]))
            return {
                "expected_usd": float(res["expected_usd"][0]),
                "pessimistic_usd_80": float(res["pessimistic_usd_80"][0]),
                "optimistic_usd_80": float(res["optimistic_usd_80"][0]),
                "lower_usd_95": float(res["lower_usd_95"][0]),
                "upper_usd_95": float(res["upper_usd_95"][0]),
                "log_margin_80": float(res["log_margin_80"]),
                "log_margin_95": float(res["log_margin_95"]),
            }
        else:
            # Analytical fallback using empirical quantiles
            q80 = 0.837
            q95 = 1.415
            pred_usd = 10.0 ** predicted_log10
            return {
                "expected_usd": pred_usd,
                "pessimistic_usd_80": 10.0 ** (predicted_log10 - q80),
                "optimistic_usd_80": 10.0 ** (predicted_log10 + q80),
                "lower_usd_95": 10.0 ** (predicted_log10 - q95),
                "upper_usd_95": 10.0 ** (predicted_log10 + q95),
                "log_margin_80": q80,
                "log_margin_95": q95,
            }

    def evaluate_financial_risk(
        self,
        predicted_log10: float,
        budget_usd: Optional[float] = None,
        movie_title: str = "Upcoming Title",
    ) -> Dict[str, Any]:
        """
        Calculates comprehensive executive downside risk metrics.
        """
        # 1. Conformal Intervals
        intervals = self.compute_conformal_intervals(predicted_log10)
        expected_gross = intervals["expected_usd"]
        pessimistic_gross = intervals["pessimistic_usd_80"]
        optimistic_gross = intervals["optimistic_usd_80"]

        # Default budget heuristic if missing: 30% of expected gross or $20M
        clean_budget = budget_usd if (budget_usd and budget_usd > 10_000) else max(expected_gross * 0.35, 15_000_000.0)
        budget_log10 = math.log10(max(clean_budget, 1.0))

        # 2. Financial Downside Probabilities
        # Z-scores in log10 space against effective residual scale
        # P(Gross >= Budget)
        z_be = (predicted_log10 - budget_log10) / self.sigma_effective
        prob_break_even = float(norm.cdf(z_be))

        # P(Gross >= 2.5 * Budget) -> Commercial Profitability Threshold
        profit_target_log10 = budget_log10 + math.log10(2.5)
        z_profit = (predicted_log10 - profit_target_log10) / self.sigma_effective
        prob_commercial_profit = float(norm.cdf(z_profit))

        # P(Gross < 0.5 * Budget) -> Catastrophic Write-Down
        disaster_target_log10 = budget_log10 + math.log10(0.5)
        z_disaster = (disaster_target_log10 - predicted_log10) / self.sigma_effective
        prob_disaster = float(norm.cdf(z_disaster))

        # 3. P&L Accounting
        # Studio share is ~50% of theatrical gross (standard exhibitor split)
        studio_theatrical_share = expected_gross * 0.50
        theatrical_net_profit = studio_theatrical_share - clean_budget
        break_even_gap = max(0.0, clean_budget - expected_gross)
        roi_multiplier = expected_gross / max(clean_budget, 1.0)

        # 4. Qualitative Risk Categorization
        if prob_break_even >= 0.75 and prob_disaster < 0.10:
            risk_tier = "Low Capital Risk"
            risk_badge = "🟢 SECURE"
        elif prob_break_even >= 0.50:
            risk_tier = "Moderate Commercial Risk"
            risk_badge = "🟡 MODERATE"
        elif prob_break_even >= 0.35:
            risk_tier = "Elevated Capital Risk"
            risk_badge = "🟠 ELEVATED"
        else:
            risk_tier = "Critical Downside Risk"
            risk_badge = "🔴 HIGH RISK"

        return {
            "movie_title": movie_title,
            "budget_usd": clean_budget,
            "budget_formatted": self.format_dual_currency(clean_budget),
            # Three-Scenario Conformal Forecast
            "forecast_scenarios": {
                "pessimistic_scenario": self.format_dual_currency(pessimistic_gross),
                "expected_scenario": self.format_dual_currency(expected_gross),
                "optimistic_scenario": self.format_dual_currency(optimistic_gross),
                "extreme_downside_95": self.format_dual_currency(intervals["lower_usd_95"]),
                "extreme_upside_95": self.format_dual_currency(intervals["upper_usd_95"]),
            },
            # Financial Probabilities
            "risk_probabilities": {
                "break_even_probability": round(min(max(prob_break_even, 0.0), 1.0), 4),
                "commercial_profitability_probability": round(min(max(prob_commercial_profit, 0.0), 1.0), 4),
                "catastrophic_disaster_probability": round(min(max(prob_disaster, 0.0), 1.0), 4),
            },
            # P&L Metrics
            "financial_performance": {
                "roi_multiplier": round(roi_multiplier, 2),
                "studio_theatrical_share_usd": round(studio_theatrical_share, 2),
                "expected_theatrical_net_usd": round(theatrical_net_profit, 2),
                "expected_theatrical_net_formatted": self.format_dual_currency(theatrical_net_profit),
                "break_even_gap_usd": round(break_even_gap, 2),
                "break_even_gap_formatted": self.format_dual_currency(break_even_gap),
            },
            "risk_assessment_tier": risk_tier,
            "risk_badge": risk_badge,
        }

