"""
CineMetrics — EDA: Cross-Industry & Regional Cinema Economics
Compares financial structures, ROI multipliers, and success rates across cinema markets.
"""

from typing import Dict, List
import pandas as pd

from ml.dataset_engineering.config import UNIFIED_MOVIES_PATH


def analyze_regional_economics(df: pd.DataFrame) -> List[Dict]:
    """
    Evaluates cinema performance metrics stratified by industry / regional market.
    """
    results = []
    industries = df["industry"].value_counts().index.tolist()

    for ind in industries:
        sub = df[df["industry"] == ind].copy()
        fin_sub = sub.dropna(subset=["budget_real_2024_usd", "revenue_real_2024_usd"])
        fin_sub = fin_sub[(fin_sub["budget_real_2024_usd"] > 10_000) & (fin_sub["revenue_real_2024_usd"] > 10_000)]

        total_movies = len(sub)
        fin_movies = len(fin_sub)

        if fin_movies > 0:
            med_budget = float(fin_sub["budget_real_2024_usd"].median())
            med_revenue = float(fin_sub["revenue_real_2024_usd"].median())
            med_roi = float(fin_sub["roi_multiplier"].median())
            total_gross = float(fin_sub["revenue_real_2024_usd"].sum())

            # Success category percentages
            cat_counts = fin_sub["success_category"].value_counts(normalize=True).to_dict()
            blockbuster_pct = round(cat_counts.get("Blockbuster", 0.0) * 100, 1)
            hit_pct = round(
                (cat_counts.get("Blockbuster", 0.0) + cat_counts.get("Super Hit", 0.0) + cat_counts.get("Hit", 0.0))
                * 100,
                1,
            )
            flop_pct = round(
                (cat_counts.get("Flop", 0.0) + cat_counts.get("Disaster", 0.0)) * 100,
                1,
            )
        else:
            med_budget, med_revenue, med_roi, total_gross = 0.0, 0.0, 0.0, 0.0
            blockbuster_pct, hit_pct, flop_pct = 0.0, 0.0, 0.0

        results.append({
            "industry": ind,
            "total_catalog": total_movies,
            "financial_sample": fin_movies,
            "median_budget_usd": med_budget,
            "median_revenue_usd": med_revenue,
            "median_roi": med_roi,
            "total_box_office_usd": total_gross,
            "hit_rate_pct": hit_pct,
            "blockbuster_pct": blockbuster_pct,
            "flop_rate_pct": flop_pct,
        })

    return results


if __name__ == "__main__":
    df = pd.read_parquet(UNIFIED_MOVIES_PATH)
    res = analyze_regional_economics(df)
    for r in res:
        print(f"Industry: {r['industry']} | Sample: {r['financial_sample']} | Med Budget: ${r['median_budget_usd']:,.0f} | Med ROI: {r['median_roi']}x | Hit Rate: {r['hit_rate_pct']}%")
