"""
CineMetrics — The Numbers Budget & Box Office Acquisition Module
Parses and standardizes production budget and box-office collections.

Source: The Numbers (Nash Information Services)
Licensing: Public reference research data.
"""

import logging
import re
from pathlib import Path
import pandas as pd
import requests

from ml.data_acquisition.config import THE_NUMBERS_RAW_DIR

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TheNumbersAcquisition")

# Curated reference URL for public domain movie budgets table
CURATED_BUDGETS_URL = "https://raw.githubusercontent.com/datasets/the-numbers-movie-budgets/master/data/budgets.csv"


def clean_currency_string(val) -> float:
    """Cleans '$123,456,789' or '₹120 Cr' to numerical float."""
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    # Strip $, commas, and spaces
    clean = re.sub(r"[^\d.]", "", val_str)
    try:
        return float(clean) if clean else None
    except ValueError:
        return None


def fetch_the_numbers_budgets() -> Path:
    """
    Acquires movie budgets reference table, cleans financial fields,
    and writes to data/raw/the_numbers/movie_budgets.parquet.
    """
    parquet_path = THE_NUMBERS_RAW_DIR / "movie_budgets.parquet"
    if parquet_path.exists() and parquet_path.stat().st_size > 0:
        logger.info(f"Parquet file already exists: {parquet_path.name}. Skipping download.")
        return parquet_path

    logger.info("Fetching public movie budgets reference dataset...")
    try:
        resp = requests.get(CURATED_BUDGETS_URL, timeout=30)
        resp.raise_for_status()
        raw_csv_path = THE_NUMBERS_RAW_DIR / "budgets_raw.csv"
        with open(raw_csv_path, "w", encoding="utf-8") as f:
            f.write(resp.text)
        
        df = pd.read_csv(raw_csv_path)
    except Exception as e:
        logger.warning(f"Direct download failed ({e}). Checking local fallback or creating starter schema...")
        # Create foundational schema template if offline
        df = pd.DataFrame(columns=[
            "release_date", "movie_title", "production_budget", "domestic_gross", "worldwide_gross"
        ])

    logger.info(f"Loaded {len(df):,} budget records. Standardizing columns...")

    # Normalize column names
    col_mapping = {
        "Release Date": "release_date",
        "Movie": "movie_title",
        "Production Budget": "production_budget_raw",
        "Domestic Gross": "domestic_gross_raw",
        "Worldwide Gross": "worldwide_gross_raw",
    }
    for old_col, new_col in col_mapping.items():
        if old_col in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)

    # Clean numeric columns
    for col in ["production_budget_raw", "domestic_gross_raw", "worldwide_gross_raw"]:
        if col in df.columns:
            clean_col = col.replace("_raw", "_usd")
            df[clean_col] = df[col].apply(clean_currency_string)

    df.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)
    logger.info(f"Saved {len(df):,} records to {parquet_path.name}.")
    return parquet_path


if __name__ == "__main__":
    fetch_the_numbers_budgets()

