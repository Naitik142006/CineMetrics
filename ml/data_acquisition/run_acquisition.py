"""
CineMetrics — Master Dataset Acquisition Runner
Orchestrates multi-source data acquisition across IMDb, The Numbers, TMDB, and Kaggle.
"""

import argparse
import logging
import sys
from pathlib import Path
import pandas as pd

from ml.data_acquisition.config import (
    BASE_DIR,
    IMDB_RAW_DIR,
    KAGGLE_RAW_DIR,
    THE_NUMBERS_RAW_DIR,
    TMDB_API_KEY,
    TMDB_RAW_DIR,
    YOUTUBE_DATA_API_KEY,
)
from ml.data_acquisition.download_imdb import run_imdb_acquisition
from ml.data_acquisition.fetch_the_numbers import fetch_the_numbers_budgets
from ml.data_acquisition.fetch_tmdb import harvest_indian_cinema_catalog, harvest_upcoming_movies
from ml.data_acquisition.fetch_kaggle import run_kaggle_acquisition
from ml.data_acquisition.fetch_youtube import check_youtube_credentials, harvest_trailer_metrics_sample

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("AcquisitionRunner")


def print_status_summary():
    """Scans and reports on currently available raw Parquet datasets."""
    print("\n" + "=" * 70)
    print("CINEMETRICS — RAW DATA LAKE STATUS REPORT (Bronze Layer)")
    print("=" * 70)
    
    rows = []
    YOUTUBE_RAW_DIR = BASE_DIR / "data" / "raw" / "youtube"
    for directory, source in [
        (IMDB_RAW_DIR, "IMDb Non-Commercial"),
        (THE_NUMBERS_RAW_DIR, "The Numbers"),
        (TMDB_RAW_DIR, "TMDB API"),
        (KAGGLE_RAW_DIR, "Kaggle Curated"),
        (YOUTUBE_RAW_DIR, "YouTube Trailer API"),
    ]:
        for parquet_file in directory.rglob("*.parquet"):
            try:
                df = pd.read_parquet(parquet_file)
                size_mb = parquet_file.stat().st_size / (1024 * 1024)
                rows.append({
                    "Source": source,
                    "File Name": parquet_file.name,
                    "Record Count": f"{len(df):,}",
                    "Size (MB)": f"{size_mb:.2f} MB",
                })
            except Exception:
                pass

    if rows:
        summary_df = pd.DataFrame(rows)
        print(summary_df.to_string(index=False))
    else:
        print("No Parquet datasets found in data/raw/ yet.")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="CineMetrics Multi-Source Dataset Ingestion Runner")
    parser.add_argument("--imdb", action="store_true", help="Download and process IMDb datasets (Zero API key needed)")
    parser.add_argument("--the-numbers", action="store_true", help="Fetch The Numbers budget reference tables (Zero API key needed)")
    parser.add_argument("--tmdb", action="store_true", help="Harvest upcoming movies & Indian cinema from TMDB API (Requires TMDB_API_KEY)")
    parser.add_argument("--kaggle", action="store_true", help="Download Kaggle benchmark datasets (Requires Kaggle credentials)")
    parser.add_argument("--youtube", action="store_true", help="Harvest YouTube trailer engagement metrics (Requires YOUTUBE_DATA_API_KEY)")
    parser.add_argument("--all", action="store_true", help="Execute all ingestion pipelines")
    parser.add_argument("--status", action="store_true", help="Print current raw lake status summary")

    args = parser.parse_args()

    # If no flags specified, print status and help
    if not any([args.imdb, args.the_numbers, args.tmdb, args.kaggle, args.youtube, args.all, args.status]):
        print_status_summary()
        parser.print_help()
        return

    if args.status:
        print_status_summary()
        return

    # 1. IMDb Datasets (Public - Zero Key Needed)
    if args.imdb or args.all:
        logger.info("Executing IMDb acquisition...")
        run_imdb_acquisition()

    # 2. The Numbers Budgets (Public Reference - Zero Key Needed)
    if args.the_numbers or args.all:
        logger.info("Executing The Numbers budget acquisition...")
        fetch_the_numbers_budgets()

    # 3. TMDB Ingestion (Requires TMDB_API_KEY)
    if args.tmdb or args.all:
        if not TMDB_API_KEY or TMDB_API_KEY == "your_tmdb_api_key_here":
            logger.warning(
                "Skipping TMDB ingestion: TMDB_API_KEY not configured in .env.\n"
                "To enable TMDB: add TMDB_API_KEY to your .env file."
            )
        else:
            logger.info("Executing TMDB upcoming harvest...")
            harvest_upcoming_movies()
            logger.info("Executing TMDB Indian cinema catalog harvest...")
            harvest_indian_cinema_catalog(start_year=2018, end_year=2024, pages_per_year=2)

    # 4. Kaggle Ingestion (Requires Kaggle API)
    if args.kaggle or args.all:
        logger.info("Executing Kaggle acquisition...")
        run_kaggle_acquisition()

    # 5. YouTube Trailer Ingestion (Requires YOUTUBE_DATA_API_KEY)
    if args.youtube or args.all:
        if not check_youtube_credentials():
            logger.warning("YOUTUBE_DATA_API_KEY is not configured. Skipping YouTube acquisition.")
        else:
            logger.info("Executing YouTube trailer acquisition sample...")
            sample_movies = [
                {"title": "Kalki 2898 AD", "year": 2024},
                {"title": "Jawan", "year": 2023},
                {"title": "Oppenheimer", "year": 2023},
                {"title": "Dune: Part Two", "year": 2024},
            ]
            harvest_trailer_metrics_sample(sample_movies)

    # Print final summary
    print_status_summary()


if __name__ == "__main__":
    main()

