# CineMetrics — Unified Dataset Design

> **Document version:** 1.0  
> **Status:** Planning / Pre-implementation  
> **Last updated:** 2025  
> **Maintainer:** CineMetrics Data Team  
> **Prerequisite reading:** `docs/04_DATASET_RESEARCH.md`, `docs/05_DATA_ACQUISITION_GUIDE.md`

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Canonical Movie Identity System](#2-canonical-movie-identity-system)
3. [Unified Database Schema (Full DDL)](#3-unified-database-schema-full-ddl)
4. [Financial Field Definitions](#4-financial-field-definitions)
5. [Missing Value Treatment Strategy](#5-missing-value-treatment-strategy)
6. [Schema Evolution and Versioning](#6-schema-evolution-and-versioning)
7. [Data Quality Tiers](#7-data-quality-tiers)

---

## 1. Design Philosophy

The CineMetrics unified dataset is the single source of truth from which all features, predictions, and analytics are derived. Its design principles are:

| Principle | Implementation |
|---|---|
| **Source-agnostic canonical identity** | Every movie has one internal `movie_id` (UUID); source-specific IDs are stored as attributes |
| **Full provenance** | Every row in every table can be traced to its origin source, URL, and retrieval timestamp |
| **Temporal integrity** | Features are stored with timestamps; feature extraction respects the temporal stage of prediction |
| **No data leakage** | The schema makes it structurally impossible to accidentally include post-release data in pre-release feature sets |
| **Financial clarity** | Currency, collection type (nett/gross), and territory are always documented alongside financial values |
| **Conflict transparency** | When sources disagree, all values are stored with source tags; conflicts are flagged, not silently resolved |
| **Extensibility** | New data sources can be added without altering the core schema |

---

## 2. Canonical Movie Identity System

### 2.1 Primary Key Design

Every movie in CineMetrics is assigned a **UUID (v4)** as its primary key, called `movie_id`. This internal ID is decoupled from all external source IDs, allowing source IDs to change or conflict without breaking the unified dataset.

```
movie_id  (UUID v4)
Example:  f7a2b3c4-d5e6-7f89-ab01-cd2345ef6789
```

**Why UUID and not TMDB ID?**
- TMDB IDs can be merged, split, or deleted
- Some movies exist in IMDb but not TMDB
- Future sources may have no overlap with TMDB
- UUID ensures the internal system is source-independent

### 2.2 External ID Anchoring

The **TMDB ID** serves as the primary anchor for discovery and enrichment because:
- TMDB has the best API for structured movie data
- TMDB IDs are stable and widely used in community datasets
- TMDB provides direct cross-links to IMDb (`imdb_id` field on the movie detail endpoint)

| External ID | Column | Type | Example |
|---|---|---|---|
| TMDB movie ID | `tmdb_id` | INTEGER | `1096197` |
| IMDb tconst | `imdb_id` | VARCHAR(12) | `tt15624440` |
| Kaggle TMDB dataset ID | `kaggle_tmdb_id` | INTEGER | `1096197` (usually same as TMDB) |

### 2.3 Title Normalization Rules

Titles from different sources often differ in punctuation, diacritics, and article placement. All titles are stored both in original form and in a **normalized form** for fuzzy matching.

**Normalization algorithm (described as pseudocode — to be implemented in `src/pipeline/title_normalizer.py`):**

```
function normalize_title(title: str) -> str:
    1. Convert to lowercase
    2. Remove leading/trailing whitespace
    3. Remove HTML entities (e.g., &amp; → &)
    4. Replace Unicode diacritics with ASCII equivalents
       (e.g., é → e, ñ → n, ā → a)
    5. Handle Devanagari/non-Latin scripts:
       - Keep original; also store transliterated version using
         the `indic-transliteration` library (HK scheme)
    6. Remove special characters except hyphens and spaces
       (Remove: ! ? , . : ; ( ) [ ] { } " ' ` ~ @ # $ % ^ & * + = | \ / < >)
    7. Normalize "The" prefix:
       - If title starts with "The ", move to end: "The Dark Knight" → "dark knight, the"
       - Similarly handle "A " and "An " prefix removal
    8. Collapse multiple spaces to single space
    9. Strip remaining whitespace
    
    Return normalized string
```

**Examples:**
| Original Title | Normalized |
|---|---|
| `The Dark Knight` | `dark knight, the` |
| `Baahubali: The Beginning` | `baahubali the beginning` |
| `K.G.F: Chapter 2` | `kgf chapter 2` |
| `RRR` | `rrr` |
| `Jawan` | `jawan` |
| `3 Idiots` | `3 idiots` |

**Indian title variations:**
- Many Bollywood films have both a Hindi title (Devanagari) and a romanized version
- South Indian films often release under different names in different languages
- The `title.akas` IMDb dataset contains regional alternates — use this for the normalized title lookup table

### 2.4 Cross-Source ID Resolution Strategy

**Step 1: Direct TMDB → IMDb mapping**
```
Call: GET /movie/{tmdb_id}/external_ids
Response: {"imdb_id": "tt1234567", "wikidata_id": "Q12345", ...}
```
This is the highest-confidence mapping (direct TMDB-to-IMDb link).

**Step 2: Title + Year fuzzy matching (fallback)**
When a movie has no TMDB ID (e.g., manually entered Indian film data):
```
1. Normalize source title using normalize_title()
2. Normalize release year (use ±1 tolerance for annual boundary films)
3. Search IMDb akas for normalized title match in relevant region
4. Compute Levenshtein distance ratio using rapidfuzz
5. If ratio ≥ 0.85 AND year difference ≤ 1: accept as match
6. If ratio ≥ 0.70 AND year difference = 0: flag for human review
7. If no match found: assign new UUID, leave imdb_id as NULL
```

**Step 3: Manual disambiguation**
Create `data/raw/manual_id_mappings.csv` for cases requiring human judgment:
```csv
movie_id,tmdb_id,imdb_id,resolution_method,resolved_by,resolution_date,notes
f7a2b3c4,...,tt1234567,tt2345678,manual_review,admin,2025-01-20,Two different movies with same title
```

### 2.5 Disambiguation Rules for Same-Name Movies

When two movies share a normalized title:

| Disambiguation Signal | Priority |
|---|---|
| Release year difference | High — different years = different movies |
| Original language difference | High — Hindi vs. Telugu likely different |
| Director/cast difference | Medium |
| Production company difference | Low |
| Runtime difference (>15 min) | Medium |
| IMDb ID present and distinct | Definitive |

If disambiguation is unresolvable: create separate `movie_id` entries, link them via `movie_related` table with `relationship_type = 'possible_duplicate'`.

---

## 3. Unified Database Schema (Full DDL)

The following schema is written in PostgreSQL-compatible DDL. For SQLite (development), adjust `UUID` → `TEXT` and `JSONB` → `TEXT`.

---

### 3.1 Table: `movies`

Core identity and non-financial metadata for every tracked movie.

```sql
CREATE TABLE movies (
    -- Primary key
    movie_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- External IDs
    tmdb_id             INTEGER UNIQUE,          -- TMDB movie ID; NULL if not on TMDB
    imdb_id             VARCHAR(12) UNIQUE,      -- IMDb tconst e.g. 'tt1234567'; NULL if not on IMDb
    
    -- Titles
    primary_title       VARCHAR(500) NOT NULL,   -- English title (or romanized if no English)
    original_title      VARCHAR(500),            -- Title in original language (may contain Unicode)
    normalized_title    VARCHAR(500),            -- Lowercase, diacritic-removed, article-moved; for fuzzy matching
    
    -- Language and geography
    original_language   CHAR(2),                -- ISO 639-1 language code (e.g., 'hi', 'te', 'en')
    production_countries VARCHAR(100)[],         -- Array of ISO 3166-1 country codes
    spoken_languages    VARCHAR(10)[],           -- Array of ISO 639-1 language codes
    
    -- Release information
    release_date_india  DATE,                   -- Theatrical release date in India (from TMDB IN release_dates)
    release_date_global DATE,                   -- Earliest theatrical release date anywhere
    release_date_usa    DATE,                   -- US release date (NULL for India-only releases)
    release_year        SMALLINT,               -- Extracted from release_date_global for fast filtering
    release_quarter     SMALLINT,               -- 1-4; derived from release month
    release_month       SMALLINT,               -- 1-12
    release_day_of_week SMALLINT,               -- 0=Monday ... 6=Sunday (of India release)
    
    -- Classification
    is_adult            BOOLEAN DEFAULT FALSE,
    content_rating_india VARCHAR(10),           -- Indian CBFC rating: U, UA, A, S
    content_rating_usa  VARCHAR(10),            -- MPAA rating: G, PG, PG-13, R, NC-17
    status              VARCHAR(50),            -- TMDB status: Released, Post Production, In Production, etc.
    
    -- Runtime and format
    runtime_minutes     SMALLINT,               -- Primary runtime
    is_3d               BOOLEAN,                -- Theatrical 3D release
    is_imax             BOOLEAN,                -- IMAX release
    
    -- Narrative metadata
    overview_en         TEXT,                   -- English synopsis
    tagline             VARCHAR(500),
    homepage_url        VARCHAR(500),
    
    -- Franchise and sequels
    belongs_to_collection_tmdb_id  INTEGER,     -- TMDB collection ID; NULL if standalone
    belongs_to_collection_name     VARCHAR(500),
    sequel_number       SMALLINT,               -- 1 for original, 2 for first sequel, etc.; NULL if standalone
    is_remake           BOOLEAN DEFAULT FALSE,
    is_adaptation       BOOLEAN DEFAULT FALSE,  -- Adapted from book, comic, etc.
    source_material     VARCHAR(200),           -- e.g., 'novel', 'comic', 'true story', 'remake'
    
    -- Market context
    screen_count_india  INTEGER,               -- Opening day screens (India); often unavailable
    screen_count_usa    INTEGER,               -- Opening day screens (USA)
    
    -- CineMetrics operational fields
    is_active_prediction BOOLEAN DEFAULT FALSE, -- Currently in the prediction pipeline
    prediction_stage    VARCHAR(50),            -- pre_6mo, pre_3mo, pre_1mo, pre_1wk, post_release
    data_completeness_score FLOAT,             -- 0.0-1.0 proportion of important fields populated
    
    -- Record management
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    source_priority     VARCHAR(50)            -- Which source's data takes priority for this record
);

-- Indexes
CREATE INDEX idx_movies_tmdb_id ON movies(tmdb_id);
CREATE INDEX idx_movies_imdb_id ON movies(imdb_id);
CREATE INDEX idx_movies_release_date ON movies(release_date_india);
CREATE INDEX idx_movies_original_language ON movies(original_language);
CREATE INDEX idx_movies_release_year ON movies(release_year);
CREATE INDEX idx_movies_active_prediction ON movies(is_active_prediction) WHERE is_active_prediction = TRUE;
```

---

### 3.2 Table: `movie_financials`

All financial data, with currency, collection type, territory, and source metadata for every field.

```sql
CREATE TABLE movie_financials (
    financial_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    -- Production costs
    production_budget_usd    BIGINT,           -- Reported or estimated production budget in USD
    production_budget_source VARCHAR(50),       -- e.g., 'the_numbers', 'tmdb', 'kaggle_tn', 'manual'
    production_budget_confidence VARCHAR(20),   -- 'official', 'estimated', 'rumored', 'unknown'
    marketing_budget_usd     BIGINT,           -- P&A spend (rarely available; often NULL)
    total_cost_usd           BIGINT,           -- production + marketing if both available
    
    -- Domestic (India) theatrical — Nett collections (Indian reporting standard)
    india_nett_total_inr_cr  NUMERIC(10,2),   -- Total India nett collection in INR crore
    india_nett_day1_inr_cr   NUMERIC(10,2),   -- India nett Day 1 (opening day)
    india_nett_wk1_inr_cr    NUMERIC(10,2),   -- India nett Week 1 (7 days)
    india_gross_total_inr_cr NUMERIC(10,2),   -- Total India gross (inc. GST) in INR crore
    india_financial_source   VARCHAR(100),     -- e.g., 'sacnilk', 'bollywood_hungama', 'koimoi'
    
    -- India USD equivalent (for model features)
    india_nett_total_usd     BIGINT,           -- india_nett_total_inr_cr converted to USD
    exchange_rate_inr_usd    NUMERIC(8,4),     -- Exchange rate used at time of conversion
    exchange_rate_date       DATE,              -- Date of exchange rate used
    
    -- US/Canada (domestic in Hollywood convention) — Gross collections
    domestic_gross_usd       BIGINT,           -- Total US + Canada theatrical gross in USD
    domestic_opening_usd     BIGINT,           -- Opening weekend (3-day) in US + Canada
    domestic_financial_source VARCHAR(50),      -- 'the_numbers', 'box_office_mojo', 'kaggle_tn'
    
    -- International theatrical (excluding US/Canada)
    international_gross_usd  BIGINT,           -- Total international (non-US/Canada) gross in USD
    
    -- Worldwide totals
    worldwide_gross_usd      BIGINT,           -- domestic_gross_usd + international_gross_usd
    worldwide_financial_source VARCHAR(100),    -- Source(s) used to construct this figure
    
    -- Profitability (derived)
    estimated_break_even_usd BIGINT,           -- Typically 2-2.5x production_budget_usd
    is_hit                   BOOLEAN,          -- NULL until released; TRUE if net profitable
    roi_estimate             FLOAT,            -- (worldwide_gross_usd - total_cost_usd) / total_cost_usd
    
    -- OTT / Streaming (future scope)
    ott_deal_value_inr_cr    NUMERIC(10,2),   -- OTT rights value; NULL for most films
    satellite_rights_inr_cr  NUMERIC(10,2),   -- TV rights value
    
    -- Data quality flags
    has_budget_data          BOOLEAN GENERATED ALWAYS AS (production_budget_usd IS NOT NULL) STORED,
    has_revenue_data         BOOLEAN GENERATED ALWAYS AS (worldwide_gross_usd IS NOT NULL) STORED,
    financial_data_conflicts JSONB,            -- JSON object documenting any source conflicts
    
    -- Record management
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(movie_id)   -- One financial record per movie (conflicts tracked within JSONB fields)
);

CREATE INDEX idx_financials_movie_id ON movie_financials(movie_id);
CREATE INDEX idx_financials_worldwide_gross ON movie_financials(worldwide_gross_usd) WHERE worldwide_gross_usd IS NOT NULL;
```

---

### 3.3 Table: `persons`

Actors, directors, writers, composers, and other film industry professionals.

```sql
CREATE TABLE persons (
    person_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- External IDs
    tmdb_person_id      INTEGER UNIQUE,         -- TMDB person ID
    imdb_nconst         VARCHAR(12) UNIQUE,     -- IMDb nconst e.g. 'nm0000093'
    
    -- Identity
    primary_name        VARCHAR(300) NOT NULL,  -- Most widely known name
    normalized_name     VARCHAR(300),           -- Lowercase, diacritic-removed
    birth_name          VARCHAR(300),           -- Legal birth name if different
    
    -- Biographical
    birth_year          SMALLINT,
    birth_country       CHAR(2),               -- ISO 3166-1 country of birth
    primary_language    CHAR(2),               -- Primary working language
    nationality         CHAR(2),               -- Current professional nationality
    
    -- Professional
    primary_profession  VARCHAR(50),           -- 'actor', 'director', 'producer', 'writer', 'composer'
    known_for_dept      VARCHAR(50),           -- TMDB: 'Acting', 'Directing', 'Writing', etc.
    is_deceased         BOOLEAN DEFAULT FALSE,
    death_year          SMALLINT,
    
    -- Popularity and reach
    tmdb_popularity     FLOAT,                 -- TMDB popularity score (snapshot at last update)
    tmdb_popularity_updated_at TIMESTAMPTZ,
    career_film_count   SMALLINT,              -- Total number of films worked on (approximate)
    
    -- CineMetrics-computed features (updated periodically)
    -- These are denormalized for performance; source of truth is movie_cast table
    avg_revenue_last_5_films_usd BIGINT,       -- Average worldwide gross of last 5 films as lead
    avg_revenue_last_10_films_usd BIGINT,
    hit_rate_last_10_films FLOAT,              -- % of last 10 films that were profitable
    is_a_lister         BOOLEAN,               -- Computed classification: top-tier box-office draw
    
    -- Record management
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_persons_tmdb_id ON persons(tmdb_person_id);
CREATE INDEX idx_persons_imdb_id ON persons(imdb_nconst);
CREATE INDEX idx_persons_primary_name ON persons(normalized_name);
```

---

### 3.4 Table: `movie_cast`

Junction table linking movies to persons, with role, billing order, and character data.

```sql
CREATE TABLE movie_cast (
    cast_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    person_id           UUID NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    
    -- Role classification
    role_type           VARCHAR(30) NOT NULL,  -- 'actor', 'actress', 'director', 'producer',
                                               -- 'writer', 'composer', 'cinematographer',
                                               -- 'editor', 'choreographer', 'music_director'
    department          VARCHAR(50),            -- 'Cast', 'Directing', 'Writing', 'Production', etc.
    job_title           VARCHAR(100),           -- Specific job: 'Screenplay', 'Story', 'Director', etc.
    
    -- Cast-specific fields
    character_name      VARCHAR(500),           -- Character played (NULL for crew)
    billing_order       SMALLINT,               -- 0 = top-billed; NULL for crew
    is_lead             BOOLEAN,                -- Top-3 billing order for major roles
    
    -- Data source
    source              VARCHAR(50),            -- 'tmdb_credits', 'imdb_principals'
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(movie_id, person_id, role_type, job_title)
);

CREATE INDEX idx_cast_movie_id ON movie_cast(movie_id);
CREATE INDEX idx_cast_person_id ON movie_cast(person_id);
CREATE INDEX idx_cast_role_type ON movie_cast(role_type);
CREATE INDEX idx_cast_billing_order ON movie_cast(movie_id, billing_order) WHERE billing_order IS NOT NULL;
```

---

### 3.5 Table: `genres`

Normalized genre master list (derived from TMDB genre IDs).

```sql
CREATE TABLE genres (
    genre_id            SMALLINT PRIMARY KEY,  -- TMDB genre ID (stable)
    genre_name          VARCHAR(50) NOT NULL UNIQUE,
    genre_name_hindi    VARCHAR(100),          -- Hindi name for display
    is_primary_genre    BOOLEAN DEFAULT TRUE,  -- FALSE for sub-genres not in TMDB list
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Seed data (TMDB official genre IDs as of 2024):
-- INSERT INTO genres VALUES
-- (28, 'Action', 'एक्शन', TRUE),
-- (12, 'Adventure', 'एडवेंचर', TRUE),
-- (16, 'Animation', 'एनिमेशन', TRUE),
-- (35, 'Comedy', 'कॉमेडी', TRUE),
-- (80, 'Crime', 'क्राइम', TRUE),
-- (99, 'Documentary', 'डॉक्यूमेंटरी', TRUE),
-- (18, 'Drama', 'ड्रामा', TRUE),
-- (10751, 'Family', 'फैमिली', TRUE),
-- (14, 'Fantasy', 'फैंटेसी', TRUE),
-- (36, 'History', 'इतिहास', TRUE),
-- (27, 'Horror', 'हॉरर', TRUE),
-- (10402, 'Music', 'संगीत', TRUE),
-- (9648, 'Mystery', 'रहस्य', TRUE),
-- (10749, 'Romance', 'रोमांस', TRUE),
-- (878, 'Science Fiction', 'साइंस फिक्शन', TRUE),
-- (10770, 'TV Movie', NULL, FALSE),
-- (53, 'Thriller', 'थ्रिलर', TRUE),
-- (10752, 'War', 'युद्ध', TRUE),
-- (37, 'Western', 'वेस्टर्न', FALSE);
```

---

### 3.6 Table: `movie_genres`

Junction table: movie ↔ genre (many-to-many).

```sql
CREATE TABLE movie_genres (
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    genre_id            SMALLINT NOT NULL REFERENCES genres(genre_id),
    is_primary          BOOLEAN DEFAULT FALSE,  -- First genre in TMDB list = primary
    source              VARCHAR(50) DEFAULT 'tmdb',
    
    PRIMARY KEY (movie_id, genre_id)
);

CREATE INDEX idx_movie_genres_genre ON movie_genres(genre_id);
```

---

### 3.7 Table: `production_companies`

```sql
CREATE TABLE production_companies (
    company_id          INTEGER PRIMARY KEY,    -- TMDB company ID
    company_name        VARCHAR(300) NOT NULL,
    origin_country      CHAR(2),               -- ISO 3166-1
    is_major_studio     BOOLEAN DEFAULT FALSE,  -- Flag for major studios (manual classification)
    is_indian_studio    BOOLEAN DEFAULT FALSE,  -- Flag for Indian production houses
    tmdb_logo_path      VARCHAR(500),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.8 Table: `movie_production_companies`

Junction: movie ↔ production company.

```sql
CREATE TABLE movie_production_companies (
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    company_id          INTEGER NOT NULL REFERENCES production_companies(company_id),
    is_lead_producer    BOOLEAN DEFAULT FALSE,  -- Primary production company
    source              VARCHAR(50) DEFAULT 'tmdb',
    
    PRIMARY KEY (movie_id, company_id)
);
```

---

### 3.9 Table: `movie_ratings`

External ratings from multiple sources, timestamped to enable tracking post-release rating evolution.

```sql
CREATE TABLE movie_ratings (
    rating_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    -- IMDb
    imdb_rating         NUMERIC(3,1),          -- e.g., 8.5 (scale 1-10)
    imdb_vote_count     INTEGER,
    
    -- TMDB
    tmdb_vote_average   NUMERIC(4,2),          -- scale 0-10
    tmdb_vote_count     INTEGER,
    
    -- Metacritic (critic score)
    metacritic_score    SMALLINT,              -- scale 0-100; available in IMDb Extensive Kaggle dataset
    metacritic_user_score NUMERIC(3,1),        -- scale 0-10
    
    -- Rotten Tomatoes (future enhancement — no free API)
    rt_tomatometer      SMALLINT,              -- scale 0-100; NULL for now
    rt_audience_score   SMALLINT,              -- scale 0-100; NULL for now
    
    -- Snapshot metadata (critical for leakage prevention)
    snapshot_timestamp  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    days_since_release  INTEGER,               -- NULL if pre-release
    is_pre_release      BOOLEAN GENERATED ALWAYS AS (days_since_release IS NULL OR days_since_release < 0) STORED,
    source              VARCHAR(50),
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ratings_movie_id ON movie_ratings(movie_id);
CREATE INDEX idx_ratings_snapshot ON movie_ratings(movie_id, snapshot_timestamp);
```

> [!IMPORTANT]
> `movie_ratings` stores TIMESTAMPED SNAPSHOTS of ratings. Never use the latest rating record for pre-release prediction features. Only use ratings where `snapshot_timestamp < movie.release_date_india AND days_since_release < 0`. See `docs/08_HISTORICAL_SNAPSHOT_STRATEGY.md`.

---

### 3.10 Table: `movie_trailers`

YouTube trailer metadata linked to each movie.

```sql
CREATE TABLE movie_trailers (
    trailer_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    -- YouTube identification
    youtube_video_id    VARCHAR(20) NOT NULL UNIQUE,
    youtube_channel_id  VARCHAR(30),
    youtube_channel_name VARCHAR(200),
    
    -- Trailer metadata
    trailer_type        VARCHAR(30),           -- 'trailer', 'teaser', 'clip', 'featurette'
    is_official         BOOLEAN DEFAULT TRUE,   -- From TMDB official flag
    language            CHAR(2),               -- ISO 639-1 language of the trailer
    published_at        TIMESTAMPTZ,            -- YouTube upload timestamp
    
    -- Days relative to release (computed feature)
    days_before_release SMALLINT,              -- Positive = trailer launched N days before release
    
    -- Initial statistics (at time of trailer launch, if captured)
    -- These fields are NULL if trailer was not being tracked at launch
    initial_view_count  BIGINT,
    initial_like_count  BIGINT,
    initial_comment_count INTEGER,
    initial_snapshot_at TIMESTAMPTZ,
    
    -- Source
    discovered_via      VARCHAR(30),           -- 'tmdb_videos', 'manual'
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trailers_movie_id ON movie_trailers(movie_id);
```

---

### 3.11 Table: `popularity_snapshots`

Timestamped TMDB popularity readings — the core of temporal feature tracking.

```sql
CREATE TABLE popularity_snapshots (
    snapshot_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    -- Popularity readings
    tmdb_popularity     FLOAT NOT NULL,        -- TMDB proprietary popularity score
    tmdb_vote_average   NUMERIC(4,2),
    tmdb_vote_count     INTEGER,
    
    -- Google Trends (if available for this snapshot)
    google_trends_india SMALLINT,              -- Relative interest score 0-100; NULL if not fetched
    google_trends_global SMALLINT,
    
    -- Reddit activity (if available)
    reddit_post_count_7d INTEGER,              -- Posts mentioning movie in past 7 days
    reddit_total_score_7d INTEGER,             -- Sum of scores of those posts
    
    -- Snapshot metadata
    snapshot_timestamp  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    days_to_release     INTEGER,               -- Negative = already released; 0 = release day
    prediction_stage    VARCHAR(30),           -- pre_6mo, pre_3mo, pre_1mo, pre_1wk, release_wk, post_wk1
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_popularity_movie_id ON popularity_snapshots(movie_id);
CREATE INDEX idx_popularity_timestamp ON popularity_snapshots(snapshot_timestamp);
CREATE INDEX idx_popularity_stage ON popularity_snapshots(prediction_stage);
```

---

### 3.12 Table: `sentiment_observations`

Timestamped sentiment analysis results from social and review data sources.

```sql
CREATE TABLE sentiment_observations (
    observation_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    -- Source of text
    source              VARCHAR(50) NOT NULL,  -- 'reddit_bollywood', 'reddit_movies', 'youtube_comments'
    
    -- Sentiment scores (all in range -1.0 to 1.0)
    compound_sentiment  FLOAT,                 -- Overall compound sentiment (VADER or similar)
    positive_ratio      FLOAT,                 -- Proportion of positive-scored texts
    negative_ratio      FLOAT,                 -- Proportion of negative-scored texts
    neutral_ratio       FLOAT,                 -- Proportion of neutral-scored texts
    
    -- Volume of texts analyzed
    text_count          INTEGER NOT NULL,
    
    -- Observation metadata
    observation_window_start TIMESTAMPTZ,      -- Start of text collection window
    observation_window_end   TIMESTAMPTZ,      -- End of text collection window
    observation_timestamp    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    days_to_release     INTEGER,
    prediction_stage    VARCHAR(30),
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sentiment_movie_id ON sentiment_observations(movie_id);
CREATE INDEX idx_sentiment_timestamp ON sentiment_observations(observation_timestamp);
```

---

### 3.13 Table: `data_sources`

Registry of all data sources used in the system.

```sql
CREATE TABLE data_sources (
    source_id           VARCHAR(50) PRIMARY KEY, -- Slug: 'tmdb_api', 'imdb_bulk', 'kaggle_tmdb5000'
    source_name         VARCHAR(200) NOT NULL,
    source_type         VARCHAR(30) NOT NULL,    -- 'api', 'bulk_download', 'kaggle', 'manual', 'scraped'
    base_url            VARCHAR(500),
    documentation_url   VARCHAR(500),
    license             VARCHAR(100),            -- 'CC0', 'CC-BY', 'tmdb-noncommercial', 'imdb-noncommercial'
    attribution_required BOOLEAN DEFAULT TRUE,
    attribution_text    TEXT,
    cost                VARCHAR(50),             -- 'free', 'free-quota', 'paid'
    access_method       VARCHAR(100),            -- 'api_key', 'oauth', 'direct_download', 'manual'
    covers_indian_cinema BOOLEAN DEFAULT FALSE,
    covers_financial_data BOOLEAN DEFAULT FALSE,
    reliability_tier    SMALLINT,               -- 1=highest, 2=medium, 3=lowest/unverified
    is_active           BOOLEAN DEFAULT TRUE,
    notes               TEXT,
    added_at            TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.14 Table: `data_source_records`

Provenance for every data point — links raw records to their source.

```sql
CREATE TABLE data_source_records (
    record_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- What data this provenance record covers
    target_table        VARCHAR(100) NOT NULL,  -- e.g., 'movies', 'movie_financials'
    target_id           UUID NOT NULL,          -- The movie_id, financial_id, etc.
    target_column       VARCHAR(100),           -- Specific column; NULL = entire row
    
    -- Source details
    source_id           VARCHAR(50) NOT NULL REFERENCES data_sources(source_id),
    source_record_id    VARCHAR(200),           -- Source's own ID for this record (e.g., TMDB movie ID)
    endpoint_or_path    VARCHAR(500),           -- Full URL or file path
    
    -- Retrieval metadata
    retrieval_timestamp TIMESTAMPTZ NOT NULL,
    schema_version      VARCHAR(20),
    
    -- Data quality
    confidence          VARCHAR(20),            -- 'official', 'estimated', 'rumored', 'community'
    has_conflicts       BOOLEAN DEFAULT FALSE,  -- TRUE if other sources disagree
    conflict_details    JSONB,                  -- JSON object with conflicting values and sources
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_provenance_target ON data_source_records(target_table, target_id);
CREATE INDEX idx_provenance_source ON data_source_records(source_id);
CREATE INDEX idx_provenance_timestamp ON data_source_records(retrieval_timestamp);
```

---

### 3.15 Table: `feature_snapshots`

Timestamped feature vectors — the core of leakage-free prediction. See `docs/08_HISTORICAL_SNAPSHOT_STRATEGY.md` for full context.

```sql
CREATE TABLE feature_snapshots (
    snapshot_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    -- When this snapshot was taken
    snapshot_timestamp  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Prediction stage at time of snapshot
    prediction_stage    VARCHAR(30) NOT NULL,   -- pre_6mo, pre_3mo, pre_1mo, pre_1wk, release_wk
    
    -- Days relative to release at snapshot time
    days_to_release     INTEGER,               -- Positive = before release
    
    -- Feature availability at snapshot time
    features_available  JSONB NOT NULL,        -- {"budget": true, "cast": true, "trailer_views": false}
    
    -- The actual feature values at this point in time
    feature_values      JSONB NOT NULL,        -- Full feature dictionary
    
    -- Data completeness
    data_completeness_score FLOAT,            -- 0.0-1.0
    missing_critical_features TEXT[],          -- Names of critical features that are NULL
    
    -- Model this snapshot was used for
    model_version_id    UUID,                  -- References model_versions; NULL if not yet used
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feature_snapshots_movie ON feature_snapshots(movie_id);
CREATE INDEX idx_feature_snapshots_stage ON feature_snapshots(prediction_stage);
CREATE INDEX idx_feature_snapshots_timestamp ON feature_snapshots(snapshot_timestamp);
```

---

### 3.16 Table: `predictions`

All revenue predictions generated by CineMetrics models.

```sql
CREATE TABLE predictions (
    prediction_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id            UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    -- Model and snapshot reference
    model_version_id    UUID NOT NULL,          -- References model_versions
    feature_snapshot_id UUID REFERENCES feature_snapshots(snapshot_id),
    
    -- Prediction context
    prediction_stage    VARCHAR(30) NOT NULL,
    prediction_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    days_to_release_at_prediction INTEGER,
    
    -- Revenue predictions (all in USD)
    -- Point estimates
    predicted_worldwide_gross_usd   BIGINT,
    predicted_india_nett_inr_cr     NUMERIC(10,2),
    predicted_domestic_usa_gross_usd BIGINT,
    predicted_opening_weekend_usd   BIGINT,
    
    -- Uncertainty quantification
    prediction_interval_lower_usd   BIGINT,     -- 80% PI lower bound (worldwide gross)
    prediction_interval_upper_usd   BIGINT,     -- 80% PI upper bound
    confidence_interval_90_lower_usd BIGINT,    -- 90% CI lower bound
    confidence_interval_90_upper_usd BIGINT,
    prediction_confidence_score     FLOAT,      -- 0.0-1.0 overall confidence
    
    -- Classification prediction
    predicted_hit_flop_class        VARCHAR(30), -- 'blockbuster', 'hit', 'above_average', 'average', 'flop'
    hit_flop_probability            JSONB,       -- {"blockbuster": 0.3, "hit": 0.4, "above_average": 0.2, ...}
    
    -- Actual outcomes (populated after release)
    actual_worldwide_gross_usd      BIGINT,
    actual_india_nett_inr_cr        NUMERIC(10,2),
    actual_hit_flop_class           VARCHAR(30),
    outcome_recorded_at             TIMESTAMPTZ,
    
    -- Prediction accuracy (computed after outcome known)
    absolute_error_usd              BIGINT,     -- |predicted - actual|
    absolute_percentage_error       FLOAT,      -- |predicted - actual| / actual
    is_correct_class                BOOLEAN,    -- Whether hit/flop classification was correct
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_movie_id ON predictions(movie_id);
CREATE INDEX idx_predictions_model ON predictions(model_version_id);
CREATE INDEX idx_predictions_stage ON predictions(prediction_stage);
CREATE INDEX idx_predictions_timestamp ON predictions(prediction_timestamp);
```

---

### 3.17 Table: `prediction_history`

Change tracking for predictions — records every update to a prediction so trends can be shown.

```sql
CREATE TABLE prediction_history (
    history_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id       UUID NOT NULL REFERENCES predictions(prediction_id) ON DELETE CASCADE,
    movie_id            UUID NOT NULL,
    
    -- The previous prediction values (before this update)
    previous_predicted_worldwide_usd BIGINT,
    previous_hit_flop_class          VARCHAR(30),
    previous_confidence              FLOAT,
    
    -- The updated values
    updated_predicted_worldwide_usd  BIGINT,
    updated_hit_flop_class           VARCHAR(30),
    updated_confidence               FLOAT,
    
    -- Change metadata
    change_reason       VARCHAR(200),           -- e.g., 'trailer_views_updated', 'budget_confirmed'
    prediction_stage    VARCHAR(30),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pred_history_prediction ON prediction_history(prediction_id);
CREATE INDEX idx_pred_history_movie ON prediction_history(movie_id);
```

---

### 3.18 Table: `model_versions`

Model registry for all trained prediction models.

```sql
CREATE TABLE model_versions (
    model_version_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identification
    model_name          VARCHAR(100) NOT NULL,  -- e.g., 'revenue_predictor_v1', 'hit_flop_classifier_v2'
    model_version        VARCHAR(20) NOT NULL,  -- Semantic version e.g., '1.0.0', '2.3.1'
    model_type          VARCHAR(50),            -- 'xgboost', 'lightgbm', 'random_forest', 'linear', 'ensemble'
    prediction_target   VARCHAR(50),            -- 'worldwide_gross_usd', 'hit_flop_class', 'india_nett'
    prediction_stage    VARCHAR(30),            -- Stage this model is designed for
    
    -- Training metadata
    training_started_at TIMESTAMPTZ,
    training_completed_at TIMESTAMPTZ,
    training_dataset_version VARCHAR(50),      -- DVC tag or hash of training dataset
    training_movie_count INTEGER,              -- Number of movies in training set
    training_year_range  VARCHAR(20),          -- e.g., '2000-2023'
    language_coverage   VARCHAR(100)[],        -- Languages included: ['hi', 'te', 'en']
    
    -- Feature configuration
    feature_list        TEXT[],                -- Ordered list of feature names used
    feature_count       INTEGER,
    target_column       VARCHAR(100),
    
    -- Performance metrics (on held-out test set)
    test_rmse_usd       BIGINT,
    test_mae_usd        BIGINT,
    test_mape           FLOAT,                 -- Mean Absolute Percentage Error
    test_r2             FLOAT,                 -- R-squared
    test_accuracy_hit_flop FLOAT,              -- Classification accuracy if applicable
    test_movie_count    INTEGER,
    
    -- Deployment
    is_active           BOOLEAN DEFAULT FALSE, -- Only one model per stage should be active
    deployed_at         TIMESTAMPTZ,
    artifact_path       VARCHAR(500),          -- Path to serialized model file
    
    -- Notes
    description         TEXT,
    training_notes      TEXT,
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_model_versions_active ON model_versions(is_active, prediction_stage) WHERE is_active = TRUE;
```

---

### 3.19 Table: `ingestion_jobs`

Scheduled data acquisition and pipeline job tracking.

```sql
CREATE TABLE ingestion_jobs (
    job_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Job definition
    job_name            VARCHAR(100) NOT NULL,  -- e.g., 'tmdb_upcoming_refresh', 'imdb_bulk_weekly'
    job_type            VARCHAR(50) NOT NULL,   -- 'acquisition', 'processing', 'feature_engineering', 'prediction'
    source              VARCHAR(50),
    
    -- Execution
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    duration_seconds    FLOAT,
    status              VARCHAR(30) NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed', 'partial'
    
    -- Results
    records_fetched     INTEGER,
    records_processed   INTEGER,
    records_failed      INTEGER,
    new_movies_added    INTEGER,
    movies_updated      INTEGER,
    
    -- Error tracking
    error_message       TEXT,
    error_stack_trace   TEXT,
    
    -- Configuration at time of run
    job_config          JSONB,
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON ingestion_jobs(status, started_at);
CREATE INDEX idx_jobs_name ON ingestion_jobs(job_name, started_at);
```

---

## 4. Financial Field Definitions

The following definitions are canonical for CineMetrics. All code, documentation, and UI must use these terms consistently.

### 4.1 Revenue Field Definitions

| Field | Canonical Definition |
|---|---|
| `worldwide_gross_usd` | **Total theatrical ticket revenue globally**, combining domestic (US+Canada) and international gross. Denominated in USD at prevailing rate at time of reporting. Does NOT include OTT, home video, merchandise, music rights, satellite rights, or any ancillary revenue. This is the primary ML target variable. |
| `domestic_gross_usd` | Total theatrical ticket sales in the **United States and Canada only**. This is the Hollywood/Western convention for "domestic". Note: for Indian films, "domestic" in Indian trade reporting means India, not US. CineMetrics always uses the US+Canada definition for `domestic_gross_usd` and uses `india_nett_total_inr_cr` or `india_nett_total_usd` for Indian domestic. |
| `international_gross_usd` | Worldwide gross minus domestic (US+Canada) gross. All theatrical ticket revenue outside the US and Canada. Includes India, UK, Australia, Southeast Asia, Middle East, etc. |
| `india_nett_total_inr_cr` | Total India theatrical nett collection in Indian Rupees (crore). **Nett = gross minus GST/entertainment tax**. This is the Indian trade standard reporting figure. Currently GST is 18% on tickets above ₹100 (as of knowledge cutoff). |
| `india_gross_total_inr_cr` | Total India theatrical gross collection in INR crore. Gross includes GST. Rarely reported in Indian trade media; prefer nett. |
| `india_nett_total_usd` | `india_nett_total_inr_cr` converted to USD using the exchange rate on the film's collection reporting date. |
| `production_budget_usd` | Reported or estimated cost of **producing the film** — including cast fees, crew, sets, VFX, music production, and post-production. Does NOT include marketing/P&A (prints and advertising) unless explicitly stated. |
| `marketing_budget_usd` | Cost of marketing (theatrical advertising, print costs, digital marketing, promotional events). Rarely disclosed. Industry rule of thumb: approximately 50–100% of production budget for Hollywood; 30–50% for Indian films. |
| `total_cost_usd` | `production_budget_usd` + `marketing_budget_usd` when both are available. The true break-even threshold is approximately 2–2.5× `production_budget_usd` (accounting for distributor share and marketing). |
| `domestic_opening_usd` | Opening **weekend** (3-day: Friday + Saturday + Sunday) gross in US + Canada. For Indian films reporting, opening day (`Day 1`) is more commonly reported than 3-day opening weekend. |

### 4.2 Source Priority Order for Revenue Labels

When multiple sources provide revenue figures, use this priority:

```
Priority 1: The Numbers (via Kaggle extract)
   — Most reliable for Hollywood; professionally maintained
   — Covers worldwide_gross_usd, domestic_gross_usd, production_budget_usd

Priority 2: TMDB revenue field (non-zero values only)
   — Community-maintained; reliable when present
   — Covers worldwide_gross_usd approximation

Priority 3: Kaggle datasets (The Movies Dataset, IMDb Extensive)
   — Cross-reference and supplement only
   — Lower reliability; treat as confirming evidence

Priority 4: Sacnilk / Bollywood Hungama / Koimoi (Indian films)
   — Manual entry; covers india_nett_total_inr_cr
   — Mark confidence = community

Priority 5: IMDb website data (via IMDb Extensive Kaggle dataset)
   — Not in official bulk dataset but captured in community Kaggle datasets
   — Cross-reference only
```

### 4.3 Conflict Resolution Rules

When two sources provide different values for the same financial field:

| Scenario | Resolution |
|---|---|
| Difference < 5% | Accept higher-priority source silently |
| Difference 5–20% | Accept higher-priority source; log conflict in `financial_data_conflicts` JSONB |
| Difference > 20% | Flag for manual review; store both values with source tags; use higher-priority source as `canonical` |
| One source says 0, other says non-zero | Non-zero value wins (0 usually means data not entered, not actual zero revenue) |
| Budget from TMDB = 0 | Treat as NULL (TMDB returns 0 for missing budgets) |

### 4.4 Currency Handling

All financial fields in the main schema are in USD. Original currency values are preserved:

```sql
-- Pattern: store both original and converted
india_nett_total_inr_cr     NUMERIC(10,2),   -- Original INR crore
india_nett_total_usd        BIGINT,           -- Converted USD
exchange_rate_inr_usd       NUMERIC(8,4),     -- Rate used for conversion
exchange_rate_date          DATE,             -- Date of rate (use collection date, not today)
```

**Exchange rate source:** Use `exchangerate.host` free API or static annual average rates from Reserve Bank of India (RBI) historical data. Document which approach is used in `config/data_sources.yaml`.

---

## 5. Missing Value Treatment Strategy

### 5.1 Field-Level Missing Value Policy

| Field | Null Rate (Estimated) | Strategy | Rationale |
|---|---|---|---|
| `production_budget_usd` | ~60% | **Flag-and-model** — use a separate "has_budget" binary feature; never impute target-correlated field | Budget is highly correlated with revenue; imputation would introduce bias |
| `worldwide_gross_usd` | ~40% | **Drop from training** — this IS the target variable; rows with null target are excluded from supervised training | Never impute target |
| `india_nett_total_inr_cr` | ~70% | **Drop Indian target rows with null** — cannot impute revenue | Never impute target |
| `runtime_minutes` | ~10% | **Median imputation** by language + genre combination | Runtime weakly correlated with performance; safe to impute |
| `release_date_india` | ~20% | **Derive from release_date_global** ± expected India lag; flag imputed cases | India release typically same day or within 2 weeks of global |
| `imdb_id` | ~15% | **Leave NULL** — attempt ID resolution via title+year match; mark unresolved | Cannot fabricate external IDs |
| `tmdb_vote_average` | ~25% (pre-release) | **Leave NULL** — this is a post-release metric and should not be used in pre-release features | Explicitly excluded from pre-release feature set |
| `tmdb_vote_count` | ~25% (pre-release) | **Leave NULL** — same as above | Explicitly excluded from pre-release feature set |
| `content_rating_india` | ~40% | **Mode imputation by language** (Hindi films most commonly 'UA') + "Unknown" category | Weak predictor; imputation risk low |
| `belongs_to_collection_name` | ~65% | **Leave NULL** — convert to binary `is_sequel` feature; NULL = standalone | Franchise membership is binary feature |
| `screen_count_india` | ~80% | **Leave NULL** — not reliably available; exclude from features | Cannot reliably impute screen count |
| `overview_en` | ~5% | **Leave NULL** — NLP features degrade gracefully without text | Text features handle missing via zero-vector |
| `tmdb_popularity` | ~0% | **No imputation needed** — always present on TMDB | Very rarely missing |
| `original_language` | ~2% | **Mode imputation from production company** + "unknown" category | Usually determinable from other metadata |
| `release_quarter` | ~20% | **Derive from available release_date fields** | Directly computable |
| `is_sequel` | ~0% (derived) | **Derive from belongs_to_collection + sequel_number** | Always computable from available data |
| `director person_id` | ~5% | **Leave NULL** — crew sometimes incompletely documented in TMDB | Mark as "unknown_director" category |
| `google_trends_india` | ~40% | **Leave NULL for historical; impute 0 for new movies not yet searched** | Trends of 0 meaning "not searched" is distinct from "missing" |
| `youtube_view_count_at_1wk` | ~30% | **Leave NULL** — only available for movies where trailer was captured on time | Cannot reconstruct historical view counts |

### 5.2 Critical Rule: Never Impute Target Variables

> [!CAUTION]
> The following fields are **target variables** (what we are predicting). They must NEVER be imputed, interpolated, or estimated for training data. Rows with NULL target variables are excluded from the supervised training set entirely.
>
> - `worldwide_gross_usd`
> - `india_nett_total_inr_cr`
> - `domestic_gross_usd`
> - `is_hit`
> - `predicted_hit_flop_class` (the actual label)

### 5.3 Pre-Release vs. Post-Release Feature Handling

The missing value strategy differs by prediction stage:

| Feature Category | Pre-Release Stage | Post-Release Stage |
|---|---|---|
| Cast/crew features | Available (announced) | Available |
| Genre features | Available | Available |
| Budget features | Often available | Usually available |
| IMDb rating | **NOT available — exclude** | Available (leakage risk if used in pre-release) |
| IMDb vote count | **NOT available — exclude** | Available |
| Trailer view count | Available (from launch date) | Available |
| Revenue (target) | **NULL — exclude from training** | Available (labels for training) |
| Week 1 gross | **NULL — this IS what we predict** | Available |

---

## 6. Schema Evolution and Versioning

### 6.1 Schema Version Tracking

All schema changes are tracked in `schema_migrations/` with numbered migration files:

```
schema_migrations/
├── 001_initial_schema.sql
├── 002_add_ott_fields.sql
├── 003_add_sentiment_tables.sql
└── migration_log.json
```

### 6.2 Backward Compatibility Rules

- Never drop columns without a deprecation migration period of at least 2 versions
- Always add new columns as NULLABLE to avoid breaking existing inserts
- JSON/JSONB fields (`feature_values`, `hit_flop_probability`) absorb new sub-fields without schema changes
- Bump `schema_version` in provenance records whenever schema changes affect data interpretation

---

## 7. Data Quality Tiers

Every movie in the dataset is assigned a data quality tier based on feature completeness:

| Tier | Name | Criteria | Usability |
|---|---|---|---|
| **Tier 1** | Gold | Has budget + revenue + cast + director + genre + release_date + imdb_id. Financial data from The Numbers or confirmed TMDB. | Full ML training use |
| **Tier 2** | Silver | Has revenue + cast + director + genre + release_date. Budget may be missing. At least one financial source. | ML training (budget-agnostic features) |
| **Tier 3** | Bronze | Has genre + release_date + cast or director. No verified revenue. | Feature engineering research; not used as training label |
| **Tier 4** | Stub | Has title + release_date only. All other fields missing or unverified. | In prediction queue; not used for training |

**Quality tier computation:**

```python
def compute_data_quality_tier(movie: dict) -> int:
    """
    Compute CineMetrics data quality tier (1-4) for a movie record.
    
    Returns:
        int: 1=Gold, 2=Silver, 3=Bronze, 4=Stub
    """
    has_verified_revenue = (
        movie.get("worldwide_gross_usd") is not None and
        movie.get("worldwide_gross_usd", 0) > 0
    )
    has_budget = movie.get("production_budget_usd") is not None
    has_cast = len(movie.get("cast", [])) >= 1
    has_director = movie.get("director_person_id") is not None
    has_genre = len(movie.get("genres", [])) >= 1
    has_release_date = movie.get("release_date_global") is not None
    has_imdb_id = movie.get("imdb_id") is not None
    
    if has_verified_revenue and has_budget and has_cast and has_director and has_genre and has_release_date and has_imdb_id:
        return 1  # Gold
    elif has_verified_revenue and has_cast and has_director and has_genre and has_release_date:
        return 2  # Silver
    elif has_genre and has_release_date and (has_cast or has_director):
        return 3  # Bronze
    else:
        return 4  # Stub
```

---

*This schema design document is authoritative for all CineMetrics database implementation. Any changes to table structures, column names, or financial definitions must be reflected here before implementation. Cross-reference with `docs/07_DATA_ENGINEERING_PIPELINE.md` for the pipeline that populates these tables.*
