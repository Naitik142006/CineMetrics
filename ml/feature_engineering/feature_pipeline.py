"""
CineMetrics — Production Feature Pipeline Engine
Constructs the full feature matrix for CatBoost, LightGBM, and baseline models.
"""

import logging
import re
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd

from ml.dataset_engineering.config import UNIFIED_MOVIES_PATH
from ml.feature_engineering.temporal_isolation import calculate_prior_talent_track_records

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FeaturePipeline")

# Major Genres for Primary Extraction
RECOGNIZED_GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime",
    "Documentary", "Drama", "Family", "Fantasy", "History",
    "Horror", "Music", "Mystery", "Romance", "Science Fiction",
    "Thriller", "War", "Western",
]


def extract_primary_genre(genres_str: str) -> str:
    """Extracts first valid genre from comma-separated genre string."""
    if not genres_str or pd.isna(genres_str):
        return "Drama"  # Mode baseline
    parts = [g.strip() for g in str(genres_str).split(",")]
    for p in parts:
        if p in RECOGNIZED_GENRES:
            return p
    return parts[0] if parts else "Drama"


def detect_sequel_or_franchise(title: str) -> int:
    """
    Detects if a film is a sequel, franchise installment, or reboot using regex heuristics.
    """
    if not title or pd.isna(title):
        return 0
    pattern = r"\b(part\s+\d+|chapter\s+\d+|vol(ume)?\s+\d+|\d+|ii|iii|iv|v|vi|vii|returns|reloaded|revolution|awakens|forever|legacy|homecoming|infinity|endgame)\b"
    return 1 if bool(re.search(pattern, str(title), re.IGNORECASE)) else 0


def assign_budget_tier(budget_real_usd: float) -> str:
    """Categorizes budget into economic production tiers."""
    if pd.isna(budget_real_usd) or budget_real_usd <= 0:
        return "Mid"
    if budget_real_usd < 5_000_000:
        return "Micro"
    elif budget_real_usd < 25_000_000:
        return "Low"
    elif budget_real_usd < 75_000_000:
        return "Mid"
    elif budget_real_usd < 150_000_000:
        return "High"
    else:
        return "Tentpole"


def build_feature_matrix(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Transforms the Silver Lakehouse into the Gold Feature Store.
    """
    if df is None:
        logger.info(f"Loading Silver Lakehouse from {UNIFIED_MOVIES_PATH}...")
        df = pd.read_parquet(UNIFIED_MOVIES_PATH)

    logger.info(f"Building feature matrix for {len(df):,} movies...")

    # 1. Apply Point-in-Time Temporal Talent Metrics
    df = calculate_prior_talent_track_records(df)

    # 2. Financial & Budget Features
    # For films with missing budget, impute using industry-specific median
    industry_median_budgets = df.groupby("industry")["budget_real_2024_usd"].median().to_dict()
    default_median = float(df["budget_real_2024_usd"].median() or 25_000_000)

    def impute_budget(row):
        b = row.get("budget_real_2024_usd")
        if pd.notna(b) and b > 10_000:
            return float(b)
        ind = row.get("industry")
        return float(industry_median_budgets.get(ind, default_median))

    df["budget_clean_usd"] = df.apply(impute_budget, axis=1)
    df["log_budget"] = np.log10(np.maximum(df["budget_clean_usd"], 10_000.0))
    df["budget_tier"] = df["budget_clean_usd"].apply(assign_budget_tier)

    # 3. Calendar & Seasonality Features
    df["release_month"] = df["temporal_timestamp"].dt.month.astype(int)
    df["release_quarter"] = df["temporal_timestamp"].dt.quarter.astype(int)
    df["release_dayofweek"] = df["temporal_timestamp"].dt.dayofweek.astype(int)  # 4 = Friday
    df["release_year_num"] = df["temporal_timestamp"].dt.year.astype(int)

    # Seasonal indicators
    df["is_summer_season"] = df["release_month"].isin([5, 6, 7]).astype(int)
    df["is_holiday_season"] = df["release_month"].isin([10, 11, 12]).astype(int)
    df["is_weekend_release"] = df["release_dayofweek"].isin([4, 5]).astype(int)  # Fri / Sat

    # 4. Content & Metadata Features
    df["primary_genre"] = df["genres"].apply(extract_primary_genre)
    df["genre_count"] = df["genres"].fillna("").apply(lambda s: len(s.split(",")) if s else 1)
    df["is_sequel_or_franchise"] = df["primary_title"].apply(detect_sequel_or_franchise)
    df["runtime_minutes_clean"] = df["runtime_minutes"].fillna(105.0)

    # Simplify language cardinality (preserve top 8, map rest to 'other')
    top_languages = ["en", "hi", "te", "ta", "ml", "kn", "fr", "es"]
    df["language_clean"] = df["original_language"].apply(lambda l: l if l in top_languages else "other")

    # 5. Target Variables
    df["target_revenue_raw"] = df["revenue_real_2024_usd"]
    df["target_revenue_log10"] = np.where(
        df["revenue_real_2024_usd"].notna() & (df["revenue_real_2024_usd"] > 10_000),
        np.log10(df["revenue_real_2024_usd"]),
        np.nan,
    )
    df["target_success_class"] = df["success_category"]
    df["target_roi"] = df["roi_multiplier"]

    logger.info("Production feature matrix successfully constructed.")
    return df


if __name__ == "__main__":
    matrix = build_feature_matrix()
    print("Feature Matrix Shape:", matrix.shape)
    cols = [
        "primary_title", "release_year_num", "log_budget", "budget_tier",
        "primary_genre", "is_holiday_season", "director_prior_movies",
        "lead_actor_prior_movies", "target_revenue_log10", "target_success_class"
    ]
    print("\nSample Feature Rows:")
    print(matrix[cols].dropna(subset=["target_revenue_log10"]).head(5).to_string(index=False))
