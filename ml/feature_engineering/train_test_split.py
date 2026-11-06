"""
CineMetrics — Chronological Out-of-Time Train / Validation / Test Splitting Engine
Generates the final Gold Feature Store snapshots in data/snapshots/ for model training.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

from ml.dataset_engineering.config import BASE_DIR, SNAPSHOTS_DATA_DIR
from ml.feature_engineering.feature_pipeline import build_feature_matrix

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TrainTestSplit")

# Canonical Features for Downstream Machine Learning Models
NUMERICAL_FEATURES: List[str] = [
    "log_budget",
    "budget_clean_usd",
    "runtime_minutes_clean",
    "genre_count",
    "is_sequel_or_franchise",
    "is_summer_season",
    "is_holiday_season",
    "is_weekend_release",
    "release_month",
    "release_quarter",
    "director_prior_movies",
    "director_prior_avg_real_gross",
    "director_prior_avg_roi",
    "director_prior_hit_rate",
    "lead_actor_prior_movies",
    "lead_actor_prior_avg_real_gross",
    "lead_actor_prior_avg_roi",
    "lead_actor_prior_hit_rate",
    "studio_prior_movies",
]

CATEGORICAL_FEATURES: List[str] = [
    "budget_tier",
    "primary_genre",
    "industry",
    "language_clean",
    "director",
    "lead_actor",
]

FEATURE_COLUMNS: List[str] = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

TARGET_COLUMNS: List[str] = [
    "target_revenue_log10",
    "target_revenue_raw",
    "target_success_class",
    "target_roi",
]

METADATA_COLUMNS: List[str] = [
    "canonical_id",
    "primary_title",
    "release_year",
    "release_date",
    "temporal_timestamp",
    "imdb_tconst",
    "tmdb_id",
    "data_quality_tier",
    "source_provenance",
]

ALL_SNAPSHOT_COLUMNS: List[str] = METADATA_COLUMNS + FEATURE_COLUMNS + TARGET_COLUMNS


def execute_chronological_split(df_matrix: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits feature matrix chronologically using out-of-time temporal holdout:
    - Train: Year <= 2013 (Historical base: 84.4%, 6,849 movies)
    - Val:   2014 <= Year <= 2016 (Validation & early stopping: 8.0%, 652 movies)
    - Test:  Year >= 2017 (True out-of-time test set: 7.5%, 611 movies)
    - Unreleased: Missing target or Year >= 2025 (Inference Radar Pool)
    """
    logger.info("Executing chronological temporal train/val/test splitting...")

    # Filter columns to only registered snapshot schema
    cols_to_keep = [c for c in ALL_SNAPSHOT_COLUMNS if c in df_matrix.columns]
    df = df_matrix[cols_to_keep].copy()

    # Partition unreleased / missing financial targets
    unreleased_mask = df["target_revenue_log10"].isna() | (df["release_year"].fillna(2020) >= 2025)
    df_unreleased = df[unreleased_mask].copy()
    df_labeled = df[~unreleased_mask].copy()

    # Clean release year for temporal boundary checks
    df_labeled["split_year"] = df_labeled["release_year"].fillna(2010).astype(int)

    train_df = df_labeled[df_labeled["split_year"] <= 2013].drop(columns=["split_year"]).reset_index(drop=True)
    val_df = df_labeled[(df_labeled["split_year"] >= 2014) & (df_labeled["split_year"] <= 2016)].drop(columns=["split_year"]).reset_index(drop=True)
    test_df = df_labeled[df_labeled["split_year"] >= 2017].drop(columns=["split_year"]).reset_index(drop=True)

    logger.info(f"Chronological Splits Created:")
    logger.info(f"  Train Split (<= 2013):        {len(train_df):,} movies ({len(train_df) / len(df_labeled):.1%})")
    logger.info(f"  Validation Split (2014-2016):  {len(val_df):,} movies ({len(val_df) / len(df_labeled):.1%})")
    logger.info(f"  Test Split (>= 2017):         {len(test_df):,} movies ({len(test_df) / len(df_labeled):.1%})")
    logger.info(f"  Unreleased / Radar Pool:       {len(df_unreleased):,} movies")

    return train_df, val_df, test_df, df_unreleased


def save_gold_feature_snapshots() -> Dict[str, Path]:
    """Generates and writes all Gold Feature Store snapshots into data/snapshots/."""
    logger.info("Starting Gold Feature Store snapshot generation...")
    df_matrix = build_feature_matrix()

    train_df, val_df, test_df, unreleased_df = execute_chronological_split(df_matrix)

    paths = {
        "train": SNAPSHOTS_DATA_DIR / "train_v1.parquet",
        "val": SNAPSHOTS_DATA_DIR / "val_v1.parquet",
        "test": SNAPSHOTS_DATA_DIR / "test_v1.parquet",
        "unreleased": SNAPSHOTS_DATA_DIR / "unreleased_v1.parquet",
        "metadata": SNAPSHOTS_DATA_DIR / "feature_metadata.json",
    }

    # Save Parquet tables with Snappy compression
    for name, path, split_df in [
        ("Train", paths["train"], train_df),
        ("Validation", paths["val"], val_df),
        ("Test", paths["test"], test_df),
        ("Unreleased", paths["unreleased"], unreleased_df),
    ]:
        split_df.to_parquet(path, engine="pyarrow", compression="snappy", index=False)
        size_kb = path.stat().st_size / 1024
        logger.info(f"Saved {name} Gold Snapshot: {path.name} ({len(split_df):,} rows, {size_kb:.1f} KB)")

    # Save feature metadata definition
    metadata = {
        "version": "v1.0",
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "feature_count": len(FEATURE_COLUMNS),
        "target_columns": TARGET_COLUMNS,
        "metadata_columns": METADATA_COLUMNS,
        "splits": {
            "train_count": len(train_df),
            "val_count": len(val_df),
            "test_count": len(test_df),
            "unreleased_count": len(unreleased_df),
        },
    }
    with open(paths["metadata"], "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved feature metadata catalog to {paths['metadata'].name}.")
    return paths


if __name__ == "__main__":
    snapshots = save_gold_feature_snapshots()
    print("\n" + "=" * 70)
    print("CINEMETRICS — GOLD FEATURE STORE AUDIT (Phase 5 Complete)")
    print("=" * 70)
    for k, p in snapshots.items():
        if p.suffix == ".parquet":
            df = pd.read_parquet(p)
            print(f"Snapshot [{k.upper():<10}]: {p.name} | Rows: {len(df):,} | Cols: {df.shape[1]}")
        else:
            print(f"Catalog  [{k.upper():<10}]: {p.name}")
    print("=" * 70 + "\n")
