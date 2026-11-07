"""
CineMetrics — Conformal Prediction & Distribution-Free Uncertainty Quantification
Implements Split Conformal Prediction (Vovk et al.) for revenue prediction intervals.
"""

from typing import Dict, List, Tuple
import numpy as np


class ConformalCalibrator:
    """
    Split Conformal Calibrator for regression models.
    Guarantees finite-sample marginal coverage: P(Y in C(X)) >= 1 - alpha.
    """

    def __init__(self, alpha_levels: List[float] = [0.20, 0.05]):
        """
        alpha_levels: error rates (0.20 -> 80% coverage interval, 0.05 -> 95% coverage interval)
        """
        self.alpha_levels = sorted(alpha_levels, reverse=True)
        self.quantiles: Dict[float, float] = {}
        self.is_calibrated = False

    def calibrate(self, y_true_log: np.ndarray, y_pred_log: np.ndarray) -> "ConformalCalibrator":
        """
        Computes non-conformity scores (absolute log residuals) and empirical quantiles.
        """
        residuals = np.abs(y_true_log - y_pred_log)
        n = len(residuals)

        for alpha in self.alpha_levels:
            # Finite-sample correction: ceil((n + 1) * (1 - alpha)) / n
            k = int(np.ceil((n + 1) * (1.0 - alpha)))
            k = min(max(k, 1), n)
            q = float(np.partition(residuals, k - 1)[k - 1])
            coverage_pct = int(round((1.0 - alpha) * 100))
            self.quantiles[coverage_pct] = q

        self.is_calibrated = True
        return self

    def predict_intervals(self, y_pred_log: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Generates lower bounds, point forecasts, and upper bounds in log and dollar space.
        """
        if not self.is_calibrated:
            raise ValueError("Calibrator has not been calibrated on validation data yet!")

        q80 = self.quantiles.get(80, 0.40)
        q95 = self.quantiles.get(95, 0.60)

        # 80% bounds (Pessimistic / Optimistic scenarios)
        log_lower_80 = y_pred_log - q80
        log_upper_80 = y_pred_log + q80

        # 95% bounds
        log_lower_95 = y_pred_log - q95
        log_upper_95 = y_pred_log + q95

        # Real Dollar transformations (10^log)
        expected_usd = np.power(10.0, y_pred_log)
        pessimistic_usd = np.power(10.0, log_lower_80)
        optimistic_usd = np.power(10.0, log_upper_80)

        usd_lower_95 = np.power(10.0, log_lower_95)
        usd_upper_95 = np.power(10.0, log_upper_95)

        return {
            "expected_log": y_pred_log,
            "expected_usd": expected_usd,
            "pessimistic_usd_80": pessimistic_usd,
            "optimistic_usd_80": optimistic_usd,
            "lower_usd_95": usd_lower_95,
            "upper_usd_95": usd_upper_95,
            "log_margin_80": q80,
            "log_margin_95": q95,
        }

    def evaluate_coverage(self, y_true_log: np.ndarray, y_pred_log: np.ndarray) -> Dict[str, float]:
        """
        Evaluates empirical coverage (PICP) on an unseen test set.
        """
        residuals = np.abs(y_true_log - y_pred_log)
        coverage_metrics = {}

        for coverage_pct, q in self.quantiles.items():
            covered = np.mean(residuals <= q) * 100.0
            coverage_metrics[f"target_{coverage_pct}pct_coverage"] = float(coverage_pct)
            coverage_metrics[f"empirical_{coverage_pct}pct_coverage"] = round(float(covered), 2)

        return coverage_metrics

