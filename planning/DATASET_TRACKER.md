# CineMetrics — Master Dataset Acquisition & Provenance Tracker

**Document ID:** PLN-01  
**Version:** 1.0  
**Status:** Operational Tracking Matrix  
**Last Updated:** 2026-11  
**Related Docs:** [Dataset Research](../docs/04_DATASET_RESEARCH.md) | [Data Acquisition Guide](../docs/05_DATA_ACQUISITION_GUIDE.md)

---

## 1. Primary Dataset Registry

| Dataset Name | Source / Provider | Access Method | File Format | Estimated Records | Geographic Scope | Licensing / Terms | Acquisition Status | Local Storage Path | Target Phase |
|---|---|---|:---:|:---:|---|---|:---:|---|:---:|
| **TMDB Upcoming Releases** | The Movie Database (TMDB) | REST API (`/movie/upcoming`) | JSON / Parquet | Dynamic (~500 active) | Global & Indian Regional | Free non-commercial with attribution | Planned | `data/raw/tmdb/upcoming/` | Phase 2 / 11 |
| **TMDB Discover Catalogue** | The Movie Database (TMDB) | REST API (`/discover/movie`) | JSON / Parquet | ~50,000+ films | Global (hi, te, ta, ml, kn, en) | Free non-commercial with attribution | Planned | `data/raw/tmdb/catalog/` | Phase 2 |
| **IMDb Title Basics** | IMDb Non-Commercial Datasets | Bulk HTTP Gzip (`title.basics.tsv.gz`) | TSV / Parquet | ~10M rows (filter to ~700k movies) | Global | Free non-commercial personal use | Planned | `data/raw/imdb/title_basics/` | Phase 2 |
| **IMDb Title Ratings** | IMDb Non-Commercial Datasets | Bulk HTTP Gzip (`title.ratings.tsv.gz`) | TSV / Parquet | ~1.5M ratings | Global | Free non-commercial personal use | Planned | `data/raw/imdb/title_ratings/` | Phase 2 |
| **IMDb Title Principals** | IMDb Non-Commercial Datasets | Bulk HTTP Gzip (`title.principals.tsv.gz`) | TSV / Parquet | ~50M credit links | Global | Free non-commercial personal use | Planned | `data/raw/imdb/title_principals/` | Phase 2 |
| **IMDb Name Basics** | IMDb Non-Commercial Datasets | Bulk HTTP Gzip (`name.basics.tsv.gz`) | TSV / Parquet | ~13M talent records | Global | Free non-commercial personal use | Planned | `data/raw/imdb/name_basics/` | Phase 2 |
| **The Numbers Movie Budgets**| The Numbers (Nash Information) | Downloadable reference table | CSV / Parquet | ~6,500 movies with budgets | Primarily US / Major International | Public domain reference data | Planned | `data/raw/the_numbers/budgets/` | Phase 2 |
| **TMDB 5000 Movie Dataset** | Kaggle (tmdb/tmdb-movie-metadata) | Kaggle CLI API | CSV / Parquet | 4,803 movies | Hollywood / Global | CC0: Public Domain | Planned | `data/raw/kaggle/tmdb_5000/` | Phase 2 |
| **The Movies Dataset** | Kaggle (rounakbanik/the-movies-dataset)| Kaggle CLI API | CSV / Parquet | 45,000 movies | Global | CC0: Public Domain | Planned | `data/raw/kaggle/movies_dataset/`| Phase 2 |
| **Bollywood Box Office Dataset**| Kaggle (Curated Indian Cinema) | Kaggle CLI API | CSV / Parquet | ~2,500 Hindi films | Indian Cinema (Bollywood) | CC BY-SA 4.0 | Planned | `data/raw/kaggle/bollywood_box_office/` | Phase 2 |
| **Sacnilk Indian Box Office** | Sacnilk Reference Tracking | Reference Web Ingestion | JSON / Parquet | ~1,200 Indian films (2018–2024) | Tollywood, Bollywood, Kollywood | Factual public reporting (Fair use)| Planned | `data/raw/indian_trade/sacnilk/` | Phase 2 / 12 |
| **YouTube Official Trailers** | Google YouTube Data API v3 | REST API (`videos.list`, `search.list`) | JSON | Trailing views for tracked films | Global & Regional trailers | Free tier (10,000 units/day) | Planned | `data/raw/youtube/trailers/` | Phase 2 / 9 |
| **Google Trends Search Series**| Google Trends via Pytrends | Unofficial Python Client | JSON / CSV | Relative interest index (0–100) | Regional & Global Search | Non-commercial research | Planned | `data/raw/google_trends/` | Phase 2 / 5 |

---

## 2. Ingestion Progress & Verification Ledger

| Date Checked | Target Source | Records Downloaded | Checksum Verified | Parquet Converted | Schema Validated | Notes / Issues |
|:---:|---|:---:|:---:|:---:|:---:|---|
| **2026-11-06** | **IMDb Title Ratings** | 1,729,129 | Verified Size (8.3 MB gz) | Yes (12.75 MB) | Yes | Acquired via `download_imdb.py` into `data/raw/imdb/title_ratings_movies.parquet` |
| **2026-11-06** | **IMDb Title Basics** | 916,973 | Verified Size (219.2 MB gz) | Yes (38.69 MB) | Yes | 12.9M raw records scanned; filtered to 916,973 movies |
| **2026-11-06** | **Kaggle TMDB 5000** | 4,803 | Verified | Yes (13.16 MB) | Yes | Movies & credits ingested to `data/raw/kaggle/tmdb-5000-movie-dataset/` |
| **2026-11-06** | **Kaggle Movie Industry** | 7,668 | Verified | Yes (0.45 MB) | Yes | Financials (budget, gross) ingested to `data/raw/kaggle/movie-industry-financials/` |
| **2026-11-06** | **Kaggle Bollywood 1000** | 1,000 | Verified | Yes (0.04 MB) | Yes | Indian box office ingested to `data/raw/kaggle/top-1000-bollywood/` |
| **2026-11-06** | **Kaggle Telugu & Hindi Revenue** | 493 | Verified | Yes (0.02 MB) | Yes | Regional revenue ingested to `data/raw/kaggle/telugu-hindi-revenue/` |
| **2026-11-06** | **YouTube Data API v3** | Active / Live | Verified | Yes (0.01 MB) | Yes | Real-time trailer engagement pipeline verified and working |
| **2026-11-06** | **TMDB Upcoming Releases** | 111 | Verified | Yes (0.04 MB) | Yes | Harvested IN & US upcoming releases via `fetch_tmdb.py` |
| **2026-11-06** | **TMDB Indian Cinema Catalog** | 1,396 | Verified | Yes (0.35 MB) | Yes | Harvested hi, te, ta, ml, kn catalogs (2018–2024) |
| **2026-11-06** | **The Numbers Budgets** | Schema Ready | Reference table | Formatted | Yes | Scraper blocked by Cloudflare 403; mapped to Kaggle TMDB 5000 budget backup |
