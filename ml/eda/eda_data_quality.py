"""
CineMetrics — EDA: Data Quality & Missingness Audit
Evaluates field-level completeness, null-rates, and reliability tiers across cinema epochs.
"""

from typing import Dict, List
import pandas as pd

from ml.dataset_engineering.config import UNIFIED_MOVIES_PATH


def audit_data_quality(df: pd.DataFrame) -> Dict:
    """
    Performs comprehensive data completeness and null-rate auditing on the Silver Lakehouse.
    """
    total_rows = len(df)
    field_audit = []

    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = round((null_count / total_rows) * 100, 2)
        valid_count = total_rows - null_count
        valid_pct = round((valid_count / total_rows) * 100, 2)

        field_audit.append({
            "column": col,
            "data_type": str(df[col].dtype),
            "valid_records": valid_count,
            "null_records": null_count,
            "completeness_pct": valid_pct,
            "null_pct": null_pct,
        })

    # Decade-based completeness
    df_epoch = df.copy()
    df_epoch["decade"] = (df_epoch["release_year"] // 10 * 10).fillna(0).astype(int)
    epoch_summary = []
    decades = [1980, 1990, 2000, 2010, 2020]

    for d in decades:
        sub = df_epoch[df_epoch["decade"] == d]
        n_d = len(sub)
        if n_d > 0:
            fin_complete = sub["budget_nominal_usd"].notna() & sub["revenue_nominal_usd"].notna()
            imdb_complete = sub["imdb_tconst"].notna()
            epoch_summary.append({
                "decade": f"{d}s",
                "movie_count": n_d,
                "financial_completeness_pct": round(fin_complete.mean() * 100, 1),
                "imdb_resolution_pct": round(imdb_complete.mean() * 100, 1),
            })

    # Data Quality Tier Breakdown
    tier_counts = df["data_quality_tier"].value_counts().to_dict()
    tier_summary = {
        "Tier 1 (Verified Budget & Revenue)": int(tier_counts.get(1, 0)),
        "Tier 2 (Partial Financials)": int(tier_counts.get(2, 0)),
        "Tier 3 (Metadata Only / Upcoming)": int(tier_counts.get(3, 0)),
    }

    return {
        "total_records": total_rows,
        "field_audit": field_audit,
        "epoch_summary": epoch_summary,
        "tier_summary": tier_summary,
    }


if __name__ == "__main__":
    df = pd.read_parquet(UNIFIED_MOVIES_PATH)
    res = audit_data_quality(df)
    print("Total Records:", res["total_records"])
    print("Tier Summary:", res["tier_summary"])
    for ep in res["epoch_summary"]:
        print(ep)

