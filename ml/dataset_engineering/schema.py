"""
CineMetrics — Pandera Data Quality & Schema Validation Specification
Validates the Silver Layer (unified_movies.parquet) single source of truth.
"""

import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

# Success categories permitted by CineMetrics economic methodology
VALID_SUCCESS_CATEGORIES = [
    "Blockbuster",
    "Super Hit",
    "Hit",
    "Average",
    "Below Average",
    "Flop",
    "Disaster",
    "Unknown",
]

# Industries tracked
VALID_INDUSTRIES = [
    "Hollywood",
    "Bollywood",
    "Tollywood",
    "Kollywood",
    "Mollywood",
    "Sandalwood",
    "Regional Indian",
    "International",
]

UnifiedMovieSchema = DataFrameSchema(
    columns={
        "canonical_id": Column(str, Check.str_length(min_value=32, max_value=36), nullable=False, unique=True),
        "primary_title": Column(str, Check.str_length(min_value=1), nullable=False),
        "original_title": Column(str, nullable=True),
        "release_year": Column(float, Check.in_range(1888, 2035), nullable=True),
        "release_date": Column(str, nullable=True),
        "runtime_minutes": Column(float, Check.in_range(0, 1000), nullable=True),
        "genres": Column(str, nullable=True),
        "original_language": Column(str, nullable=True),
        "industry": Column(str, nullable=False),
        "imdb_tconst": Column(str, Check.str_matches(r"^tt\d+$"), nullable=True),
        "imdb_rating": Column(float, Check.in_range(1.0, 10.0), nullable=True),
        "imdb_vote_count": Column(float, Check.greater_than_or_equal_to(0), nullable=True),
        "tmdb_id": Column(float, nullable=True),
        "budget_nominal_usd": Column(float, Check.greater_than_or_equal_to(0), nullable=True),
        "revenue_nominal_usd": Column(float, Check.greater_than_or_equal_to(0), nullable=True),
        "budget_real_2024_usd": Column(float, Check.greater_than_or_equal_to(0), nullable=True),
        "revenue_real_2024_usd": Column(float, Check.greater_than_or_equal_to(0), nullable=True),
        "roi_multiplier": Column(float, nullable=True),
        "success_category": Column(str, Check.isin(VALID_SUCCESS_CATEGORIES), nullable=False),
        "director": Column(str, nullable=True),
        "lead_actor": Column(str, nullable=True),
        "production_company": Column(str, nullable=True),
        "source_provenance": Column(str, nullable=False),
        "data_quality_tier": Column(int, Check.isin([1, 2, 3]), nullable=False),
        "updated_at": Column(str, nullable=False),
    },
    coerce=True,
    strict=False,
)
