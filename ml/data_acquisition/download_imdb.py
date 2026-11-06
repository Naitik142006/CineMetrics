"""
CineMetrics — IMDb Non-Commercial Dataset Acquisition Engine
Downloads public official IMDb gzip archives, filters movie entities on-the-fly,
and converts to optimized Snappy Parquet partitions.

Source: https://datasets.imdbws.com/
Licensing: Free for personal and non-commercial educational/portfolio research.
Zero API keys required.
"""

import gzip
import logging
import sys
import time
from pathlib import Path
import pandas as pd
import requests

from ml.data_acquisition.config import (
    IMDB_DATASETS_BASE_URL,
    IMDB_FILES,
    IMDB_RAW_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("IMDbAcquisition")


def download_file(url: str, dest_path: Path, chunk_size: int = 1024 * 1024) -> Path:
    """
    Downloads an archive from a URL with progress reporting.
    Skips if file already exists with non-zero size.
    """
    if dest_path.exists() and dest_path.stat().st_size > 0:
        logger.info(f"File already exists: {dest_path.name} ({dest_path.stat().st_size / (1024*1024):.1f} MB). Skipping download.")
        return dest_path

    logger.info(f"Downloading {url} -> {dest_path.name}...")
    start_time = time.time()
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    total_bytes = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_bytes > 0:
                    percent = (downloaded / total_bytes) * 100
                    mb_downloaded = downloaded / (1024 * 1024)
                    mb_total = total_bytes / (1024 * 1024)
                    sys.stdout.write(f"\r  Progress: {mb_downloaded:.1f}/{mb_total:.1f} MB ({percent:.1f}%)")
                    sys.stdout.flush()

    sys.stdout.write("\n")
    elapsed = time.time() - start_time
    logger.info(f"Successfully downloaded {dest_path.name} in {elapsed:.1f}s.")
    return dest_path


def process_title_basics(tsv_gz_path: Path) -> Path:
    """
    Reads title.basics.tsv.gz in chunks, filters to titleType in ('movie', 'tvMovie'),
    and outputs a compact Parquet file.
    Reduces ~10M records down to ~700k relevant movie records!
    """
    parquet_path = IMDB_RAW_DIR / "title_basics_movies.parquet"
    if parquet_path.exists() and parquet_path.stat().st_size > 0:
        logger.info(f"Parquet file already exists: {parquet_path.name}. Skipping conversion.")
        return parquet_path

    logger.info("Processing title.basics.tsv.gz (Filtering movies only)...")
    chunks = []
    chunk_size = 200_000
    total_processed = 0
    total_retained = 0

    # Dtype specification for fast reading
    dtypes = {
        "tconst": "string",
        "titleType": "category",
        "primaryTitle": "string",
        "originalTitle": "string",
        "isAdult": "string",
        "startYear": "string",
        "endYear": "string",
        "runtimeMinutes": "string",
        "genres": "string",
    }

    with gzip.open(tsv_gz_path, "rt", encoding="utf-8") as f:
        for chunk in pd.read_csv(
            f,
            sep="\t",
            na_values="\\N",
            dtype=dtypes,
            chunksize=chunk_size,
            low_memory=False,
        ):
            total_processed += len(chunk)
            # Filter strictly for movie types
            movie_chunk = chunk[chunk["titleType"].isin(["movie", "tvMovie"])].copy()
            
            # Clean types
            movie_chunk["isAdult"] = pd.to_numeric(movie_chunk["isAdult"], errors="coerce").fillna(0).astype("int8")
            movie_chunk["startYear"] = pd.to_numeric(movie_chunk["startYear"], errors="coerce")
            movie_chunk["runtimeMinutes"] = pd.to_numeric(movie_chunk["runtimeMinutes"], errors="coerce")

            total_retained += len(movie_chunk)
            chunks.append(movie_chunk)
            sys.stdout.write(f"\r  Scanned: {total_processed:,} | Retained Movies: {total_retained:,}")
            sys.stdout.flush()

    sys.stdout.write("\n")
    df_movies = pd.concat(chunks, ignore_index=True)
    df_movies.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)
    logger.info(f"Wrote {len(df_movies):,} movies to {parquet_path.name} ({parquet_path.stat().st_size / (1024*1024):.1f} MB).")
    return parquet_path


def process_title_ratings(tsv_gz_path: Path, valid_tconsts: set = None) -> Path:
    """
    Processes title.ratings.tsv.gz, optionally filtering to movies in valid_tconsts.
    """
    parquet_path = IMDB_RAW_DIR / "title_ratings_movies.parquet"
    if parquet_path.exists() and parquet_path.stat().st_size > 0:
        logger.info(f"Parquet file already exists: {parquet_path.name}. Skipping conversion.")
        return parquet_path

    logger.info("Processing title.ratings.tsv.gz...")
    dtypes = {
        "tconst": "string",
        "averageRating": "float32",
        "numVotes": "int32",
    }

    with gzip.open(tsv_gz_path, "rt", encoding="utf-8") as f:
        df_ratings = pd.read_csv(f, sep="\t", na_values="\\N", dtype=dtypes)

    if valid_tconsts:
        initial_len = len(df_ratings)
        df_ratings = df_ratings[df_ratings["tconst"].isin(valid_tconsts)].copy()
        logger.info(f"Filtered ratings from {initial_len:,} to {len(df_ratings):,} matching movie records.")

    df_ratings.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)
    logger.info(f"Wrote {len(df_ratings):,} rating records to {parquet_path.name}.")
    return parquet_path


def run_imdb_acquisition(download_all: bool = False, files_subset: list = None):
    """
    Main acquisition runner for IMDb datasets.
    By default, downloads title.basics and title.ratings (essential for core catalog and ratings).
    Set download_all=True to also download principals, crew, and name.basics.
    """
    logger.info("=====================================================")
    logger.info("Starting IMDb Non-Commercial Dataset Acquisition")
    logger.info("=====================================================")

    target_files = files_subset or (IMDB_FILES if download_all else ["title.basics.tsv.gz", "title.ratings.tsv.gz"])

    downloaded_paths = {}
    for filename in target_files:
        url = IMDB_DATASETS_BASE_URL + filename
        dest = IMDB_RAW_DIR / filename
        try:
            path = download_file(url, dest)
            downloaded_paths[filename] = path
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")

    # Process and convert to Parquet
    valid_movie_tconsts = set()
    if "title.basics.tsv.gz" in downloaded_paths:
        basics_parquet = process_title_basics(downloaded_paths["title.basics.tsv.gz"])
        # Extract movie tconsts to filter ratings
        df_basics = pd.read_parquet(basics_parquet, columns=["tconst"])
        valid_movie_tconsts = set(df_basics["tconst"].dropna().values)

    if "title.ratings.tsv.gz" in downloaded_paths:
        process_title_ratings(downloaded_paths["title.ratings.tsv.gz"], valid_movie_tconsts)

    logger.info("IMDb Dataset Acquisition completed successfully.")


if __name__ == "__main__":
    download_all = "--all" in sys.argv
    run_imdb_acquisition(download_all=download_all)

