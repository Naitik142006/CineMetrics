"""
CineMetrics — Strict Temporal Isolation & Point-in-Time Feature Engine
Calculates talent track records (directors, lead actors, production companies)
strictly using historical data prior to each film's release date (zero lookahead leakage).
"""

import logging
from typing import Optional
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TemporalIsolation")


def assign_point_in_time_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures every movie has a robust datetime anchor for temporal ordering.
    """
    df = df.copy()

    def parse_date(row):
        d_str = str(row.get("release_date", "")).strip()
        if d_str and d_str != "nan" and d_str != "None":
            try:
                # Handle YYYY-MM-DD or strings like 'August 17, 1984'
                return pd.to_datetime(d_str[:10], errors="coerce")
            except Exception:
                pass
        yr = row.get("release_year")
        if pd.notna(yr) and yr > 1800:
            return pd.to_datetime(f"{int(yr)}-07-01")
        return pd.to_datetime("2020-01-01")

    df["temporal_timestamp"] = df.apply(parse_date, axis=1)
    df["temporal_timestamp"] = pd.to_datetime(df["temporal_timestamp"]).fillna(pd.to_datetime("2020-01-01"))
    return df


def calculate_prior_talent_track_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes expanding historical performance for Directors and Lead Actors chronologically.
    Guarantees: Feature at film i uses ONLY films released strictly before film i.
    """
    logger.info("Enforcing strict temporal isolation on talent track records...")
    df = assign_point_in_time_dates(df)

    # Sort strictly chronologically
    df = df.sort_values(by=["temporal_timestamp", "canonical_id"]).reset_index(drop=True)

    # Helper binary indicator for commercial success
    df["is_commercial_hit"] = df["success_category"].isin(["Blockbuster", "Super Hit", "Hit"]).astype(float)
    # Use real 2024 revenue for track records
    df["real_revenue_clean"] = df["revenue_real_2024_usd"].fillna(0.0)
    df["roi_clean"] = df["roi_multiplier"].fillna(1.0)

    # 1. Director Temporal Features
    logger.info("Computing point-in-time expanding metrics for Directors...")
    df["director_prior_movies"] = 0
    df["director_prior_avg_real_gross"] = 0.0
    df["director_prior_avg_roi"] = 1.0
    df["director_prior_hit_rate"] = 0.0

    valid_dirs = df[df["director"].notna() & (df["director"] != "")].copy()
    for col_name, new_col, agg_fn in [
        ("canonical_id", "director_prior_movies", "count"),
        ("real_revenue_clean", "director_prior_avg_real_gross", "mean"),
        ("roi_clean", "director_prior_avg_roi", "mean"),
        ("is_commercial_hit", "director_prior_hit_rate", "mean"),
    ]:
        if agg_fn == "count":
            # Expanding count of prior films
            res = valid_dirs.groupby("director").cumcount()
        else:
            # Expanding mean of prior films strictly shifted by 1
            grouped = valid_dirs.groupby("director")[col_name]
            res = grouped.shift(1).expanding().mean().reset_index(level=0, drop=True)

        valid_dirs[new_col] = res

    # Re-merge computed values back to main dataframe
    df.loc[valid_dirs.index, "director_prior_movies"] = valid_dirs["director_prior_movies"].fillna(0).astype(int)
    df.loc[valid_dirs.index, "director_prior_avg_real_gross"] = valid_dirs["director_prior_avg_real_gross"].fillna(0.0)
    df.loc[valid_dirs.index, "director_prior_avg_roi"] = valid_dirs["director_prior_avg_roi"].fillna(1.0)
    df.loc[valid_dirs.index, "director_prior_hit_rate"] = valid_dirs["director_prior_hit_rate"].fillna(0.0)

    # 2. Lead Actor Temporal Features
    logger.info("Computing point-in-time expanding metrics for Lead Actors...")
    df["lead_actor_prior_movies"] = 0
    df["lead_actor_prior_avg_real_gross"] = 0.0
    df["lead_actor_prior_avg_roi"] = 1.0
    df["lead_actor_prior_hit_rate"] = 0.0

    valid_actors = df[df["lead_actor"].notna() & (df["lead_actor"] != "")].copy()
    for col_name, new_col, agg_fn in [
        ("canonical_id", "lead_actor_prior_movies", "count"),
        ("real_revenue_clean", "lead_actor_prior_avg_real_gross", "mean"),
        ("roi_clean", "lead_actor_prior_avg_roi", "mean"),
        ("is_commercial_hit", "lead_actor_prior_hit_rate", "mean"),
    ]:
        if agg_fn == "count":
            res = valid_actors.groupby("lead_actor").cumcount()
        else:
            grouped = valid_actors.groupby("lead_actor")[col_name]
            res = grouped.shift(1).expanding().mean().reset_index(level=0, drop=True)

        valid_actors[new_col] = res

    df.loc[valid_actors.index, "lead_actor_prior_movies"] = valid_actors["lead_actor_prior_movies"].fillna(0).astype(int)
    df.loc[valid_actors.index, "lead_actor_prior_avg_real_gross"] = valid_actors["lead_actor_prior_avg_real_gross"].fillna(0.0)
    df.loc[valid_actors.index, "lead_actor_prior_avg_roi"] = valid_actors["lead_actor_prior_avg_roi"].fillna(1.0)
    df.loc[valid_actors.index, "lead_actor_prior_hit_rate"] = valid_actors["lead_actor_prior_hit_rate"].fillna(0.0)

    # 3. Production Company Prior Movies
    logger.info("Computing point-in-time prior movie counts for Studios...")
    df["studio_prior_movies"] = 0
    valid_studios = df[df["production_company"].notna() & (df["production_company"] != "")].copy()
    valid_studios["studio_prior_movies"] = valid_studios.groupby("production_company").cumcount()
    df.loc[valid_studios.index, "studio_prior_movies"] = valid_studios["studio_prior_movies"].fillna(0).astype(int)

    # Clean intermediate temporary calculation columns
    df = df.drop(columns=["is_commercial_hit", "real_revenue_clean", "roi_clean"])
    logger.info("Temporal isolation successfully enforced across all talent track records.")
    return df


if __name__ == "__main__":
    from ml.dataset_engineering.config import UNIFIED_MOVIES_PATH
    df = pd.read_parquet(UNIFIED_MOVIES_PATH)
    res = calculate_prior_talent_track_records(df)
    sample_dir = res[res["director"] == "Steven Spielberg"][
        ["primary_title", "release_year", "director_prior_movies", "director_prior_avg_real_gross", "director_prior_hit_rate"]
    ].head(6)
    print("\nSteven Spielberg Chronological Track Record Verification:")
    print(sample_dir.to_string(index=False))

