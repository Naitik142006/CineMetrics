"""
CineMetrics — Data Acquisition Configuration Module
Handles environment variables, API keys, and data storage paths.
"""

import os
from pathlib import Path

# Resolve base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file if it exists
def load_env():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val

load_env()

# Data Storage Directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
IMDB_RAW_DIR = RAW_DATA_DIR / "imdb"
TMDB_RAW_DIR = RAW_DATA_DIR / "tmdb"
THE_NUMBERS_RAW_DIR = RAW_DATA_DIR / "the_numbers"
KAGGLE_RAW_DIR = RAW_DATA_DIR / "kaggle"
INDIAN_TRADE_RAW_DIR = RAW_DATA_DIR / "indian_trade"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
UNIFIED_DATA_DIR = DATA_DIR / "unified"
SNAPSHOTS_DATA_DIR = DATA_DIR / "snapshots"

# Ensure raw data directories exist
for directory in [
    RAW_DATA_DIR,
    IMDB_RAW_DIR,
    TMDB_RAW_DIR,
    THE_NUMBERS_RAW_DIR,
    KAGGLE_RAW_DIR,
    INDIAN_TRADE_RAW_DIR,
    PROCESSED_DATA_DIR,
    UNIFIED_DATA_DIR,
    SNAPSHOTS_DATA_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# API Keys
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
YOUTUBE_DATA_API_KEY = os.environ.get("YOUTUBE_DATA_API_KEY", "")
KAGGLE_USERNAME = os.environ.get("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.environ.get("KAGGLE_KEY", "")

# Upstream URLs
IMDB_DATASETS_BASE_URL = "https://datasets.imdbws.com/"
IMDB_FILES = [
    "title.basics.tsv.gz",
    "title.ratings.tsv.gz",
    "title.crew.tsv.gz",
    "title.principals.tsv.gz",
    "name.basics.tsv.gz",
]

TMDB_API_BASE_URL = "https://api.themoviedb.org/3"

