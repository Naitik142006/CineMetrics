"""
CineMetrics — EDA: Financial Target Distributions & Transformation Analysis
Evaluates box-office revenue skewness, kurtosis, and mathematical target transformations.
"""

from typing import Dict
import numpy as np
import pandas as pd
from scipy import stats

from ml.dataset_engineering.config import UNIFIED_MOVIES_PATH


def analyze_target_distributions(df: pd.DataFrame) -> Dict:
    """
    Analyzes the statistical properties of revenue and budget distributions,
    demonstrating the necessity of log-space target transformations.
    """
    # Filter to films with verified financial numbers
    df_fin = df.dropna(subset=["budget_real_2024_usd", "revenue_real_2024_usd"]).copy()
    df_fin = df_fin[(df_fin["budget_real_2024_usd"] > 10_000) & (df_fin["revenue_real_2024_usd"] > 10_000)]

    raw_rev = df_fin["revenue_real_2024_usd"].values
    raw_bud = df_fin["budget_real_2024_usd"].values

    log10_rev = np.log10(raw_rev)
    log1p_rev = np.log1p(raw_rev)

    # Parametric & Non-Parametric Metrics
    stats_summary = {
        "sample_size": len(df_fin),
        "raw_revenue": {
            "mean": float(np.mean(raw_rev)),
            "std": float(np.std(raw_rev)),
            "median": float(np.median(raw_rev)),
            "iqr": float(np.percentile(raw_rev, 75) - np.percentile(raw_rev, 25)),
            "p10": float(np.percentile(raw_rev, 10)),
            "p25": float(np.percentile(raw_rev, 25)),
            "p75": float(np.percentile(raw_rev, 75)),
            "p90": float(np.percentile(raw_rev, 90)),
            "p99": float(np.percentile(raw_rev, 99)),
            "skewness": float(stats.skew(raw_rev)),
            "kurtosis": float(stats.kurtosis(raw_rev)),
        },
        "log10_revenue": {
            "mean": float(np.mean(log10_rev)),
            "std": float(np.std(log10_rev)),
            "median": float(np.median(log10_rev)),
            "skewness": float(stats.skew(log10_rev)),
            "kurtosis": float(stats.kurtosis(log10_rev)),
        },
        "log1p_revenue": {
            "mean": float(np.mean(log1p_rev)),
            "std": float(np.std(log1p_rev)),
            "median": float(np.median(log1p_rev)),
            "skewness": float(stats.skew(log1p_rev)),
            "kurtosis": float(stats.kurtosis(log1p_rev)),
        },
        "correlations": {
            "pearson_raw": float(stats.pearsonr(raw_bud, raw_rev)[0]),
            "spearman_rank": float(stats.spearmanr(raw_bud, raw_rev)[0]),
            "pearson_log": float(stats.pearsonr(np.log10(raw_bud), log10_rev)[0]),
        },
    }

    return stats_summary


if __name__ == "__main__":
    df = pd.read_parquet(UNIFIED_MOVIES_PATH)
    res = analyze_target_distributions(df)
    print("Sample Size:", res["sample_size"])
    print("Raw Skewness:", res["raw_revenue"]["skewness"])
    print("Log10 Skewness:", res["log10_revenue"]["skewness"])
    print("Spearman Rank Corr (Budget vs Rev):", res["correlations"]["spearman_rank"])

