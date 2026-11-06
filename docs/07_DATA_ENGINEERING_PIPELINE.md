# CineMetrics — Data Engineering Pipeline Specification

**Document ID:** 07  
**Version:** 1.0  
**Status:** Approved Engineering Specification  
**Last Updated:** 2026-11  
**Related Docs:** [Unified Dataset Design](06_UNIFIED_DATASET_DESIGN.md) | [Historical Snapshot Strategy](08_HISTORICAL_SNAPSHOT_STRATEGY.md) | [Data Ingestion](14_AUTOMATED_DATA_INGESTION.md) | [Data Pipeline Diagram](../diagrams/data_pipeline.mmd)

---

## Table of Contents

1. [Executive Summary & Pipeline Principles](#1-executive-summary--pipeline-principles)
2. [End-to-End Pipeline Architecture (16 Steps)](#2-end-to-end-pipeline-architecture-16-steps)
3. [Step-by-Step Technical Blueprint](#3-step-by-step-technical-blueprint)
   - [Step 1: Multi-Source Raw Acquisition](#step-1-multi-source-raw-acquisition)
   - [Step 2: Bronze Layer Raw Ingestion & Parquet Partitioning](#step-2-bronze-layer-raw-ingestion--parquet-partitioning)
   - [Step 3: Lineage & Provenance Metadata Tracking](#step-3-lineage--provenance-metadata-tracking)
   - [Step 4: Column Standardisation & Canonical Mapping](#step-4-column-standardisation--canonical-mapping)
   - [Step 5: String & Title Normalisation Algorithms](#step-5-string--title-normalisation-algorithms)
   - [Step 6: Cross-Source Entity & ID Resolution](#step-6-cross-source-entity--id-resolution)
   - [Step 7: Record Linkage & Multi-Pass Matching](#step-7-record-linkage--multi-pass-matching)
   - [Step 8: Deduplication & Merge Arbitration](#step-8-deduplication--merge-arbitration)
   - [Step 9: Financial Source Priority & Conflict Resolution](#step-9-financial-source-priority--conflict-resolution)
   - [Step 10: Multi-Currency Normalisation Engine](#step-10-multi-currency-normalisation-engine)
   - [Step 11: Real-Term Inflation Adjustment Engine](#step-11-real-term-inflation-adjustment-engine)
   - [Step 12: Missing Value Audit & Imputation Strategy](#step-12-missing-value-audit--imputation-strategy)
   - [Step 13: Data Quality Enforcement via Pydantic & Pandera](#step-13-data-quality-enforcement-via-pydantic--pandera)
   - [Step 14: Feature Extraction & Engineering Orchestration](#step-14-feature-extraction--engineering-orchestration)
   - [Step 15: Silver Layer Canonical Data Store Assembly](#step-15-silver-layer-canonical-data-store-assembly)
   - [Step 16: Gold Layer Temporal Split Dataset Generation](#step-16-gold-layer-temporal-split-dataset-generation)
4. [Technology Stack & Tooling Selection](#4-technology-stack--tooling-selection)
5. [Orchestration, Scheduling & Resilience](#5-orchestration-scheduling--resilience)
6. [Data Governance, Versioning & Auditability](#6-data-governance-versioning--auditability)

---

## 1. Executive Summary & Pipeline Principles

The CineMetrics Data Engineering Pipeline transforms heterogeneous, asynchronous, and geographically fragmented movie datasets into a unified, temporally leakage-free analytical data lake. 

The pipeline adheres to four fundamental engineering tenets:
1. **Temporal Correctness**: Every row in the training dataset is locked to an immutable historical timestamp. No post-release information ever contaminates pre-release feature vectors.
2. **Deterministic Provenance**: Every financial and metadata attribute can be traced directly to its source API payload, dump file, or manual ledger entry.
3. **Idempotence & Reproducibility**: Re-running the pipeline on identical raw input produces bit-for-bit identical feature matrices and training splits.
4. **Student-Feasible Compute**: The pipeline executes efficiently on single-node consumer hardware (16GB RAM) using columnar storage (Parquet), zero-copy transformations (PyArrow / DuckDB), and selective chunking in Pandas.

---

## 2. End-to-End Pipeline Architecture (16 Steps)

The pipeline transitions raw data across the classic medallion architecture: **Bronze (Raw Ingestion)** → **Silver (Conformed & Reconciled Canonical Store)** → **Gold (ML Training Sets & Feature Stores)**.

```
+----------------------------------------------------------------------------------------------------+
| BRONZE LAYER: INGESTION & AUDIT                                                                    |
| [1. Raw Acquisition] -> [2. Parquet Partitioning] -> [3. Provenance Logging] -> [4. Column Std]   |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| SILVER LAYER: ENTITY RESOLUTION & RECONCILIATION                                                   |
| [5. Title Normalisation] -> [6. ID Resolution] -> [7. Record Matching] -> [8. Deduplication]     |
| [9. Financial Reconciliation] -> [10. Currency Engine] -> [11. Inflation Engine]                  |
| [12. Missing Value Audit] -> [13. Pydantic Quality Gate]                                           |
+----------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼
+----------------------------------------------------------------------------------------------------+
| GOLD LAYER: ANALYTICAL & ML READINESS                                                              |
| [14. Feature Extraction] -> [15. Canonical Dataset] -> [16. Temporal Train/Val/Test Splits]       |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Step-by-Step Technical Blueprint

### Step 1: Multi-Source Raw Acquisition
- **Input**: External REST APIs (TMDB, YouTube Data API, Google Trends) and bulk dumps (IMDb TSV gzip files, Kaggle archives, Sacnilk/BOM reference tables).
- **Execution**: Asynchronous Python clients (`httpx`) with rate-limiting token buckets and exponential backoff retry policies.
- **Output**: Unprocessed raw JSON, TSV, and CSV files in `data/raw/{source}/{YYYY-MM-DD}/`.
- **Validation**: Checksum validation (SHA-256) verifying payload download integrity.

### Step 2: Bronze Layer Raw Ingestion & Parquet Partitioning
- **Input**: Downloaded raw payloads.
- **Execution**: Convert raw JSON and TSV directly into Apache Parquet format using PyArrow. Apply Snappy compression. Partition files by `source_name` and `acquisition_year_month`.
- **Output**: `data/bronze/{source}/part-*.parquet`.
- **Validation**: Schema conformance check ensuring all expected root keys exist.

### Step 3: Lineage & Provenance Metadata Tracking
- **Input**: Parquet batches from Step 2.
- **Execution**: Append metadata fields to every raw record:
  - `_source_id`: e.g., `tmdb_api`, `imdb_tsv`, `the_numbers_budget`
  - `_retrieval_timestamp`: ISO-8601 UTC timestamp
  - `_source_uri`: Exact API endpoint or archive file URI
  - `_pipeline_version`: Git commit SHA of the running pipeline
- **Output**: Enriched Bronze Parquet tables.
- **Validation**: Non-null assertion on all lineage metadata columns.

### Step 4: Column Standardisation & Canonical Mapping
- **Input**: Raw source-specific dataframes.
- **Execution**: Apply declarative YAML schema mapping dictionaries converting disparate naming conventions into canonical attributes:
  - TMDB `original_title`, IMDb `primaryTitle`, Kaggle `movie_title` → `title_raw`
  - TMDB `release_date`, IMDb `startYear` → `release_date_iso`
  - TMDB `budget`, The Numbers `production_budget` → `budget_nominal_raw`
- **Output**: Conformed dataframes with standard column headers.
- **Validation**: Validate that 100% of canonical required columns are mapped.

### Step 5: String & Title Normalisation Algorithms
- **Input**: `title_raw`, `release_date_iso`, `original_language`.
- **Execution**: Execute regex sanitization and linguistic normalisation:
  1. Strip leading and trailing whitespace; convert to lowercase.
  2. Strip diacritics and accents (Unicode NFKD normalization).
  3. Remove punctuation and special symbols except alphanumeric characters.
  4. Standardize Roman numerals (e.g., "Part II" -> "Part 2").
  5. Handle regional transliteration variants (e.g., "Baahubali" vs. "Bahubali").
  6. Generate `title_normalized` hash token.
- **Output**: Deterministic normalised string fields.
- **Validation**: Unit tests verifying edge-case transformations (e.g., "Spider-Man: No Way Home (2021)" -> "spider man no way home").

### Step 6: Cross-Source Entity & ID Resolution
- **Input**: Normalised datasets across TMDB, IMDb, and financial trackers.
- **Execution**:
  - Deterministic pass: Match via explicit foreign keys (TMDB provides `imdb_id` via `/movie/{id}/external_ids`).
  - Secondary pass: Match via exact `(title_normalized, release_year)` pair.
- **Output**: Unified entity mapping table mapping `(tmdb_id, imdb_id, internal_movie_id)`.
- **Validation**: Assert zero 1-to-many conflicting identifier associations.

### Step 7: Record Linkage & Multi-Pass Matching
- **Input**: Unresolved residual titles from Step 6.
- **Execution**: RapidFuzz multi-attribute weighted scoring:
  - Jaro-Winkler string similarity on title: 60% weight
  - Release year tolerance ($|year_1 - year_2| \le 1$): 20% weight
  - Primary director string similarity: 20% weight
  - Threshold: Composite score $\ge 0.88$ classified as match; $0.75 \le score < 0.88$ routed to manual review queue; $<0.75$ treated as distinct entity.
- **Output**: Linkage graph linking multi-source records to canonical `movie_id`.
- **Validation**: Precision/Recall verification against a manually curated ground-truth gold set of 200 Indian and Hollywood films.

### Step 8: Deduplication & Merge Arbitration
- **Input**: Linked record clusters.
- **Execution**: Identify duplicate entries (same physical film indexed under regional and international titles). Consolidate into a single canonical row. Maintain an array of `aliases` in the movie record.
- **Output**: Deduplicated master movie table.
- **Validation**: Confirm uniqueness of `movie_id`, `tmdb_id`, and `imdb_id`.

### Step 9: Financial Source Priority & Conflict Resolution
- **Input**: Discrepant box-office collections and budget figures across sources.
- **Execution**: Apply strict provenance arbitration hierarchy:
  - **Budget Priority**: The Numbers > Verified Studio Filings > TMDB > Trade Reports > Imputed
  - **Hollywood Revenue Priority**: Box Office Mojo / The Numbers > TMDB Reported > Third-party dumps
  - **Indian Box Office Priority**: Sacnilk / Trade Consensus > Bollywood Hungama > TMDB > Media Estimates
- **Output**: Canonical financial record storing:
  - Primary authoritative value
  - Source identifier and confidence rating (`verified`, `reported`, `estimated`)
  - Full audit array of all alternative reported values for transparency
- **Validation**: Flag any film where source variances exceed 25% for editorial verification.

### Step 10: Multi-Currency Normalisation Engine
- **Input**: Nominal financial figures reported in INR (₹), USD ($), GBP (£), EUR (€).
- **Execution**:
  - Map each transaction/collection event to the historical foreign exchange rate active on the exact `release_date`.
  - Ingestion of free daily FX reference tables (via Open Exchange Rates / European Central Bank historical feeds).
  - Convert all nominal values to standard nominal USD and standard nominal INR.
  - Retain original local currency string and nominal value untouched for auditability.
- **Output**: Standardized dual-currency fields (`budget_usd_nominal`, `worldwide_gross_usd_nominal`, etc.).
- **Validation**: Sanity check asserting exchange rate was within historical bounds for the target year.

### Step 11: Real-Term Inflation Adjustment Engine
- **Input**: Nominal financial attributes and historical release years.
- **Execution**:
  - Apply United States Bureau of Labor Statistics (BLS) Consumer Price Index (CPI-U) monthly series.
  - Baseline Anchor: 2024 USD constant dollars.
  - Formula:
    $$\text{Gross}_{\text{real\_2024}} = \text{Gross}_{\text{nominal}} \times \left( \frac{\text{CPI}_{\text{2024-01}}}{\text{CPI}_{\text{release\_date}}} \right)$$
  - Perform corresponding Indian CPI adjustment using Reserve Bank of India (RBI) historical inflation indices for domestic Indian analysis.
- **Output**: Real-term inflation-adjusted financial features.
- **Validation**: Assert real gross $\ge$ nominal gross for all films released prior to 2024.

### Step 12: Missing Value Audit & Imputation Strategy
- **Input**: Conformed Silver movie dataframes.
- **Execution**:
  - Generate column-level sparsity reports.
  - Strict Target Rules: Target variables (`worldwide_gross`, `opening_weekend_gross`) are **NEVER** imputed. Records lacking revenue targets are excluded from training splits (used only in inference/exploration).
  - Feature Imputation:
    - `runtime_minutes`: Imputed via genre-specific median.
    - `budget_nominal`: Categorized into `budget_tier` (`micro`, `low`, `mid`, `high`, `mega`) using KNN imputation based on genre, star power, and production company tier; add binary flag `is_budget_imputed = 1`.
- **Output**: Cleaned and imputed feature matrix.
- **Validation**: Zero missing values in mandatory model feature vectors.

### Step 13: Data Quality Enforcement via Pydantic & Pandera
- **Input**: Imputed conformed dataframe.
- **Execution**: Execute declarative schema validation test suites:
  - Pandera DataFrame schemas testing statistical distributions and type bounds.
  - Pydantic models verifying individual entity integrity.
  - Hard constraint checks: `release_year` $\in [1900, 2030]$, `budget_usd` $> 0$, `runtime_minutes` $\in [10, 600]$.
- **Output**: Validation certification log.
- **Validation**: Pipeline halts with non-zero exit code if fatal validation errors exceed 0.5% threshold.

### Step 14: Feature Extraction & Engineering Orchestration
- **Input**: Validated conformed entities.
- **Execution**: Compute time-locked derived features (detailed in Doc 09):
  - Star power historical rolling decay formulas.
  - Director track record averages.
  - Release calendar density & clash competition metrics.
  - Digital trailer momentum velocity.
- **Output**: High-dimensional feature vector table.
- **Validation**: Verify that all feature transformations operate solely on data with timestamps strictly earlier than the target prediction snapshot date.

### Step 15: Silver Layer Canonical Data Store Assembly
- **Input**: Validated master entities, normalized financials, and feature tables.
- **Execution**: Materialize and index into relational PostgreSQL tables (`movies`, `movie_financials`, `persons`, `movie_cast`, `feature_snapshots`) and mirror to optimized columnar Parquet partitions.
- **Output**: Production-ready relational and analytical database.
- **Validation**: Foreign key referential integrity checks and row count parity audits between PostgreSQL and Parquet mirrors.

### Step 16: Gold Layer Temporal Split Dataset Generation
- **Input**: Feature vectors and verified target labels.
- **Execution**: Partition dataset strictly by calendar release date:
  - **Training Set**: Releases before 2020-01-01
  - **Validation Set**: Releases between 2020-01-01 and 2022-12-31
  - **Holdout Test Set**: Releases between 2023-01-01 and 2024-12-31
- **Output**: Immutable version-controlled datasets (`train_v1.parquet`, `val_v1.parquet`, `test_v1.parquet`) with cryptographic hash signatures.
- **Validation**: Assert zero temporal overlap or entity leakage across splits.

---

## 4. Technology Stack & Tooling Selection

| Component | Technology | Selection Justification |
|---|---|---|
| **Raw Storage** | Apache Parquet (Snappy) | High-speed columnar scans, compact binary footprint, open standard. |
| **Data Processing** | Python 3.11 + Pandas + PyArrow | Industry-standard tabular operations, PyArrow C++ engine acceleration. |
| **Exploratory SQL** | DuckDB | Blazing fast in-process analytical SQL on local Parquet files without server overhead. |
| **Schema Validation** | Pandera + Pydantic v2 | Type safety, declarative distribution checks, seamless FastAPI integration. |
| **String & Fuzzy Matching** | RapidFuzz (C++ engine) | 10x–50x faster than traditional `fuzzywuzzy` for bulk Levenshtein string scoring. |
| **Relational Store** | PostgreSQL 15+ | Acid compliance, robust indexing (B-Tree, GIN, GiST), JSONB support. |

---

## 5. Orchestration, Scheduling & Resilience

- **Scheduler**: APScheduler running inside the Python runtime (no heavy Airflow or Kubernetes overhead required).
- **Batch Frequency**:
  - Daily at 02:00 IST: Discovery & incremental ingestion.
  - Weekly (Sunday 04:00 IST): Re-calculation of rolling talent star-power scores.
  - On-Demand / Ad-Hoc: Manual ingestion triggers via admin endpoints.
- **Failure Recovery**:
  - Dead Letter Queue (`failed_ingestion_payloads/`).
  - Automatic retry with exponential backoff (3 attempts: 5s, 30s, 300s).
  - Transactional rollback on database writes via SQLAlchemy session managers.

---

## 6. Data Governance, Versioning & Auditability

1. **Dataset Versioning**: Every generated ML dataset adheres to semantic versioning: `DATASET_V{major}.{minor}_{timestamp_hash}`.
2. **Audit Log**: The `data_source_records` table captures the exact timestamp, raw payload hash, source URI, and operator ID for every row mutation.
3. **Immutability of History**: Snapshots once written are read-only. Updates create new timestamped snapshot versions rather than mutating historical records.
