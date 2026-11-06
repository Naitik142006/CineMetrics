"""
CineMetrics — Commercial Success Classification Engine
Implements documented cinema economics methodology to categorize theatrical performance.
"""

import math
from typing import Optional, Tuple


def calculate_success_category(
    revenue_usd: Optional[float],
    budget_usd: Optional[float],
    industry: str = "Hollywood",
) -> Tuple[str, Optional[float]]:
    """
    Categorizes theatrical commercial performance using economic ROI thresholds.

    Categories:
    - Blockbuster:  ROI >= 3.0 AND (Revenue >= $100M OR Indian Revenue >= $30M (~250 Cr))
    - Super Hit:    ROI >= 2.5
    - Hit:          ROI >= 2.0
    - Average:      1.2 <= ROI < 2.0
    - Below Average: 0.8 <= ROI < 1.2
    - Flop:         0.4 <= ROI < 0.8
    - Disaster:     ROI < 0.4

    Returns:
        (category_name, roi_multiplier)
    """
    if (
        revenue_usd is None
        or budget_usd is None
        or math.isnan(revenue_usd)
        or math.isnan(budget_usd)
        or budget_usd <= 10_000  # Below minimum credible budget threshold
        or revenue_usd < 0
    ):
        return ("Unknown", None)

    roi = round(revenue_usd / budget_usd, 3)

    # Volume gate for Blockbuster
    is_indian = industry.lower() in ("indian", "bollywood", "tollywood", "kollywood", "mollywood", "sandalwood")
    min_blockbuster_gross = 30_000_000 if is_indian else 100_000_000

    if roi >= 3.0 and revenue_usd >= min_blockbuster_gross:
        return ("Blockbuster", roi)
    elif roi >= 2.5:
        return ("Super Hit", roi)
    elif roi >= 2.0:
        return ("Hit", roi)
    elif 1.2 <= roi < 2.0:
        return ("Average", roi)
    elif 0.8 <= roi < 1.2:
        return ("Below Average", roi)
    elif 0.4 <= roi < 0.8:
        return ("Flop", roi)
    else:
        return ("Disaster", roi)


if __name__ == "__main__":
    test_cases = [
        {"rev": 1_000_000_000, "bud": 150_000_000, "ind": "Hollywood"}, # ROI 6.67 -> Blockbuster
        {"rev": 250_000_000, "bud": 100_000_000, "ind": "Hollywood"},   # ROI 2.5 -> Super Hit
        {"rev": 150_000_000, "bud": 100_000_000, "ind": "Hollywood"},   # ROI 1.5 -> Average
        {"rev": 60_000_000, "bud": 100_000_000, "ind": "Hollywood"},    # ROI 0.6 -> Flop
        {"rev": 20_000_000, "bud": 100_000_000, "ind": "Hollywood"},    # ROI 0.2 -> Disaster
    ]
    for tc in test_cases:
        cat, roi = calculate_success_category(tc["rev"], tc["bud"], tc["ind"])
        print(f"Revenue: ${tc['rev']:,.0f} | Budget: ${tc['bud']:,.0f} -> Category: {cat} (ROI: {roi}x)")

