"""
CineMetrics — EDA: Talent Equity & Power-Law Concentration Analysis
Quantifies commercial concentration and track-record predictability across directors & actors.
"""

from typing import Dict, List
import pandas as pd

from ml.dataset_engineering.config import UNIFIED_MOVIES_PATH


def analyze_talent_equity(df: pd.DataFrame) -> Dict:
    """
    Examines talent equity and revenue concentration (Pareto principle) in cinema.
    """
    df_fin = df.dropna(subset=["revenue_real_2024_usd"]).copy()
    total_rev_pool = df_fin["revenue_real_2024_usd"].sum()

    # 1. Director Analysis
    df_dir = df_fin.dropna(subset=["director"]).copy()
    dir_agg = (
        df_dir.groupby("director")
        .agg(
            film_count=("canonical_id", "count"),
            total_real_gross=("revenue_real_2024_usd", "sum"),
            median_real_gross=("revenue_real_2024_usd", "median"),
            median_roi=("roi_multiplier", "median"),
        )
        .reset_index()
    )
    dir_agg = dir_agg[dir_agg["film_count"] >= 3].sort_values(by="total_real_gross", ascending=False)

    top_directors = []
    for _, r in dir_agg.head(12).iterrows():
        top_directors.append({
            "director": r["director"],
            "film_count": int(r["film_count"]),
            "total_gross_usd": float(r["total_real_gross"]),
            "median_gross_usd": float(r["median_real_gross"]),
            "median_roi": float(r["median_roi"]) if pd.notna(r["median_roi"]) else 0.0,
        })

    # 2. Lead Actor Analysis
    df_act = df_fin.dropna(subset=["lead_actor"]).copy()
    act_agg = (
        df_act.groupby("lead_actor")
        .agg(
            film_count=("canonical_id", "count"),
            total_real_gross=("revenue_real_2024_usd", "sum"),
            median_real_gross=("revenue_real_2024_usd", "median"),
            median_roi=("roi_multiplier", "median"),
        )
        .reset_index()
    )
    act_agg = act_agg[act_agg["film_count"] >= 3].sort_values(by="total_real_gross", ascending=False)

    top_actors = []
    for _, r in act_agg.head(12).iterrows():
        top_actors.append({
            "actor": r["lead_actor"],
            "film_count": int(r["film_count"]),
            "total_gross_usd": float(r["total_real_gross"]),
            "median_gross_usd": float(r["median_real_gross"]),
            "median_roi": float(r["median_roi"]) if pd.notna(r["median_roi"]) else 0.0,
        })

    # 3. Pareto Principle (Revenue Concentration)
    # Sort all films by revenue
    sorted_revs = df_fin["revenue_real_2024_usd"].sort_values(ascending=False).values
    n = len(sorted_revs)
    top_1pct_idx = max(1, int(n * 0.01))
    top_5pct_idx = max(1, int(n * 0.05))
    top_10pct_idx = max(1, int(n * 0.10))
    top_20pct_idx = max(1, int(n * 0.20))

    concentration = {
        "total_revenue_pool_usd": float(total_rev_pool),
        "top_1pct_revenue_share": round(float(sorted_revs[:top_1pct_idx].sum() / total_rev_pool * 100), 2),
        "top_5pct_revenue_share": round(float(sorted_revs[:top_5pct_idx].sum() / total_rev_pool * 100), 2),
        "top_10pct_revenue_share": round(float(sorted_revs[:top_10pct_idx].sum() / total_rev_pool * 100), 2),
        "top_20pct_revenue_share": round(float(sorted_revs[:top_20pct_idx].sum() / total_rev_pool * 100), 2),
    }

    return {
        "top_directors": top_directors,
        "top_actors": top_actors,
        "concentration": concentration,
    }


if __name__ == "__main__":
    df = pd.read_parquet(UNIFIED_MOVIES_PATH)
    res = analyze_talent_equity(df)
    print("Concentration:", res["concentration"])
    print("Top Director:", res["top_directors"][0])
    print("Top Actor:", res["top_actors"][0])
