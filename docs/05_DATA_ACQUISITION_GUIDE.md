# CineMetrics — Data Acquisition Guide

> **Document version:** 1.0  
> **Status:** Planning / Pre-implementation  
> **Last updated:** 2025  
> **Maintainer:** CineMetrics Data Team  
> **Prerequisite reading:** `docs/04_DATASET_RESEARCH.md`

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Setup](#2-environment-setup)
3. [Directory Structure](#3-directory-structure)
4. [TMDB API Setup and First Data Pull](#4-tmdb-api-setup-and-first-data-pull)
5. [IMDb Dataset Download](#5-imdb-dataset-download)
6. [Kaggle API Setup and Dataset Download](#6-kaggle-api-setup-and-dataset-download)
7. [YouTube Data API Setup](#7-youtube-data-api-setup)
8. [Google Trends Access via pytrends](#8-google-trends-access-via-pytrends)
9. [Reddit API Setup](#9-reddit-api-setup)
10. [Indian Box-Office Data Collection](#10-indian-box-office-data-collection)
11. [Data Freshness Tracking](#11-data-freshness-tracking)
12. [Storage Estimates](#12-storage-estimates)
13. [API Rate Limit Management](#13-api-rate-limit-management)
14. [Data Provenance Logging](#14-data-provenance-logging)
15. [Legal and Ethical Checklist](#15-legal-and-ethical-checklist)

---

## 1. Prerequisites

### 1.1 System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| Python | 3.11 | 3.11+ |
| RAM | 8 GB | 16 GB (IMDb dataset parsing) |
| Disk space | 10 GB free | 50 GB free |
| OS | Windows 10+ / Ubuntu 20.04+ / macOS 12+ | Any |
| Internet connection | Stable broadband | — |

### 1.2 Required API Keys / Credentials

Before beginning data acquisition, obtain the following credentials. Store all keys in `config/.env` (never committed to version control).

| Credential | Source | Required For | Cost | Priority |
|---|---|---|---|---|
| TMDB API Key | themoviedb.org | All TMDB endpoints | Free | **P0 — Required** |
| YouTube Data API Key | Google Cloud Console | Trailer stats | Free (quota) | P1 |
| Kaggle API credentials | kaggle.com/settings | Kaggle CLI downloads | Free | P1 |
| Google credentials | Google Cloud Console | pytrends (optional) | Free | P2 |
| Reddit OAuth credentials | reddit.com/prefs/apps | Reddit API | Free | P3 |

### 1.3 Python Package Dependencies

The following packages must be installed before running any acquisition scripts. The full package list belongs in `requirements.txt`:

```
# Core data handling
pandas>=2.0.0
pyarrow>=14.0.0
fastparquet>=2023.10.0

# HTTP and API clients
requests>=2.31.0
httpx>=0.25.0
tenacity>=8.2.3

# TMDB convenience (optional — alternative to raw requests)
tmdbsimple>=2.9.1

# IMDb dataset parsing
gzip  # built-in

# YouTube
google-api-python-client>=2.100.0

# Google Trends
pytrends>=4.9.2

# Reddit
praw>=7.7.1

# Kaggle CLI
kaggle>=1.5.16

# Data validation
pydantic>=2.5.0

# Fuzzy matching
rapidfuzz>=3.5.2

# Environment variable management
python-dotenv>=1.0.0

# Scheduling
apscheduler>=3.10.4

# Progress bars (development utility)
tqdm>=4.66.1

# Logging
loguru>=0.7.2

# Database (if using PostgreSQL)
sqlalchemy>=2.0.23
psycopg2-binary>=2.9.9
```

Install all dependencies:

```bash
pip install -r requirements.txt
```

---

## 2. Environment Setup

### 2.1 Project Root Setup

```bash
# Navigate to the CineMetrics project root
cd c:\Users\NAITIK\OneDrive\Desktop\CineMetrics\CineMetrics

# Create a virtual environment (recommended)
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2.2 Environment Variables File

Create `config/.env` with the following template:

```ini
# ============================================================
# CineMetrics Environment Configuration
# DO NOT COMMIT THIS FILE TO VERSION CONTROL
# Add config/.env to .gitignore
# ============================================================

# --- TMDB ---
TMDB_API_KEY=your_tmdb_api_key_here
TMDB_BASE_URL=https://api.themoviedb.org/3

# --- YouTube ---
YOUTUBE_API_KEY=your_youtube_api_key_here

# --- Reddit OAuth ---
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=CineMetrics/1.0 by u/your_reddit_username

# --- Database (if using PostgreSQL) ---
DATABASE_URL=postgresql://cinemetrics_user:password@localhost:5432/cinemetrics_db

# --- Data directories ---
DATA_RAW_DIR=data/raw
DATA_PROCESSED_DIR=data/processed
DATA_UNIFIED_DIR=data/unified
DATA_SNAPSHOTS_DIR=data/snapshots

# --- Logging ---
LOG_LEVEL=INFO
LOG_DIR=logs/
```

### 2.3 .gitignore Additions

Ensure the following are in `.gitignore`:

```
config/.env
config/*.env
*.env
data/raw/
data/snapshots/
*.parquet
*.tsv.gz
kaggle.json
```

---

## 3. Directory Structure

The following directory structure is the standard for all CineMetrics data storage. Create this structure before beginning acquisition:

```
CineMetrics/
├── data/
│   ├── raw/                          # Unprocessed data exactly as received from sources
│   │   ├── tmdb/                     # TMDB API responses
│   │   │   ├── movies/               # Individual movie JSON files
│   │   │   ├── upcoming/             # Upcoming movies list responses
│   │   │   ├── discover/             # Discover endpoint responses
│   │   │   ├── persons/              # Person detail JSON files
│   │   │   └── metadata.json         # Last fetch timestamps per endpoint
│   │   │
│   │   ├── imdb/                     # IMDb bulk dataset files
│   │   │   ├── title.basics.tsv.gz
│   │   │   ├── title.ratings.tsv.gz
│   │   │   ├── title.crew.tsv.gz
│   │   │   ├── title.principals.tsv.gz
│   │   │   ├── name.basics.tsv.gz
│   │   │   ├── title.akas.tsv.gz
│   │   │   └── download_manifest.json  # Download dates and checksums
│   │   │
│   │   ├── kaggle/                   # Kaggle dataset downloads
│   │   │   ├── tmdb-5000/            # TMDB 5000 Movie Dataset
│   │   │   ├── the-movies-dataset/   # GroupLens / rounakbanik dataset
│   │   │   ├── movie-budgets/        # The Numbers budget dataset
│   │   │   ├── imdb-extensive/       # Stefano Leone IMDb dataset
│   │   │   ├── bollywood/            # Bollywood-specific datasets
│   │   │   └── download_manifest.json
│   │   │
│   │   ├── the_numbers/              # Manually downloaded or Kaggle-sourced
│   │   │   └── movie_budgets.csv
│   │   │
│   │   ├── youtube/                  # YouTube Data API responses
│   │   │   ├── trailer_stats/        # JSON files per video ID, per snapshot date
│   │   │   └── metadata.json
│   │   │
│   │   ├── google_trends/            # pytrends response CSVs
│   │   │   └── snapshots/            # Dated trend snapshots per movie
│   │   │
│   │   ├── reddit/                   # Reddit API responses
│   │   │   └── posts/                # Subreddit post snapshots
│   │   │
│   │   └── indian_sources/           # Manually entered Indian box-office data
│   │       ├── sacnilk_manual.csv    # Hand-transcribed Sacnilk data
│   │       ├── bollywood_hungama_manual.csv
│   │       └── koimoi_manual.csv
│   │
│   ├── processed/                    # Cleaned, normalized, typed data (Parquet)
│   │   ├── tmdb_movies.parquet
│   │   ├── tmdb_persons.parquet
│   │   ├── imdb_basics.parquet
│   │   ├── imdb_ratings.parquet
│   │   ├── imdb_crew.parquet
│   │   ├── imdb_principals.parquet
│   │   ├── imdb_names.parquet
│   │   ├── imdb_akas.parquet
│   │   ├── kaggle_tmdb5000.parquet
│   │   ├── kaggle_movies_dataset.parquet
│   │   ├── kaggle_movie_budgets.parquet
│   │   ├── youtube_trailer_stats.parquet
│   │   ├── google_trends.parquet
│   │   └── reddit_posts.parquet
│   │
│   ├── unified/                      # Cross-source merged canonical dataset
│   │   ├── movies.parquet            # Canonical movie table
│   │   ├── movie_financials.parquet  # All financial data, with source tags
│   │   ├── persons.parquet           # Canonical person table
│   │   ├── movie_cast.parquet        # Movie-person relationships
│   │   └── feature_matrix.parquet    # ML-ready feature matrix
│   │
│   └── snapshots/                    # Timestamped feature snapshots (leakage prevention)
│       ├── feature_snapshots/        # Named by movie_id + snapshot_date
│       └── popularity_readings/      # Daily TMDB popularity readings
│
├── config/
│   ├── .env                          # API keys (not committed)
│   ├── .env.example                  # Template (committed — no real keys)
│   └── data_sources.yaml             # Source registry and configuration
│
├── logs/
│   ├── acquisition/                  # Acquisition job logs
│   ├── pipeline/                     # ETL pipeline logs
│   └── errors/                       # Error-specific logs
│
└── src/
    └── acquisition/                  # Data acquisition scripts
        ├── tmdb_client.py
        ├── imdb_downloader.py
        ├── kaggle_downloader.py
        ├── youtube_client.py
        ├── trends_client.py
        └── provenance_logger.py
```

**Create the directory structure:**

```bash
# Windows (PowerShell)
$dirs = @(
    "data/raw/tmdb/movies", "data/raw/tmdb/upcoming", "data/raw/tmdb/discover",
    "data/raw/tmdb/persons", "data/raw/imdb", "data/raw/kaggle/tmdb-5000",
    "data/raw/kaggle/the-movies-dataset", "data/raw/kaggle/movie-budgets",
    "data/raw/kaggle/imdb-extensive", "data/raw/kaggle/bollywood",
    "data/raw/the_numbers", "data/raw/youtube/trailer_stats",
    "data/raw/google_trends/snapshots", "data/raw/reddit/posts",
    "data/raw/indian_sources", "data/processed", "data/unified",
    "data/snapshots/feature_snapshots", "data/snapshots/popularity_readings",
    "config", "logs/acquisition", "logs/pipeline", "logs/errors",
    "src/acquisition"
)
foreach ($dir in $dirs) { New-Item -ItemType Directory -Force -Path $dir }
```

```bash
# macOS / Linux
mkdir -p data/raw/{tmdb/{movies,upcoming,discover,persons},imdb,kaggle/{tmdb-5000,the-movies-dataset,movie-budgets,imdb-extensive,bollywood},the_numbers,youtube/trailer_stats,google_trends/snapshots,reddit/posts,indian_sources}
mkdir -p data/{processed,unified,snapshots/{feature_snapshots,popularity_readings}}
mkdir -p config logs/{acquisition,pipeline,errors} src/acquisition
```

---

## 4. TMDB API Setup and First Data Pull

### 4.1 Account Creation and API Key

1. Go to [https://www.themoviedb.org/signup](https://www.themoviedb.org/signup)
2. Register with email; verify email address
3. Log in → click your avatar → **Settings** → **API** (left sidebar)
4. Click **Create** → choose **Developer**
5. Fill in:
   - Application name: `CineMetrics`
   - Application URL: `http://localhost` (for development)
   - Application summary: "Academic project for movie revenue prediction using machine learning. Non-commercial use."
6. After submission, your **API Key (v3 auth)** appears immediately
7. Copy the key to `config/.env` as `TMDB_API_KEY`

### 4.2 Test the API Key

```python
# src/acquisition/tmdb_client.py — Test connection (pseudocode style)
import os
import requests
from dotenv import load_dotenv

load_dotenv("config/.env")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def test_connection():
    """Verify TMDB API key is working."""
    url = f"{BASE_URL}/configuration"
    params = {"api_key": TMDB_API_KEY}
    
    response = requests.get(url, params=params)
    response.raise_for_status()   # raises HTTPError if status != 200
    
    config = response.json()
    print(f"TMDB connection OK. Base image URL: {config['images']['base_url']}")
    return config

if __name__ == "__main__":
    test_connection()
```

Expected output: `TMDB connection OK. Base image URL: https://image.tmdb.org/t/p/`

### 4.3 Fetching a Single Movie (Example)

```python
def fetch_movie_detail(movie_id: int) -> dict:
    """
    Fetch full movie detail from TMDB including credits, videos, keywords.
    Uses append_to_response to reduce API calls.
    
    Parameters:
        movie_id: TMDB integer movie ID
    
    Returns:
        dict: Combined movie detail + credits + videos + keywords
    """
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "append_to_response": "credits,videos,keywords,release_dates,external_ids",
        "language": "en-US"
    }
    
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 404:
        # Movie not found — log and return None
        log.warning(f"Movie {movie_id} not found on TMDB (404)")
        return None
    
    response.raise_for_status()
    
    data = response.json()
    
    # Save raw response to disk
    output_path = f"data/raw/tmdb/movies/{movie_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        import json
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data
```

### 4.4 Fetching All Movies by Language (Discover Endpoint)

```python
def discover_movies_by_language(
    language_code: str,
    start_year: int,
    end_year: int,
    output_dir: str = "data/raw/tmdb/discover"
) -> list[dict]:
    """
    Retrieve all movies of a given original language between start_year and end_year.
    Handles TMDB's 500-page (10,000 result) limit by splitting into annual chunks.
    
    Parameters:
        language_code: ISO 639-1 code (e.g., "hi", "te", "ta", "ml", "kn", "en")
        start_year: Inclusive start year
        end_year: Inclusive end year
        output_dir: Directory to save paginated responses
    
    Returns:
        List of all movie dicts retrieved
    """
    all_movies = []
    
    for year in range(start_year, end_year + 1):
        page = 1
        while True:
            params = {
                "api_key": TMDB_API_KEY,
                "with_original_language": language_code,
                "primary_release_date.gte": f"{year}-01-01",
                "primary_release_date.lte": f"{year}-12-31",
                "sort_by": "popularity.desc",
                "page": page
            }
            
            response = requests.get(
                f"{BASE_URL}/discover/movie",
                params=params,
                timeout=10
            )
            
            if response.status_code == 429:
                # Rate limited — wait and retry
                retry_after = int(response.headers.get("Retry-After", 10))
                time.sleep(retry_after + 1)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            all_movies.extend(data["results"])
            
            if page >= data["total_pages"] or page >= 500:
                break
            
            page += 1
            time.sleep(0.4)  # ~25 requests per 10 seconds to stay under rate limit
    
    return all_movies
```

### 4.5 Daily Upcoming Movies Snapshot

```python
def fetch_upcoming_movies(region: str = "IN") -> list[dict]:
    """
    Fetch movies with upcoming release dates in the specified region.
    Should be run daily to track the prediction pipeline's target queue.
    
    Parameters:
        region: ISO 3166-1 country code
    
    Returns:
        List of upcoming movie dicts
    """
    all_upcoming = []
    page = 1
    
    while True:
        params = {
            "api_key": TMDB_API_KEY,
            "region": region,
            "language": "en-US",
            "page": page
        }
        
        response = requests.get(
            f"{BASE_URL}/movie/upcoming",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        all_upcoming.extend(data["results"])
        
        if page >= data["total_pages"]:
            break
        page += 1
        time.sleep(0.4)
    
    # Log provenance
    log_provenance(
        source="tmdb",
        endpoint="/movie/upcoming",
        params={"region": region},
        record_count=len(all_upcoming),
        output_path=f"data/raw/tmdb/upcoming/upcoming_{region}_{date.today()}.json"
    )
    
    return all_upcoming
```

---

## 5. IMDb Dataset Download

### 5.1 Download Commands

IMDb datasets are available as gzip-compressed TSV files. No authentication required.

```bash
# Windows (PowerShell) — requires curl (available in Windows 10+)
$imdb_base = "https://datasets.imdbws.com"
$output_dir = "data\raw\imdb"

$files = @(
    "title.basics.tsv.gz",
    "title.ratings.tsv.gz",
    "title.crew.tsv.gz",
    "title.principals.tsv.gz",
    "name.basics.tsv.gz",
    "title.akas.tsv.gz"
)

foreach ($file in $files) {
    Write-Host "Downloading $file..."
    curl -L "$imdb_base/$file" -o "$output_dir\$file"
}
Write-Host "IMDb downloads complete."
```

```bash
# macOS / Linux (bash)
IMDB_BASE="https://datasets.imdbws.com"
OUTPUT_DIR="data/raw/imdb"

for FILE in title.basics.tsv.gz title.ratings.tsv.gz title.crew.tsv.gz \
            title.principals.tsv.gz name.basics.tsv.gz title.akas.tsv.gz; do
    echo "Downloading $FILE..."
    wget -P "$OUTPUT_DIR" "$IMDB_BASE/$FILE"
done
echo "IMDb downloads complete."
```

### 5.2 Verify Downloads

```python
# Verify IMDb files are intact and log checksums for provenance
import hashlib
import os
import json
from datetime import date

def verify_and_log_imdb_downloads(imdb_dir: str = "data/raw/imdb"):
    """Compute MD5 checksums and log download metadata."""
    manifest = {
        "download_date": str(date.today()),
        "files": {}
    }
    
    expected_files = [
        "title.basics.tsv.gz",
        "title.ratings.tsv.gz",
        "title.crew.tsv.gz",
        "title.principals.tsv.gz",
        "name.basics.tsv.gz",
        "title.akas.tsv.gz"
    ]
    
    for filename in expected_files:
        filepath = os.path.join(imdb_dir, filename)
        if not os.path.exists(filepath):
            print(f"MISSING: {filename}")
            manifest["files"][filename] = {"status": "missing"}
            continue
        
        file_size = os.path.getsize(filepath)
        
        # MD5 checksum
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        
        manifest["files"][filename] = {
            "status": "ok",
            "size_bytes": file_size,
            "md5": hasher.hexdigest()
        }
        print(f"OK: {filename} ({file_size / 1e6:.1f} MB)")
    
    # Save manifest
    with open(os.path.join(imdb_dir, "download_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    
    return manifest
```

### 5.3 Loading IMDb Data with Pandas

```python
import pandas as pd
import gzip

def load_imdb_basics(filepath: str = "data/raw/imdb/title.basics.tsv.gz") -> pd.DataFrame:
    """
    Load IMDb title.basics dataset, filtered to movies only.
    
    Returns:
        DataFrame with movie records only. '\N' replaced with None.
    """
    df = pd.read_csv(
        filepath,
        sep="\t",
        compression="gzip",
        na_values=["\\N"],    # IMDb uses \N for null
        low_memory=False,
        dtype={
            "tconst": str,
            "titleType": str,
            "primaryTitle": str,
            "originalTitle": str,
            "isAdult": str,
            "startYear": str,   # Read as string; convert after filtering
            "endYear": str,
            "runtimeMinutes": str,
            "genres": str
        }
    )
    
    # Filter to movies only
    df = df[df["titleType"] == "movie"].copy()
    
    # Type conversions
    df["startYear"] = pd.to_numeric(df["startYear"], errors="coerce")
    df["runtimeMinutes"] = pd.to_numeric(df["runtimeMinutes"], errors="coerce")
    df["isAdult"] = df["isAdult"].map({"0": False, "1": True})
    
    # Save processed version
    df.to_parquet("data/processed/imdb_basics.parquet", index=False)
    
    print(f"IMDb basics loaded: {len(df):,} movies")
    return df
```

---

## 6. Kaggle API Setup and Dataset Download

### 6.1 Kaggle Account and API Credentials

1. Create an account at [https://www.kaggle.com/](https://www.kaggle.com/)
2. Navigate to **Account Settings** → scroll to **API** section
3. Click **Create New Token** — downloads `kaggle.json`
4. Place `kaggle.json` at:
   - **Windows:** `C:\Users\<username>\.kaggle\kaggle.json`
   - **macOS/Linux:** `~/.kaggle/kaggle.json`
5. Restrict file permissions (Linux/Mac): `chmod 600 ~/.kaggle/kaggle.json`

The `kaggle.json` file contains:
```json
{
  "username": "your_kaggle_username",
  "key": "your_api_key_here"
}
```

> [!CAUTION]
> Never commit `kaggle.json` to version control. Add `kaggle.json` and `~/.kaggle/` to `.gitignore`.

### 6.2 Install Kaggle CLI

```bash
pip install kaggle
```

Verify installation:
```bash
kaggle --version
# Expected: Kaggle API 1.x.x
```

### 6.3 Download Recommended Datasets

```bash
# TMDB 5000 Movie Dataset
kaggle datasets download tmdb/tmdb-movie-metadata \
    --path data/raw/kaggle/tmdb-5000 \
    --unzip

# The Movies Dataset (rounakbanik)
# REQUIRES VERIFICATION: search Kaggle for exact slug
kaggle datasets download rounakbanik/the-movies-dataset \
    --path data/raw/kaggle/the-movies-dataset \
    --unzip

# IMDb Movies Extensive Dataset (Stefano Leone)
# REQUIRES VERIFICATION: search Kaggle for exact slug
kaggle datasets download stefanoleone992/imdb-extensive-dataset \
    --path data/raw/kaggle/imdb-extensive \
    --unzip

# Movie budgets (from The Numbers) — search Kaggle for current best version
# REQUIRES VERIFICATION: search Kaggle for "movie budgets the-numbers"
kaggle datasets download <uploader>/<dataset-slug> \
    --path data/raw/kaggle/movie-budgets \
    --unzip
```

> [!NOTE]
> Dataset slugs marked as REQUIRES VERIFICATION. Run `kaggle datasets search "movie budget"` to find current available datasets and their exact slugs.

### 6.4 Kaggle Dataset Search via CLI

```bash
# Search for Bollywood datasets
kaggle datasets search "bollywood movies" --sort-by hotness

# Search for Indian movies
kaggle datasets search "Indian movies dataset" --sort-by usability

# List files in a downloaded dataset
kaggle datasets files tmdb/tmdb-movie-metadata
```

### 6.5 Log Kaggle Downloads

```python
def log_kaggle_download(dataset_slug: str, output_dir: str):
    """Record Kaggle dataset download metadata for provenance."""
    import subprocess
    import json
    from datetime import datetime
    
    # Get dataset info via CLI
    result = subprocess.run(
        ["kaggle", "datasets", "metadata", dataset_slug, "-p", output_dir],
        capture_output=True, text=True
    )
    
    manifest_entry = {
        "dataset_slug": dataset_slug,
        "download_timestamp": datetime.utcnow().isoformat() + "Z",
        "output_dir": output_dir,
        "kaggle_metadata_fetched": result.returncode == 0
    }
    
    # Append to master download manifest
    manifest_path = "data/raw/kaggle/download_manifest.json"
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except FileNotFoundError:
        manifest = {"downloads": []}
    
    manifest["downloads"].append(manifest_entry)
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
```

---

## 7. YouTube Data API Setup

### 7.1 Google Cloud Project and API Enable

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
   - Project name: `CineMetrics`
   - Click **Create**
3. Navigate to **APIs & Services → Library**
4. Search for **YouTube Data API v3**
5. Click **Enable**
6. Navigate to **APIs & Services → Credentials**
7. Click **Create Credentials → API Key**
8. Copy the API key
9. Click **Edit API key** → under **API restrictions**, select **Restrict key** → choose **YouTube Data API v3**
10. Store in `config/.env` as `YOUTUBE_API_KEY`

### 7.2 Test YouTube API

```python
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv("config/.env")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def build_youtube_client():
    """Build authenticated YouTube Data API v3 client."""
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def test_youtube_connection():
    """Test YouTube API connectivity."""
    youtube = build_youtube_client()
    request = youtube.videos().list(
        part="snippet,statistics",
        id="dQw4w9WgXcQ"  # well-known test video
    )
    response = request.execute()
    video = response["items"][0]
    print(f"YouTube API OK. Test video title: {video['snippet']['title']}")
    return True

if __name__ == "__main__":
    test_youtube_connection()
```

### 7.3 Fetching Trailer Statistics

```python
def fetch_trailer_stats(youtube_video_id: str, movie_id: str) -> dict:
    """
    Fetch current statistics for a YouTube trailer video.
    Records are timestamped because counts change over time.
    
    Parameters:
        youtube_video_id: YouTube video key (from TMDB /movie/{id}/videos)
        movie_id: CineMetrics internal movie ID (for provenance)
    
    Returns:
        dict: Statistics snapshot with timestamp
    """
    from datetime import datetime
    
    youtube = build_youtube_client()
    
    request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=youtube_video_id
    )
    response = request.execute()
    
    if not response["items"]:
        return {"error": "video_not_found", "video_id": youtube_video_id}
    
    item = response["items"][0]
    stats = item.get("statistics", {})
    
    snapshot = {
        "movie_id": movie_id,
        "youtube_video_id": youtube_video_id,
        "snapshot_timestamp": datetime.utcnow().isoformat() + "Z",
        "published_at": item["snippet"]["publishedAt"],
        "title": item["snippet"]["title"],
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)) if "likeCount" in stats else None,
        "comment_count": int(stats.get("commentCount", 0)) if "commentCount" in stats else None,
        "duration_iso": item["contentDetails"]["duration"]
    }
    
    # Save snapshot
    output_dir = f"data/raw/youtube/trailer_stats"
    snapshot_date = datetime.utcnow().strftime("%Y%m%d")
    output_path = f"{output_dir}/{youtube_video_id}_{snapshot_date}.json"
    
    import json
    with open(output_path, "w") as f:
        json.dump(snapshot, f, indent=2)
    
    return snapshot
```

---

## 8. Google Trends Access via pytrends

### 8.1 Install pytrends

```bash
pip install pytrends
```

### 8.2 Fetch Search Interest for a Movie

```python
from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta

def fetch_movie_search_trends(
    movie_title: str,
    movie_id: str,
    release_date: str,
    geo: str = "IN",
    weeks_before_release: int = 12
) -> pd.DataFrame:
    """
    Fetch Google Trends search interest for a movie title in the
    period leading up to its release date.
    
    Parameters:
        movie_title: Movie title to search for
        movie_id: CineMetrics internal movie ID
        release_date: YYYY-MM-DD release date
        geo: ISO 3166-1 country code (e.g., 'IN', 'US', '' for global)
        weeks_before_release: How far back to look
    
    Returns:
        DataFrame with weekly relative interest (0-100)
    
    Notes:
        - pytrends uses an unofficial interface; may be rate-limited.
        - Wait 60 seconds between requests to avoid being blocked.
        - Returns relative scores (0-100), not absolute search volumes.
    """
    pytrends = TrendReq(
        hl="en-US",
        tz=330 if geo == "IN" else 0,  # IST offset for India
        retries=3,
        backoff_factor=0.5
    )
    
    release_dt = datetime.strptime(release_date, "%Y-%m-%d")
    start_dt = release_dt - timedelta(weeks=weeks_before_release)
    
    timeframe = f"{start_dt.strftime('%Y-%m-%d')} {release_dt.strftime('%Y-%m-%d')}"
    
    pytrends.build_payload(
        kw_list=[movie_title],
        cat=0,
        timeframe=timeframe,
        geo=geo,
        gprop=""
    )
    
    interest_df = pytrends.interest_over_time()
    
    if interest_df.empty:
        print(f"No trends data for '{movie_title}' in {geo}")
        return pd.DataFrame()
    
    interest_df = interest_df.drop(columns=["isPartial"], errors="ignore")
    interest_df["movie_id"] = movie_id
    interest_df["query_term"] = movie_title
    interest_df["geo"] = geo
    
    # Save snapshot
    output_path = f"data/raw/google_trends/snapshots/{movie_id}_{geo}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    interest_df.to_csv(output_path)
    
    return interest_df
```

> [!WARNING]
> `pytrends` is an unofficial library using Google Trends' web interface. It can be blocked without notice. Implement aggressive retry logic and respect rate limits (minimum 30–60 seconds between requests). Do not run more than ~50 queries per day without testing for blocks.

---

## 9. Reddit API Setup

### 9.1 Create Reddit App

1. Log into Reddit at [https://www.reddit.com/](https://www.reddit.com/)
2. Navigate to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
3. Click **Create Another App** at the bottom
4. Fill in:
   - **Name:** CineMetrics
   - **Type:** Select **script** (for personal use / local scripts)
   - **Redirect URI:** `http://localhost:8080` (not used for script type)
5. Click **Create App**
6. Note your **Client ID** (under the app name) and **Client Secret**
7. Add to `config/.env`:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT` → `"CineMetrics/1.0 by u/your_reddit_username"`

### 9.2 Fetch Subreddit Posts

```python
import praw
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv("config/.env")

def build_reddit_client() -> praw.Reddit:
    """Build authenticated Reddit client."""
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT")
    )

def fetch_movie_mentions(
    movie_title: str,
    movie_id: str,
    subreddits: list[str] = ["bollywood", "tollywood", "movies", "boxoffice"],
    post_limit: int = 50
) -> list[dict]:
    """
    Search for posts mentioning a movie title across relevant subreddits.
    
    Parameters:
        movie_title: Movie title to search for
        movie_id: CineMetrics internal movie ID
        subreddits: List of subreddit names to search
        post_limit: Maximum posts per subreddit
    
    Returns:
        List of post dicts with engagement metadata
    """
    reddit = build_reddit_client()
    posts = []
    
    for sub_name in subreddits:
        subreddit = reddit.subreddit(sub_name)
        
        for submission in subreddit.search(
            query=movie_title,
            sort="new",
            limit=post_limit
        ):
            posts.append({
                "movie_id": movie_id,
                "subreddit": sub_name,
                "post_id": submission.id,
                "title": submission.title,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "upvote_ratio": submission.upvote_ratio,
                "created_utc": datetime.utcfromtimestamp(submission.created_utc).isoformat() + "Z",
                "fetch_timestamp": datetime.utcnow().isoformat() + "Z"
            })
    
    return posts
```

> [!NOTE]
> Reddit API changes in 2023 significantly restrict bulk historical access. This implementation works for recent posts only. Historical data before the project launch is not accessible through the standard free tier.

---

## 10. Indian Box-Office Data Collection

Since no official API exists for Indian box-office data, CineMetrics uses a **manual data entry** workflow for major Indian releases.

### 10.1 Manual Entry Template

Create and maintain `data/raw/indian_sources/sacnilk_manual.csv` with the following schema:

```csv
movie_id,tmdb_id,imdb_id,movie_title,language,release_date,
collection_day,nett_collection_inr_cr,source_name,source_url,
entry_date,entered_by,confidence,notes
```

| Column | Description |
|---|---|
| `movie_id` | CineMetrics internal UUID |
| `tmdb_id` | TMDB movie ID for cross-reference |
| `movie_title` | Exact title as on source website |
| `language` | `hindi`, `telugu`, `tamil`, `malayalam`, `kannada` |
| `release_date` | YYYY-MM-DD |
| `collection_day` | Integer (Day 1 = release day, Day 2 = next day, etc.) |
| `nett_collection_inr_cr` | Nett collection in Indian Rupees (crore) |
| `source_name` | `sacnilk`, `bollywood_hungama`, `koimoi`, `box_office_india` |
| `source_url` | Exact URL of the page from which data was read |
| `entry_date` | YYYY-MM-DD when data was entered |
| `entered_by` | Username/name of person who entered the data |
| `confidence` | `high`, `medium`, `low` |
| `notes` | Any discrepancies vs. other sources |

### 10.2 Currency Conversion

Indian collections are reported in **INR crore** (1 crore = 10 million). Convert to USD for unified financial table:

```python
def inr_crore_to_usd(
    inr_crore: float,
    exchange_rate_inr_per_usd: float
) -> float:
    """
    Convert INR crore to USD.
    
    Parameters:
        inr_crore: Amount in Indian Rupees (crore)
        exchange_rate_inr_per_usd: Exchange rate at time of collection
    
    Returns:
        float: Amount in USD
    
    Example:
        inr_crore_to_usd(100.0, 83.5) → 11_976_047.9...
        (₹100 crore / ₹83.5 per dollar = ~$11.98 million USD)
    """
    inr_amount = inr_crore * 1e7  # 1 crore = 10,000,000
    usd_amount = inr_amount / exchange_rate_inr_per_usd
    return usd_amount
```

---

## 11. Data Freshness Tracking

### 11.1 Freshness Policy

| Data Source | Update Frequency | Stale After | Action If Stale |
|---|---|---|---|
| TMDB upcoming movies | Daily | 24 hours | Re-fetch `/movie/upcoming` |
| TMDB movie detail (released) | Weekly | 7 days | Re-fetch with append_to_response |
| TMDB movie detail (unreleased) | Daily | 24 hours | Re-fetch to catch status changes |
| TMDB popularity | Daily | 24 hours | Record popularity snapshot |
| IMDb bulk datasets | Weekly | 7 days | Re-download all .tsv.gz files |
| IMDb ratings | Weekly | 7 days | Re-download title.ratings.tsv.gz |
| YouTube trailer stats | Weekly (pre-release), Daily (1 week before release) | Defined above | Re-fetch video statistics |
| Google Trends | Weekly | 7 days | Re-fetch with 90-day window |
| Reddit posts | Daily (tracked movies) | 24 hours | Search + append new posts |
| Indian sources | Manual | N/A | Enter data as it becomes available |

### 11.2 Freshness Metadata File

Each data source directory contains a `metadata.json` file:

```json
{
  "source": "tmdb",
  "last_full_fetch": "2025-01-15T00:00:00Z",
  "last_incremental_fetch": "2025-01-20T06:00:00Z",
  "total_records": 48234,
  "movies_tracked": 342,
  "fetch_frequency_hours": 24,
  "next_scheduled_fetch": "2025-01-21T06:00:00Z",
  "schema_version": "1.0",
  "notes": "Full re-fetch for Indian language movies (hi, te, ta, ml, kn) 2000-2025"
}
```

### 11.3 Freshness Check Function

```python
from datetime import datetime, timezone
import json

def is_data_stale(source_name: str, stale_after_hours: int) -> bool:
    """
    Check if a data source's last fetch is older than the threshold.
    
    Parameters:
        source_name: One of: tmdb, imdb, kaggle, youtube, reddit
        stale_after_hours: Number of hours before data is considered stale
    
    Returns:
        bool: True if data should be refreshed
    """
    metadata_path = f"data/raw/{source_name}/metadata.json"
    
    try:
        with open(metadata_path) as f:
            metadata = json.load(f)
    except FileNotFoundError:
        return True  # Never fetched — always stale
    
    last_fetch_str = metadata.get("last_incremental_fetch") or metadata.get("last_full_fetch")
    
    if not last_fetch_str:
        return True
    
    last_fetch = datetime.fromisoformat(last_fetch_str.replace("Z", "+00:00"))
    age_hours = (datetime.now(timezone.utc) - last_fetch).total_seconds() / 3600
    
    return age_hours > stale_after_hours
```

---

## 12. Storage Estimates

| Data Source | Raw Size | Processed (Parquet) | Notes |
|---|---|---|---|
| IMDb all files (compressed) | ~1.0 GB | ~1.5 GB | Parquet slightly larger than gzip for columnar |
| IMDb all files (uncompressed) | ~3.7 GB | — | — |
| TMDB movies (50k movies, JSON) | ~2 GB | ~400 MB | JSON → Parquet compression significant |
| Kaggle datasets (all) | ~500 MB | ~200 MB | — |
| YouTube stats (snapshots) | ~50 MB/year | ~20 MB/year | Grows with tracked movies |
| Google Trends snapshots | ~10 MB/year | ~5 MB/year | Small weekly files |
| Reddit posts | ~100 MB/year | ~50 MB/year | Depends on monitoring scope |
| Indian sources (manual) | ~1 MB | ~1 MB | Small CSV files |
| **Total (Year 1)** | **~7.5 GB** | **~2.5 GB** | — |

> [!TIP]
> Store raw data in its original format (compressed where available). Use Parquet for all processed data — it typically achieves 70–90% size reduction compared to CSV while enabling fast columnar queries.

---

## 13. API Rate Limit Management

### 13.1 Rate Limit Summary

| API | Limit | Strategy |
|---|---|---|
| TMDB | ~40 req/10 sec | Sleep 0.4s between requests; exponential backoff on 429 |
| YouTube | 10,000 units/day | Use `videos.list` (1 unit/call) over `search.list` (100 units/call) |
| Google Trends | Unofficial; ~1–2 req/min | 60-second sleep between queries; run overnight |
| Reddit | 100 req/min (OAuth) | Throttle to 60 req/min; praw handles most rate limiting |
| IMDb | No API limit | Download once; re-use |
| Kaggle | 500 req/day (ESTIMATED) | Download datasets once; re-use |

### 13.2 Retry Strategy with Tenacity

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((requests.exceptions.HTTPError, 
                                    requests.exceptions.ConnectionError,
                                    requests.exceptions.Timeout)),
    reraise=True
)
def tmdb_get(endpoint: str, params: dict) -> dict:
    """
    Make a TMDB API GET request with automatic retry on transient failures.
    
    - Retries up to 5 times
    - Wait starts at 2s, doubles each attempt, capped at 60s
    - Reraises on final failure
    """
    base_url = "https://api.themoviedb.org/3"
    params["api_key"] = os.getenv("TMDB_API_KEY")
    
    response = requests.get(f"{base_url}{endpoint}", params=params, timeout=15)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 10))
        time.sleep(retry_after + 1)
        response.raise_for_status()  # Trigger retry
    
    response.raise_for_status()
    return response.json()
```

### 13.3 Acquisition Job Throttle Configuration

Define per-source throttle settings in `config/data_sources.yaml`:

```yaml
sources:
  tmdb:
    requests_per_10_seconds: 25
    sleep_between_requests_ms: 400
    max_retries: 5
    timeout_seconds: 15
  youtube:
    daily_quota_units: 10000
    units_per_search: 100
    units_per_videos_list: 1
    max_videos_per_batch: 50
  google_trends:
    sleep_between_requests_seconds: 60
    max_queries_per_day: 50
  reddit:
    requests_per_minute: 60
    praw_handles_throttle: true
```

---

## 14. Data Provenance Logging

Every data point in CineMetrics must have a traceable provenance record. This is both a data quality measure and a legal compliance measure.

### 14.1 Provenance Log Format

```python
from dataclasses import dataclass
from datetime import datetime
import json
import uuid

@dataclass
class ProvenanceRecord:
    """
    A provenance record documents the origin of every data retrieval event.
    One record per API call or file download.
    """
    provenance_id: str           # UUID
    source_name: str             # e.g., "tmdb", "imdb", "kaggle_tmdb5000"
    source_type: str             # "api", "bulk_download", "manual_entry"
    endpoint_or_url: str         # Full URL or endpoint path used
    parameters: dict             # Query parameters or identifiers
    retrieval_timestamp: str     # ISO 8601 UTC
    record_count: int            # Number of records retrieved
    schema_version: str          # Version of the source schema we parsed
    output_path: str             # Where the raw data was saved
    license: str                 # Data license (e.g., "CC0", "imdb-noncommercial")
    notes: str                   # Any anomalies observed

def log_provenance(
    source_name: str,
    endpoint: str,
    params: dict,
    record_count: int,
    output_path: str,
    source_type: str = "api",
    schema_version: str = "1.0",
    license_str: str = "unknown",
    notes: str = ""
) -> ProvenanceRecord:
    """Log a data acquisition event to the provenance log file."""
    
    record = ProvenanceRecord(
        provenance_id=str(uuid.uuid4()),
        source_name=source_name,
        source_type=source_type,
        endpoint_or_url=endpoint,
        parameters=params,
        retrieval_timestamp=datetime.utcnow().isoformat() + "Z",
        record_count=record_count,
        schema_version=schema_version,
        output_path=output_path,
        license=license_str,
        notes=notes
    )
    
    # Append to JSONL log file
    log_path = f"logs/acquisition/provenance_{datetime.utcnow().strftime('%Y%m')}.jsonl"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record.__dict__) + "\n")
    
    return record
```

### 14.2 Provenance Log Example Entry

```json
{
  "provenance_id": "f7a2b3c4-1234-5678-abcd-ef0123456789",
  "source_name": "tmdb",
  "source_type": "api",
  "endpoint_or_url": "https://api.themoviedb.org/3/movie/1096197",
  "parameters": {"append_to_response": "credits,videos,keywords,release_dates,external_ids"},
  "retrieval_timestamp": "2025-01-20T06:30:00Z",
  "record_count": 1,
  "schema_version": "1.0",
  "output_path": "data/raw/tmdb/movies/1096197.json",
  "license": "tmdb-noncommercial",
  "notes": "Movie ID: Jawan (2023). Budget field = 0 (not provided by TMDB)."
}
```

---

## 15. Legal and Ethical Checklist

Before executing any data acquisition, verify the following checklist. Document the outcome of each check in `config/data_acquisition_compliance.md`.

### Pre-Acquisition Legal Checklist

| Item | Requirement | Verified? |
|---|---|---|
| **TMDB ToS** | Non-commercial use; must attribute TMDB | ☐ |
| **TMDB Attribution** | Display "This product uses the TMDB API but is not endorsed or certified by TMDB" in UI | ☐ |
| **IMDb ToS** | Non-commercial personal use only; no redistribution | ☐ |
| **IMDb Data Policy** | Cannot include raw IMDb data in public GitHub repos or public datasets | ☐ |
| **Kaggle licenses** | Verify each downloaded dataset's license before use | ☐ |
| **YouTube ToS** | Only use YouTube Data API for authorized purposes; no bulk downloading of videos | ☐ |
| **Google Trends** | pytrends is unofficial; Google ToS technically prohibits automated scraping | ☐ |
| **Reddit ToS** | Comply with Reddit Developer Terms; no bulk historical scraping | ☐ |
| **The Numbers** | Do not scrape; use only Kaggle-sourced extracts | ☐ |
| **Box Office Mojo** | Do not scrape; reference only | ☐ |
| **Sacnilk / Indian sources** | Manual reference use only; no automated scraping | ☐ |

### Data Ethics Checklist

| Item | Requirement | Verified? |
|---|---|---|
| **No personal data** | No collection of personally identifiable information about users | ☐ |
| **Person data scope** | Only public professional information about film industry professionals (name, filmography) | ☐ |
| **No tracking** | No tracking of individual Reddit/YouTube/Google users | ☐ |
| **Aggregation only** | Social media signals used in aggregate only; no individual profiling | ☐ |
| **Source disclosure** | All data sources disclosed in product documentation and UI | ☐ |
| **Financial data accuracy disclaimer** | Predictions labeled with confidence intervals; not financial advice | ☐ |
| **No deceptive scraping** | User-Agent headers accurately identify CineMetrics; no spoofing | ☐ |

### Storage Security Checklist

| Item | Requirement | Verified? |
|---|---|---|
| **API keys secured** | All keys in `.env`; not committed to Git | ☐ |
| **IMDb data not redistributed** | Raw IMDb files not in public repository | ☐ |
| **Kaggle data not redistributed** | Check each dataset license before including in repo | ☐ |
| **Gitignore configured** | `data/raw/`, `*.tsv.gz`, `*.parquet`, `config/.env` in `.gitignore` | ☐ |
| **Backup plan** | At least one local copy of downloaded datasets; re-download scripts available | ☐ |

---

*This document is a planning reference. Update it as acquisition pipelines are implemented and new data sources are added. See `docs/07_DATA_ENGINEERING_PIPELINE.md` for the processing steps that follow acquisition.*
