"""
CineMetrics — Kaggle Reference Datasets Ingestion Module
Downloads curated benchmark datasets (TMDB 5000, Bollywood box office) via Kaggle API.

Requires: kaggle.json or KAGGLE_USERNAME and KAGGLE_KEY in environment.
"""

import logging
import os
import shutil
import zipfile
from pathlib import Path
import pandas as pd

from ml.data_acquisition.config import KAGGLE_KEY, KAGGLE_RAW_DIR, KAGGLE_USERNAME

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("KaggleAcquisition")

# Reference Kaggle Datasets for Cinema Analytics
CURATED_DATASETS = [
    {
        "name": "tmdb-5000-movie-dataset",
        "slug": "tmdb/tmdb-movie-metadata",
        "primary_files": ["tmdb_5000_movies.csv", "tmdb_5000_credits.csv"],
    },
    {
        "name": "top-1000-bollywood",
        "slug": "bilalwaseer/top-1000-bollywood-movies-and-their-box-office",
        "primary_files": ["Top_1000_Bollywood_Movies.csv"],
    },
    {
        "name": "telugu-hindi-revenue",
        "slug": "meghanabmvrss/telugu-and-hindi-film-dataset-for-revenue-prediction",
        "primary_files": [],
    },
    {
        "name": "movie-industry-financials",
        "slug": "danielgrijalvas/movies",
        "primary_files": ["movies.csv"],
    },
]


def check_kaggle_credentials() -> bool:
    """Verifies whether Kaggle credentials are configured."""
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json.exists():
        return True
    access_token = Path.home() / ".kaggle" / "access_token"
    if access_token.exists():
        return True
    if os.environ.get("KAGGLE_API_TOKEN"):
        return True
    if KAGGLE_USERNAME and KAGGLE_KEY and KAGGLE_USERNAME != "your_kaggle_username":
        os.environ["KAGGLE_USERNAME"] = KAGGLE_USERNAME
        os.environ["KAGGLE_KEY"] = KAGGLE_KEY
        return True
    return False


def fetch_kaggle_dataset(dataset_slug: str, extract_to: Path) -> bool:
    """
    Downloads and extracts a dataset from Kaggle using the Kaggle Python API.
    """
    if not check_kaggle_credentials():
        logger.warning(
            f"Kaggle credentials not detected!\n"
            f"To download '{dataset_slug}' automatically:\n"
            f"1. Go to https://www.kaggle.com/settings -> API -> Create New Token.\n"
            f"2. Place 'kaggle.json' in: {Path.home() / '.kaggle / kaggle.json'}\n"
            f"   Or set KAGGLE_USERNAME and KAGGLE_KEY in '.env'."
        )
        return False

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()

        logger.info(f"Downloading Kaggle dataset: {dataset_slug}...")
        extract_to.mkdir(parents=True, exist_ok=True)
        api.dataset_download_files(dataset_slug, path=str(extract_to), unzip=True)
        logger.info(f"Successfully downloaded and extracted to {extract_to}.")
        return True
    except Exception as e:
        logger.error(f"Failed to download Kaggle dataset {dataset_slug}: {e}")
        return False


def convert_csvs_to_parquet(directory: Path):
    """Converts extracted CSV files into compressed Parquet files."""
    for csv_file in directory.glob("*.csv"):
        parquet_file = csv_file.with_suffix(".parquet")
        if not parquet_file.exists():
            logger.info(f"Converting {csv_file.name} -> {parquet_file.name}...")
            try:
                df = pd.read_csv(csv_file, low_memory=False)
                df.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=False)
                logger.info(f"Converted {len(df):,} rows.")
            except Exception as e:
                logger.warning(f"Could not convert {csv_file.name}: {e}")


def run_kaggle_acquisition():
    """Acquires all curated Kaggle reference datasets."""
    logger.info("Starting Kaggle Datasets Acquisition...")
    for ds in CURATED_DATASETS:
        target_dir = KAGGLE_RAW_DIR / ds["name"]
        success = fetch_kaggle_dataset(ds["slug"], target_dir)
        if success:
            convert_csvs_to_parquet(target_dir)


if __name__ == "__main__":
    run_kaggle_acquisition()

