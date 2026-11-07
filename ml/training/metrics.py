"""
CineMetrics — Machine Learning Evaluation Metrics Suite
Computes standardized econometric and percentage error metrics in log and original dollar space.
"""

from typing import Dict
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def calculate_smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Computes Symmetric Mean Absolute Percentage Error (SMAPE) in percentage:
    SMAPE = (100% / n) * sum( 2 * |y - y_hat| / (|y| + |y_hat|) )
    Bound between 0% and 200%. Handles zeros gracefully.
    """
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    diff = np.abs(y_true - y_pred)
    # Mask zero denominators where both true and pred are 0
    valid_mask = denominator > 0
    if not np.any(valid_mask):
        return 0.0
    return float(np.mean(diff[valid_mask] / denominator[valid_mask]) * 100.0)


def evaluate_predictions(y_true_log: np.ndarray, y_pred_log: np.ndarray, y_true_real: np.ndarray) -> Dict[str, float]:
    """
    Evaluates model predictions across both mathematical spaces:
    1. Log10 Space: RMSE, MAE, R2
    2. Real Dollar Space: SMAPE (%), MedAE (USD), MeanAE (USD)
    """
    y_pred_real = np.power(10.0, y_pred_log)

    rmse = float(np.sqrt(mean_squared_error(y_true_log, y_pred_log)))
    mae = float(mean_absolute_error(y_true_log, y_pred_log))
    r2 = float(r2_score(y_true_log, y_pred_log))

    smape = calculate_smape(y_true_real, y_pred_real)
    medae_real = float(np.median(np.abs(y_true_real - y_pred_real)))
    meanae_real = float(np.mean(np.abs(y_true_real - y_pred_real)))

    return {
        "rmse_log": round(rmse, 4),
        "mae_log": round(mae, 4),
        "r2_log": round(r2, 4),
        "smape_pct": round(smape, 2),
        "medae_usd": round(medae_real, 2),
        "meanae_usd": round(meanae_real, 2),
    }

