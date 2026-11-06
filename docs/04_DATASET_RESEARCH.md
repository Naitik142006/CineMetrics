# CineMetrics — Dataset Research & Collection Strategy

**Document ID:** DOC-04  
**Version:** 1.0  
**Status:** Complete — Planning Phase  
**Last Reviewed:** 2024-01-01  
**Owner:** Data Engineering Team  
**Related Docs:** [05_DATA_SCHEMA_AND_DATABASE_DESIGN.md](05_DATA_SCHEMA_AND_DATABASE_DESIGN.md) · [06_DATA_INGESTION_PIPELINE.md](06_DATA_INGESTION_PIPELINE.md) · [16_DATA_UPDATE_AND_RETRAINING_POLICY.md](16_DATA_UPDATE_AND_RETRAINING_POLICY.md)

---

## Table of Contents

1. [Data Strategy Overview](#1-data-strategy-overview)
2. [Primary Data Sources](#2-primary-data-sources)
3. [Secondary Data Sources](#3-secondary-data-sources)
4. [Indian Cinema Specific Sources](#4-indian-cinema-specific-sources)
5. [NLP and Sentiment Data Sources](#5-nlp-and-sentiment-data-sources)
6. [Kaggle Datasets Evaluation](#6-kaggle-datasets-evaluation)
7. [Data Gaps and Mitigation](#7-data-gaps-and-mitigation)
8. [Legal and Ethical Considerations](#8-legal-and-ethical-considerations)
9. [Data Volume and Storage Estimates](#9-data-volume-and-storage-estimates)
10. [Collection Priority and Sequencing](#10-collection-priority-and-sequencing)

---

## 1. Data Strategy Overview

CineMetrics requires three fundamentally different categories of data:

| Category | Purpose | Update Frequency |
|---|---|---|
| **Historical movie data** | ML model training corpus | One-time + periodic refresh |
| **Live/upcoming movie data** | Real-time prediction pipeline | Daily to weekly |
| **Sentiment/social signals** | NLP feature enrichment | Per-movie, near release |

### Design Principle: Source Hierarchy

For every data attribute, a **source hierarchy** is established. When source A is unavailable, fall back to source B, then C. This prevents single-source failures from blocking ingestion.

```
Example for "worldwide box office gross":
  Primary:   The Numbers API or Box Office Mojo
  Fallback:  TMDB revenue field
  Fallback2: Wikipedia infobox scrape (REQUIRES VERIFICATION per film)
  Manual:    Sacnilk / Bollywood Hungama for Indian markets
```

### Two-Phase Data Approach

**Phase 1 — Bootstrap (Training Data):**  
Collect 2,000–5,000 historical films (2010–2023) with verified box-office actuals. This corpus is static — it is used exclusively for model training and will not be updated except for periodic retraining cycles.

**Phase 2 — Live Pipeline:**  
Ongoing ingestion of newly announced, in-production, and newly released films. This powers the "Upcoming Releases Intelligence" mode and provides future ground truth for model evaluation.

---

## 2. Primary Data Sources

### 2.1 TMDB (The Movie Database) API

**URL:** https://www.themoviedb.org/documentation/api  
**Access:** Free API key (no cost for non-commercial use)  
**Rate Limit:** 40 requests per 10 seconds (REQUIRES VERIFICATION — check current TMDB docs)  
**Data Format:** JSON over HTTPS

#### What TMDB Provides

| Endpoint | Key Fields | Use in CineMetrics |
|---|---|---|
| `/movie/{id}` | title, budget, revenue, release_date, genres, runtime, status, production_companies, production_countries, spoken_languages, overview, popularity, vote_average, vote_count, tagline | Core movie metadata; primary revenue target (global) |
| `/movie/{id}/credits` | cast (name, character, order, popularity), crew (director, producer, DP, composer) | Cast-based features, director track record |
| `/movie/{id}/keywords` | keyword list | Genre-adjacent features, theme tagging |
| `/movie/{id}/release_dates` | certification (G/PG/R etc.), release dates by region | Age rating feature; regional release calendar |
| `/movie/{id}/videos` | YouTube trailer key, type, published_at | Trailer metadata for YouTube API cross-reference |
| `/movie/{id}/images` | poster_path, backdrop_path | Poster features (future: CNNs) |
| `/movie/{id}/similar` | similar movie IDs | Competitive landscape analysis |
| `/movie/{id}/recommendations` | recommended movie IDs | Franchise/IP detection |
| `/movie/upcoming` | List of upcoming movies | Automated discovery |
| `/movie/now_playing` | Currently in theatres | Live tracking |
| `/movie/popular` | Trending movies | Social heat signal |
| `/person/{id}` | biography, known_for_department, popularity, birthday | Person-level enrichment |
| `/search/movie` | Fuzzy search results | Deduplication, manual lookup |
| `/discover/movie` | Filtered movie discovery | Bulk historical collection |

#### TMDB Data Quality Notes

> [!WARNING]
> TMDB `budget` and `revenue` fields are notoriously incomplete. As of 2024, **fewer than 30% of movies** have non-zero budget/revenue values. For the ML target variable, supplementary sources (The Numbers, Box Office Mojo) are mandatory.

- **Completeness:** Metadata fields (title, genres, cast) are generally >90% complete for movies with 100+ votes.
- **Revenue field:** Often zero or null, especially for non-Hollywood and older films.
- **Budget field:** More frequently populated for Hollywood; sparse for Indian films.
- **Vote count:** Good proxy for popularity/cultural relevance but not audience score.
- **Popularity score:** TMDB's own proprietary metric — useful but not directly interpretable.

#### TMDB Collection Strategy

```python
# PLANNED — not implemented
# Step 1: Discover all movies by year using /discover/movie
# Pagination: 500 pages × 20 results = up to 10,000 movies per year (ESTIMATED)
# Step 2: For each movie_id, fetch full details + credits + keywords + release_dates
# Step 3: Store raw JSON in a staging table; normalize in a separate ETL step
# Total estimated API calls for 5,000 movies: ~25,000 calls (5 endpoints × 5,000)
# Time at 40 req/10s: ~6,250 seconds ≈ ~1.75 hours (single-threaded)
```

---

### 2.2 IMDb Non-Commercial Datasets

**URL:** https://developer.imdb.com/non-commercial-datasets/  
**Access:** Free download; non-commercial use only  
**Format:** Gzipped TSV files  
**Update Frequency:** Daily snapshots  
**License:** Personal and non-commercial use only (see Terms of Service)

#### Available Files and Relevance

| File | Size (ESTIMATED) | Key Columns | CineMetrics Use |
|---|---|---|---|
| `title.basics.tsv.gz` | ~800 MB | tconst, titleType, primaryTitle, startYear, endYear, runtimeMinutes, genres | Movie type filtering, runtime, genre; use for TMDB-IMDb ID mapping |
| `title.ratings.tsv.gz` | ~25 MB | tconst, averageRating, numVotes | Audience reception signal — powerful feature |
| `title.principals.tsv.gz` | ~600 MB | tconst, ordering, nconst, category, job, characters | Cast/crew structure by movie |
| `name.basics.tsv.gz` | ~400 MB | nconst, primaryName, birthYear, primaryProfession, knownForTitles | Person metadata, career linking |
| `title.crew.tsv.gz` | ~90 MB | tconst, directors, writers | Director and writer IDs |
| `title.akas.tsv.gz` | ~1.5 GB | titleId, region, title, language | Alternative titles for India-region matching |
| `title.episode.tsv.gz` | ~200 MB | tconst, parentTconst, seasonNumber, episodeNumber | TV series — filter out for movie-only analysis |

#### IMDb Integration Notes

- **IMDb tconst ↔ TMDB movie_id mapping:** TMDB provides an `imdb_id` field in `/movie/{id}` responses. This is the primary join key.
- **Ratings** (`averageRating`, `numVotes`) from `title.ratings.tsv.gz` are among the most informative features because they reflect historical audience reception for the director's and cast's prior films.
- **Data leakage risk:** IMDb ratings for a *target movie* being predicted must **never** be used as an input feature (they reflect post-release opinion). Only use ratings of *prior works* of cast/crew.
- Filter `title.basics` to `titleType IN ('movie', 'tvMovie')` before joining.

---

### 2.3 The Numbers

**URL:** https://www.the-numbers.com/  
**Access:** Public web; no official API  
**Format:** HTML tables (web scraping required)  
**Legal:** Terms of service must be verified before scraping. Rate-limit scraper to 1 request / 2 seconds minimum. The Numbers is a reputable source for Hollywood box-office data.

#### What The Numbers Provides

- **Opening weekend domestic gross** (US)
- **Total domestic gross** (North America)
- **Total worldwide gross** (sum of domestic + international)
- **Production budget** (self-reported by studios — treat as approximate)
- **Release date** (confirmed theatrical)
- **Distributor**
- **MPAA rating**
- **Genre classifications** (The Numbers proprietary)

> [!IMPORTANT]
> The Numbers is the gold standard for Hollywood production budgets and domestic box office. For international (non-US) grosses, supplement with Box Office Mojo or manual research.

#### Scraping Approach (PLANNED)

```python
# PLANNED — not implemented
# Target pages:
#   https://www.the-numbers.com/movie/<slug>#tab=box-office
#   https://www.the-numbers.com/box-office-records/worldwide/all-movies/cumulative/all-time
# Use requests + BeautifulSoup
# Respect robots.txt
# Minimum 2-second delay between requests
# Cache all HTML responses locally before parsing
```

---

### 2.4 Box Office Mojo (IMDb Owned)

**URL:** https://www.boxofficemojo.com/  
**Access:** Public web; no official API  
**Format:** HTML  
**Notes:** Owned by Amazon/IMDb. Terms of Service should be reviewed. Data is high-quality for North American and international markets.

#### Key Data Points

- Domestic opening weekend gross
- International gross by territory (UK, Germany, China, India, etc.)
- Franchise/series collections
- Year-by-year top earners

#### Usage in CineMetrics

Box Office Mojo serves as a **validation cross-reference** for The Numbers figures, not a primary collection source. If The Numbers and BOM disagree by >5%, flag for manual review.

---

## 3. Secondary Data Sources

### 3.1 YouTube Data API v3

**URL:** https://developers.google.com/youtube/v3  
**Access:** Free tier with daily quota (10,000 units/day by default)  
**Format:** JSON  
**Purpose:** Trailer analytics as pre-release sentiment signal

#### Endpoints Used

| Endpoint | Data Collected | Feature Engineering |
|---|---|---|
| `videos.list` | viewCount, likeCount, commentCount, publishedAt | View velocity, like ratio |
| `commentThreads.list` | Top-level comment text, author, like count | NLP sentiment corpus |
| `search.list` | Search for official trailers by movie name | Trailer discovery |

#### Quota Management

```
Quota costs (ESTIMATED):
  videos.list:            1 unit per request (up to 50 video IDs per request)
  commentThreads.list:    1 unit per request (up to 100 results)
  search.list:            100 units per request

Daily plan for ~10 movies/day:
  - 1 search per movie × 100 units = 1,000 units
  - 1 videos.list per movie × 1 unit = 10 units
  - 5 comment pages per movie × 1 unit = 50 units
  Total: ~1,060 units/day — well within 10,000 limit
```

#### Limitations

- Comment data is not available for videos with comments disabled.
- YouTube quota resets at midnight Pacific Time.
- Comments must be fetched individually per video — no bulk endpoint.
- Deleted/unlisted trailers cannot be retrieved retrospectively.

---

### 3.2 Google Trends (Unofficial)

**Access:** Via `pytrends` Python library (unofficial, reverse-engineered)  
**Format:** Pandas DataFrame (returned by pytrends)  
**Rate Limit:** Aggressive — 1 request per 5-10 seconds minimum to avoid 429 errors  
**Purpose:** Relative search interest for movie titles and actors

> [!WARNING]
> `pytrends` is an unofficial library that reverse-engineers Google Trends. Google has no official API for Trends data. This library may break without notice. Use defensively with try/except and treat as optional enrichment data.

#### Data Collected

- **Relative search interest** (0–100 scale) for a movie title over time
- **Geographic distribution** of search interest (by state/country)
- **Related queries** (can surface buzz around similar films)
- **Interest over time** for director/actor names (career trajectory signal)

#### Implementation Notes

```python
# PLANNED — not implemented
from pytrends.request import TrendReq

pytrends = TrendReq(hl='en-US', tz=330)  # tz=330 for IST
pytrends.build_payload(
    kw_list=['RRR movie', 'SS Rajamouli'],
    timeframe='2021-01-01 2022-01-01',
    geo='IN'
)
df_interest = pytrends.interest_over_time()
# Returns weekly relative interest; normalize to 0-1 for feature use
```

---

### 3.3 Wikidata / Wikipedia

**Access:** Wikidata Query Service (SPARQL) — free; Wikipedia REST API — free  
**Purpose:** Supplementary budget/gross data, franchise detection, real-world context

#### SPARQL Query Example (PLANNED)

```sparql
SELECT ?film ?filmLabel ?budget ?boxOffice WHERE {
  ?film wdt:P31 wd:Q11424.          # instance of: film
  ?film wdt:P577 ?releaseDate.       # release date
  OPTIONAL { ?film wdt:P2130 ?budget. }      # cost (budget)
  OPTIONAL { ?film wdt:P2142 ?boxOffice. }   # box office collection
  FILTER(YEAR(?releaseDate) >= 2010)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 10000
```

> [!NOTE]
> Wikidata budget/revenue figures often reflect Wikipedia article data, which may be inconsistent across films. Use as a tertiary fallback only.

---

## 4. Indian Cinema Specific Sources

### 4.1 Sacnilk

**URL:** https://sacnilk.com/  
**Access:** Public web (web scraping)  
**Data:** Day-wise box-office collections for Bollywood, Telugu, Tamil, Malayalam, Kannada films

#### What Sacnilk Provides

| Data Type | Granularity | Markets Covered |
|---|---|---|
| Opening day collection | Per-day | India (by language/circuit) |
| First week collection | Day-by-day | India (all industries) |
| Total India net collection | Cumulative | All major Indian industries |
| OTT premiere details | Date + platform | Netflix, Prime, Disney+ Hotstar, etc. |
| Budget vs. collection comparison | Per film | Yes |
| Verdict (Hit/Flop/Blockbuster) | Official trade verdict | Yes |

> [!IMPORTANT]
> Sacnilk is the primary source for **India net collection** data, which is distinct from worldwide gross. Indian box-office figures are typically reported as *net* (after entertainment tax) rather than *gross* (before tax). See [../docs/16_FINANCIAL_METRICS_AND_CALCULATIONS.md] for definitions.

#### Scraping Strategy

```
Target URLs pattern:
  https://sacnilk.com/[movie-name]-box-office-collection/
  
Challenges:
  - URL slug format varies (hyphens, year suffix sometimes included)
  - Layout changes between older and newer pages
  - Day-wise table structure varies slightly by film

Approach:
  - Use requests + BeautifulSoup
  - Parse multiple table structures with try/except
  - Store raw HTML for reprocessing
  - Implement 3-second delay between requests
  - Check robots.txt before scraping
```

---

### 4.2 Bollywood Hungama

**URL:** https://www.bollywoodhungama.com/  
**Access:** Public web  
**Data:** Box-office verdicts, budget information, collection milestones for Bollywood

> [!NOTE]
> Bollywood Hungama is a secondary validation source for Bollywood-specific data. Cross-reference against Sacnilk for India net collections.

---

### 4.3 Koimoi

**URL:** https://www.koimoi.com/  
**Access:** Public web  
**Data:** Bollywood and South Indian box-office data, OTT deals, celebrity rankings

---

### 4.4 Ormax Media (Cited Data Only)

**URL:** https://www.ormaxmedia.com/  
**Access:** Reports published publicly; no API  
**Data:** Opening day estimates, occupancy ratings, pre-release buzz scores

> [!NOTE]
> Ormax publishes weekly "Movie Power Index" scores and "India OTT Audience" reports. These are cited in trades and can be manually collected for key films. No programmatic access is available.

---

### 4.5 Trade Buzz Data (Manual Collection)

For high-importance films (budget > ₹100 Cr), manually track:
- Pre-release advance booking numbers (from ticketing platforms — BookMyShow, PVR)
- Occupancy percentages on Day 1 (trade reports)
- Screen count information

This data is sparse and manual, used only as supplementary features.

---

## 5. NLP and Sentiment Data Sources

### 5.1 Rotten Tomatoes

**Access:** No official public API; unofficial scraping possible  
**Data:** Tomatometer score (critic %) + Audience Score (%), critic review text, audience review text

> [!WARNING]
> Rotten Tomatoes has no public API. Scraping must respect their Terms of Service. The Tomatometer score and audience score are valuable features but must be collected at the right temporal point (post-release for actuals, estimated pre-release scores not available).

#### Feature Engineering from RT

- `rt_tomatometer`: Critic consensus score (0–100)
- `rt_audience_score`: Audience score (0–100)  
- `rt_critic_sentiment`: Average sentiment polarity of critic review texts (NLP)
- `rt_consensus_text`: Short consensus description (NLP embedding)

---

### 5.2 IMDb User Reviews

**Access:** IMDb website (scraping); also available as informal corpus on Kaggle  
**Format:** HTML text  
**Data:** User review text, rating (1–10), date, helpfulness votes

#### Use in CineMetrics

- Retrospective analysis only (post-release)
- Used to build ground-truth for sentiment model training
- Future feature: sentiment trajectory (do reviews improve or worsen over time?)

---

### 5.3 Pre-Collected Sentiment Datasets (Kaggle)

For NLP model fine-tuning (not features for revenue prediction), use:

| Dataset | Description | Link |
|---|---|---|
| SST-2 (Stanford Sentiment Treebank) | English sentiment binary classification | HuggingFace Datasets |
| IMDB Movie Reviews | 50,000 English reviews, positive/negative | HuggingFace Datasets |
| Multilingual Sentiment (SemEval) | Multi-language sentiment annotations | REQUIRES VERIFICATION |

---

## 6. Kaggle Datasets Evaluation

The following Kaggle datasets have been evaluated for use as the ML training corpus bootstrap:

### 6.1 TMDB 5000 Movie Dataset

**Kaggle URL:** https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata  
**Files:** `tmdb_5000_movies.csv`, `tmdb_5000_credits.csv`  
**Record Count:** ~4,803 movies (ESTIMATED — verify on Kaggle)  
**Coverage:** Primarily Hollywood, 1960s–2017  
**Key Columns:** budget, revenue, genres, keywords, cast, crew, popularity, vote_average, vote_count, production_companies, release_date, runtime

#### Evaluation

| Criterion | Assessment |
|---|---|
| Revenue completeness | ~40% of movies have non-zero revenue (ESTIMATED) |
| Budget completeness | ~50% of movies have non-zero budget (ESTIMATED) |
| Indian cinema coverage | Minimal — primarily Hollywood |
| Recency | Cuts off ~2017; needs supplementation for 2018–2024 |
| Data quality | Generally clean; cast/crew fields are JSON-encoded |
| License | TMDB license — non-commercial use |

**Decision:** Use as bootstrap training data. Supplement with TMDB API pulls for 2017–2024 and Indian cinema data.

---

### 6.2 The Movies Dataset (GroupLens)

**Kaggle URL:** https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset  
**Files:** movies_metadata.csv, credits.csv, keywords.csv, links.csv, ratings.csv, ratings_small.csv  
**Record Count:** ~45,000 movies, ~26 million ratings (ESTIMATED)  
**Coverage:** Broad historical, primarily English-language

#### Evaluation

| Criterion | Assessment |
|---|---|
| Revenue completeness | Low — TMDB source, same gaps |
| Rating data | 26M user ratings — excellent for popularity signal |
| Indian cinema | Sparse |
| Use | Good for collaborative-filtering style popularity features |
| License | CC BY 4.0 |

**Decision:** Use `ratings.csv` for popularity signal. Skip duplicate metadata fields already from TMDB 5000.

---

### 6.3 Bollywood Movies Dataset

Multiple Bollywood datasets exist on Kaggle with varying quality. At time of writing, recommended candidate:

**Search Terms:** "bollywood box office collection" on Kaggle  
**Expected Coverage:** 2000–2022 Bollywood films  
**Key Fields:** movie name, year, budget, india_net_gross, verdict

> [!NOTE]
> REQUIRES VERIFICATION — Identify the most complete, recently updated Bollywood dataset on Kaggle before collection begins. Evaluate for: year coverage, budget inclusion, India-net vs worldwide distinction, verdict label consistency.

---

### 6.4 Indian Movies Dataset (IMDB-based)

**Expected Source:** Kaggle — search "Indian movies IMDB"  
**Coverage:** Bollywood + South Indian industries  
**Key Fields:** IMDb ID, title, language, genre, director, actors, rating, votes

**Decision:** Use for South Indian cinema bootstrap where Sacnilk scraping is insufficient.

---

## 7. Data Gaps and Mitigation

| Data Gap | Impact | Mitigation Strategy |
|---|---|---|
| TMDB budget/revenue fields missing for 70%+ of movies | Cannot train regression model on this field alone | Supplement with The Numbers + Sacnilk + Kaggle datasets; build ensemble of data sources |
| Indian cinema budgets largely unreported | Budget feature unavailable for many Indian films | Use budget ranges/buckets instead of exact figures; impute with industry+year median |
| Pre-release social data not available historically | Cannot train on historical YouTube/Twitter signals | Train base model without sentiment; add sentiment as supplementary model for recent films |
| Advance booking data not programmatically available | Cannot use as feature | Manual collection for key films only; treat as N/A for most |
| Telugu/Tamil/Malayalam film coverage sparse | South Indian model may underfit | Weight Sacnilk + IMDb + Wikipedia manual collection for South Indian cinema |
| International gross breakdown by territory | Cannot model territory-specific performance | Use total worldwide gross as target; domestic India + overseas India as supplementary targets |
| OTT sale prices not public | Cannot model streaming value | Classify as "has OTT deal" (binary) based on announcement data |

---

## 8. Legal and Ethical Considerations

### 8.1 Terms of Service Summary

| Source | Commercial Use | Scraping Permitted | Rate Limiting Required | Notes |
|---|---|---|---|---|
| TMDB API | Non-commercial only (free tier) | Via API (not scraping) | Yes — 40 req/10s | Must display TMDB attribution |
| IMDb Non-Commercial Datasets | Non-commercial only | Downloaded files | N/A | Cannot redistribute |
| The Numbers | Non-commercial research | Robots.txt must be checked | Yes — 1 req/2s min | ToS requires verification |
| Sacnilk | Non-commercial research | Robots.txt must be checked | Yes — 3s min | ToS requires verification |
| YouTube Data API | Non-commercial (free quota) | Via API | Quota-based | Must display YouTube branding |
| Google Trends (pytrends) | No official ToS | Unofficial (use cautiously) | Yes — 10s+ | May break without notice |
| Rotten Tomatoes | No scraping (ToS) | Not permitted | — | Manual data collection only |
| Box Office Mojo | Non-commercial research | Robots.txt must be checked | Yes | ToS requires verification |

> [!CAUTION]
> Before beginning any web scraping, **verify the current robots.txt and Terms of Service** for each site. This documentation reflects planning-phase research and may be outdated. When in doubt, contact the website owner or use only official APIs.

### 8.2 Data Attribution Requirements

- TMDB data must display the TMDB logo and credit: "This product uses the TMDB API but is not endorsed or certified by TMDB."
- IMDb data files are for personal, non-commercial use only. No redistribution.
- Google/YouTube data must follow YouTube API Services Terms of Service.

### 8.3 Privacy Considerations

- No collection of Personally Identifiable Information (PII) of regular users.
- YouTube commenter usernames/identities are **not** stored — only comment text and engagement counts.
- No IMDb user review author data is stored — only review text and rating.

---

## 9. Data Volume and Storage Estimates

### 9.1 Raw Data Volume (Training Corpus)

| Dataset | Estimated Rows | Estimated Size |
|---|---|---|
| Movies (core metadata) | 10,000–15,000 | 50–100 MB |
| Cast entries | 150,000–300,000 | 200–400 MB |
| Crew entries | 100,000–200,000 | 150–300 MB |
| IMDb ratings (linked) | 10,000–15,000 | 5 MB |
| YouTube trailer data | 5,000–8,000 trailers | 20 MB |
| YouTube comments | 500,000–2,000,000 | 2–8 GB (text) |
| IMDb user reviews | 100,000–500,000 | 1–5 GB (text) |
| Sacnilk collections | 1,000–3,000 films | 10–50 MB |
| Feature engineered table | 10,000 rows × 150 columns | 50–200 MB |

> [!NOTE]
> YouTube comment and review text data is large. Store raw text in a separate `reviews` table or file store; extract numeric sentiment features before model training. Never store raw comment text in the main feature matrix.

### 9.2 Storage Architecture

```
data/
├── raw/                    # Never committed to git — in .gitignore
│   ├── tmdb/               # Raw TMDB JSON responses per movie
│   ├── imdb/               # Extracted IMDb TSV subsets
│   ├── thenumbers/         # Scraped HTML cache
│   ├── sacnilk/            # Scraped HTML cache (Indian data)
│   └── youtube/            # Raw YouTube API responses
├── processed/              # Cleaned, normalized tables (Parquet)
│   ├── movies.parquet
│   ├── cast.parquet
│   ├── crew.parquet
│   ├── collections.parquet
│   └── features.parquet
└── external/               # Kaggle downloads (also not committed)
    ├── tmdb_5000_movies.csv
    └── bollywood_dataset.csv
```

---

## 10. Collection Priority and Sequencing

The following sequencing is recommended to unblock ML training as quickly as possible:

### Priority 1 — Immediate (Day 1–3)

1. **Download IMDb Non-Commercial Datasets** — Free, instant, high quality
   - `title.basics`, `title.ratings`, `title.principals`, `name.basics`, `title.crew`
2. **Download Kaggle TMDB 5000 Movie Dataset** — Free, instant, pre-cleaned
3. **Download Kaggle Bollywood Dataset** — Free, instant

### Priority 2 — Week 1

4. **Set up TMDB API key** and begin collecting metadata for 2017–2024 movies
5. **Set up YouTube Data API key** for trailer data collection
6. **Build TMDB ↔ IMDb ID mapping table** (join key for all further work)

### Priority 3 — Week 2

7. **Build Sacnilk scraper** for Indian box-office collection data
8. **Build The Numbers scraper** for Hollywood financial data
9. **Merge and deduplicate** all sources into unified `movies` table

### Priority 4 — Week 3+

10. **Begin YouTube comment collection** for sentiment corpus
11. **Integrate Google Trends** for search interest signals
12. **Begin Rotten Tomatoes manual data collection** for top-tier films only

---

*This document will be updated as actual data collection reveals gaps or quality issues not anticipated during planning. See [16_DATA_UPDATE_AND_RETRAINING_POLICY.md](16_DATA_UPDATE_AND_RETRAINING_POLICY.md) for how data updates trigger model retraining.*
