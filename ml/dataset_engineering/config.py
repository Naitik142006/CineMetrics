"""
CineMetrics — Unified Dataset Engineering Configuration
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
UNIFIED_DATA_DIR = DATA_DIR / "unified"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SNAPSHOTS_DATA_DIR = DATA_DIR / "snapshots"

# Ensure directories exist
UNIFIED_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Raw source file paths
IMDB_BASICS_PATH = RAW_DATA_DIR / "imdb" / "title_basics_movies.parquet"
IMDB_RATINGS_PATH = RAW_DATA_DIR / "imdb" / "title_ratings_movies.parquet"
TMDB_5000_MOVIES_PATH = RAW_DATA_DIR / "kaggle" / "tmdb-5000-movie-dataset" / "tmdb_5000_movies.parquet"
TMDB_5000_CREDITS_PATH = RAW_DATA_DIR / "kaggle" / "tmdb-5000-movie-dataset" / "tmdb_5000_credits.parquet"
MOVIE_INDUSTRY_PATH = RAW_DATA_DIR / "kaggle" / "movie-industry-financials" / "movies.parquet"
BOLLYWOOD_1000_PATH = RAW_DATA_DIR / "kaggle" / "top-1000-bollywood" / "Top 1000 Bollywood Movies and their boxoffice.parquet"
TELUGU_HINDI_PATH = RAW_DATA_DIR / "kaggle" / "telugu-hindi-revenue" / "Movie Data.parquet"
TMDB_UPCOMING_PATH = RAW_DATA_DIR / "tmdb" / "tmdb_upcoming.parquet"
TMDB_INDIAN_CATALOG_PATH = RAW_DATA_DIR / "tmdb" / "tmdb_indian_catalog.parquet"
YOUTUBE_TRAILERS_PATH = RAW_DATA_DIR / "youtube" / "trailer_metrics.parquet"

# Unified Silver target
UNIFIED_MOVIES_PATH = UNIFIED_DATA_DIR / "unified_movies.parquet"

