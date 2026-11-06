# CineMetrics — Relational Database Specification & DDL Schema

**Document ID:** 18  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [Unified Dataset Design](06_UNIFIED_DATASET_DESIGN.md) | [System Architecture](17_SYSTEM_ARCHITECTURE.md) | [API Specification](19_API_SPECIFICATION.md) | [Database ERD Diagram](../diagrams/database_erd.mmd)

---

## Table of Contents

1. [Database Architectural Principles](#1-database-architectural-principles)
2. [Complete Production DDL Schema (19 Relational Entities)](#2-complete-production-ddl-schema-19-relational-entities)
   - 2.1 [Core Identity & Metadata Entities](#21-core-identity--metadata-entities)
   - 2.2 [Talent, Credits & Junction Entities](#22-talent-credits--junction-entities)
   - 2.3 [Financials, Ratings & External Signals](#23-financials-ratings--external-signals)
   - 2.4 [Digital Buzz, Trailers & Sentiment Observations](#24-digital-buzz-trailers--sentiment-observations)
   - 2.5 [Machine Learning Snapshots, Predictions & Lineage](#25-machine-learning-snapshots-predictions--lineage)
   - 2.6 [Automated Ingestion, Auditing & Change History](#26-automated-ingestion-auditing--change-history)
3. [Comprehensive Indexing Strategy](#3-comprehensive-indexing-strategy)
4. [Entity Relationships & Cardinality Directory](#4-entity-relationships--cardinality-directory)
5. [Ten Production SQL Query Patterns](#5-ten-production-sql-query-patterns)
6. [Database Tuning & Storage Sizing Recommendations](#6-database-tuning--storage-sizing-recommendations)

---

## 1. Database Architectural Principles

CineMetrics utilizes **PostgreSQL 15+** as its primary system of record. The relational design satisfies three engineering mandates:
1. **Third Normal Form (3NF) for Core Metadata**: Master entities (movies, persons, production companies) eliminate data redundancy and anomalies.
2. **Optimized Point-in-Time Snapshots (JSONB)**: High-dimensional feature matrices are stored in semi-structured JSONB columns within strictly indexed temporal snapshot tables, enabling schema evolution without destructive table alters.
3. **Immutable Audit Trails**: Historical predictions and data updates are append-only. Modifying an active forecast inserts a new version into the audit history rather than overwriting historical records.

---

## 2. Complete Production DDL Schema (19 Relational Entities)

### 2.1 Core Identity & Metadata Entities

```sql
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fast fuzzy title search

-- 1. Master Movies Table
CREATE TABLE movies (
    movie_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tmdb_id INTEGER UNIQUE,
    imdb_id VARCHAR(20) UNIQUE,
    title VARCHAR(500) NOT NULL,
    original_title VARCHAR(500),
    title_normalized VARCHAR(500) NOT NULL,
    release_date DATE,
    release_year INTEGER,
    runtime_minutes INTEGER CHECK (runtime_minutes > 0),
    original_language VARCHAR(10) NOT NULL,
    market_segment VARCHAR(50) NOT NULL, -- 'Bollywood', 'Tollywood', 'Kollywood', 'Hollywood', etc.
    status VARCHAR(50) NOT NULL DEFAULT 'announced', -- 'announced', 'production', 'imminent', 'released', 'historical'
    overview TEXT,
    tagline VARCHAR(500),
    poster_path VARCHAR(500),
    backdrop_path VARCHAR(500),
    
    -- Cinematic & structural attributes
    is_franchise BOOLEAN DEFAULT FALSE,
    is_sequel BOOLEAN DEFAULT FALSE,
    sequel_number INTEGER DEFAULT 1,
    is_remake BOOLEAN DEFAULT FALSE,
    is_pan_india BOOLEAN DEFAULT FALSE,
    
    -- Informational quality indicators
    prediction_readiness_score INTEGER DEFAULT 0 CHECK (prediction_readiness_score BETWEEN 0 AND 100),
    data_completeness_score FLOAT DEFAULT 0.0 CHECK (data_completeness_score BETWEEN 0.0 AND 1.0),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Genres Lookup Table
CREATE TABLE genres (
    genre_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- 3. Movie-Genre Junction Table
CREATE TABLE movie_genres (
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(genre_id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (movie_id, genre_id)
);

-- 4. Production Companies Table
CREATE TABLE production_companies (
    company_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tmdb_company_id INTEGER UNIQUE,
    name VARCHAR(300) NOT NULL,
    country_code VARCHAR(10),
    tier VARCHAR(50) DEFAULT 'indie', -- 'tier_1_major', 'tier_2_mid', 'indie'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Movie-Production Company Junction Table
CREATE TABLE movie_production_companies (
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES production_companies(company_id) ON DELETE CASCADE,
    is_lead_producer BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (movie_id, company_id)
);
```

### 2.2 Talent, Credits & Junction Entities

```sql
-- 6. Persons Master Table (Actors, Directors, Writers, Producers)
CREATE TABLE persons (
    person_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tmdb_person_id INTEGER UNIQUE,
    imdb_nconst VARCHAR(20) UNIQUE,
    name VARCHAR(300) NOT NULL,
    normalized_name VARCHAR(300) NOT NULL,
    gender SMALLINT DEFAULT 0, -- 0: unknown, 1: female, 2: male, 3: non-binary
    profile_path VARCHAR(500),
    primary_profession VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Movie Cast & Crew Junction Table
CREATE TABLE movie_cast (
    credit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    role_type VARCHAR(50) NOT NULL, -- 'lead_actor', 'supporting_actor', 'director', 'writer', 'producer'
    billing_order INTEGER NOT NULL DEFAULT 99,
    character_name VARCHAR(300),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_movie_person_role UNIQUE (movie_id, person_id, role_type)
);
```

### 2.3 Financials, Ratings & External Signals

```sql
-- 8. Movie Financials Table (Canonical Normalized Collections)
CREATE TABLE movie_financials (
    financial_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID UNIQUE NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    
    -- Reported nominal values in original currencies
    currency_reported VARCHAR(10) NOT NULL DEFAULT 'USD',
    production_budget_nominal NUMERIC(15, 2),
    domestic_gross_nominal NUMERIC(15, 2),
    international_gross_nominal NUMERIC(15, 2),
    worldwide_gross_nominal NUMERIC(15, 2),
    opening_day_gross_nominal NUMERIC(15, 2),
    opening_weekend_gross_nominal NUMERIC(15, 2),
    
    -- Indian-specific box-office metrics
    india_gross_inr NUMERIC(15, 2),
    india_nett_inr NUMERIC(15, 2),
    distributor_share_inr NUMERIC(15, 2),
    
    -- Real-term standardized financial metrics (2024 USD baseline)
    production_budget_real_usd NUMERIC(15, 2),
    worldwide_gross_real_usd NUMERIC(15, 2),
    cpi_deflator_used FLOAT DEFAULT 1.0,
    exchange_rate_used FLOAT DEFAULT 1.0,
    
    -- Financial audit provenance
    budget_source VARCHAR(100),
    revenue_source VARCHAR(100),
    financial_reliability_rating VARCHAR(50) DEFAULT 'reported', -- 'verified', 'reported', 'estimated', 'unconfirmed'
    is_budget_imputed BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. External Movie Ratings Table (Historical Snapshots of Third-Party Scores)
CREATE TABLE movie_ratings (
    rating_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    source_platform VARCHAR(50) NOT NULL, -- 'imdb', 'tmdb', 'metacritic', 'rotten_tomatoes'
    rating_value FLOAT NOT NULL,
    rating_max FLOAT NOT NULL DEFAULT 10.0,
    vote_count BIGINT DEFAULT 0,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.4 Digital Buzz, Trailers & Sentiment Observations

```sql
-- 10. Movie Trailers & Digital Media Table
CREATE TABLE movie_trailers (
    trailer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    youtube_video_id VARCHAR(50) NOT NULL,
    trailer_title VARCHAR(500),
    trailer_type VARCHAR(50) DEFAULT 'official_trailer', -- 'teaser', 'trailer', 'glimpse'
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    view_count_24h BIGINT,
    latest_view_count BIGINT,
    latest_like_count BIGINT,
    last_polled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. Time-Series Popularity Snapshots Table
CREATE TABLE popularity_snapshots (
    popularity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL, -- 'tmdb_popularity', 'google_trends_relative', 'youtube_velocity'
    metric_value FLOAT NOT NULL,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 12. Sentiment Observations Table (Aggregated NLP Results)
CREATE TABLE sentiment_observations (
    sentiment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL, -- e.g., 'muril_base_cased'
    sample_size INTEGER NOT NULL,
    compound_polarity FLOAT NOT NULL CHECK (compound_polarity BETWEEN -1.0 AND 1.0),
    positive_ratio FLOAT NOT NULL CHECK (positive_ratio BETWEEN 0.0 AND 1.0),
    neutral_ratio FLOAT NOT NULL,
    negative_ratio FLOAT NOT NULL,
    controversy_index FLOAT,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.5 Machine Learning Snapshots, Predictions & Lineage

```sql
-- 13. Data Sources Registry
CREATE TABLE data_sources (
    source_id VARCHAR(50) PRIMARY KEY, -- 'tmdb_api', 'imdb_tsv', 'the_numbers', 'sacnilk'
    source_name VARCHAR(200) NOT NULL,
    website_url VARCHAR(500),
    license_type VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

-- 14. Data Source Records Lineage Table
CREATE TABLE data_source_records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id VARCHAR(50) NOT NULL REFERENCES data_sources(source_id),
    target_entity VARCHAR(50) NOT NULL, -- 'movies', 'financials', 'credits'
    entity_uuid UUID NOT NULL,
    raw_payload_hash VARCHAR(64) NOT NULL,
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 15. Immutable Feature Snapshots Table
CREATE TABLE feature_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    snapshot_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    prediction_stage VARCHAR(50) NOT NULL, -- 'stage_1_6m', 'stage_2_3m', 'stage_3_1m', 'stage_4_release_day', 'stage_5_post_opening'
    days_to_release INTEGER NOT NULL,
    data_completeness_score FLOAT NOT NULL,
    feature_payload JSONB NOT NULL, -- Point-in-time engineered feature vector
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 16. Registered Model Versions Table
CREATE TABLE model_versions (
    model_version_id VARCHAR(100) PRIMARY KEY, -- e.g., 'catboost_global_v1.0.0'
    model_type VARCHAR(50) NOT NULL, -- 'gradient_boosted_trees', 'quantile_regressor'
    framework VARCHAR(50) NOT NULL, -- 'catboost', 'lightgbm'
    artifact_path VARCHAR(500) NOT NULL,
    train_cutoff_date DATE NOT NULL,
    training_sample_count INTEGER NOT NULL,
    test_smape FLOAT NOT NULL,
    test_r2 FLOAT NOT NULL,
    is_production BOOLEAN DEFAULT FALSE,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 17. Predictions Table (Active Forecasts)
CREATE TABLE predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    model_version_id VARCHAR(100) NOT NULL REFERENCES model_versions(model_version_id),
    prediction_stage VARCHAR(50) NOT NULL,
    prediction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Numerical Revenue Forecasts
    predicted_worldwide_gross_usd NUMERIC(15, 2) NOT NULL,
    predicted_worldwide_gross_inr NUMERIC(15, 2) NOT NULL,
    predicted_opening_weekend_usd NUMERIC(15, 2),
    
    -- Conformal Uncertainty Bounds
    pessimistic_gross_usd NUMERIC(15, 2) NOT NULL,
    expected_gross_usd NUMERIC(15, 2) NOT NULL,
    optimistic_gross_usd NUMERIC(15, 2) NOT NULL,
    coverage_level FLOAT DEFAULT 0.80,
    
    -- Success Classification Output
    predicted_success_category VARCHAR(50) NOT NULL,
    class_probabilities JSONB NOT NULL,
    
    -- SHAP Feature Importance Explanations
    shap_feature_importance JSONB NOT NULL,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 18. Prediction History Table (Audit Log of Forecast Drift)
CREATE TABLE prediction_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    prediction_id UUID NOT NULL REFERENCES predictions(prediction_id),
    previous_expected_gross_usd NUMERIC(15, 2),
    new_expected_gross_usd NUMERIC(15, 2),
    delta_percentage FLOAT,
    trigger_event VARCHAR(100),
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.6 Automated Ingestion, Auditing & Change History

```sql
-- 19. Ingestion Jobs & Execution Audit Table
CREATE TABLE ingestion_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(100) NOT NULL, -- 'daily_discovery', 'trailer_poll', 'post_release_sync'
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    records_discovered INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 20. Movie Change History Table (Field-Level Audit Log)
CREATE TABLE movie_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    field_modified VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    source_attribution VARCHAR(100),
    modified_by VARCHAR(100) DEFAULT 'automated_engine',
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 3. Comprehensive Indexing Strategy

```sql
-- 1. Fast Full-Text & Fuzzy Title Search
CREATE INDEX idx_movies_title_trgm ON movies USING gin (title_normalized gin_trgm_ops);
CREATE INDEX idx_movies_release_date ON movies (release_date);
CREATE INDEX idx_movies_status ON movies (status);
CREATE INDEX idx_movies_market_segment ON movies (market_segment);

-- 2. Fast Active Forecast & Dashboard Queries
CREATE INDEX idx_predictions_active_movie ON predictions (movie_id) WHERE is_active = TRUE;
CREATE INDEX idx_predictions_expected_gross ON predictions (expected_gross_usd DESC) WHERE is_active = TRUE;

-- 3. Temporal Snapshot Lookups
CREATE INDEX idx_feature_snapshots_movie_stage ON feature_snapshots (movie_id, prediction_stage);
CREATE INDEX idx_popularity_snapshots_lookup ON popularity_snapshots (movie_id, source, snapshot_date);

-- 4. Credit & Talent Graph Lookups
CREATE INDEX idx_movie_cast_person_role ON movie_cast (person_id, role_type);
CREATE INDEX idx_movie_cast_movie_billing ON movie_cast (movie_id, billing_order);
```

---

## 4. Entity Relationships & Cardinality Directory

```
MOVIES (1) ───────────────< MOVIE_CAST (M) >─────────────── (1) PERSONS
MOVIES (1) ───────────────< MOVIE_GENRES (M) >────────────── (1) GENRES
MOVIES (1) ───────────────< MOVIE_PRODUCTION_COMPANIES (M) >─ (1) PRODUCTION_COMPANIES
MOVIES (1) ───────────────|| MOVIE_FINANCIALS (1)
MOVIES (1) ───────────────< MOVIE_TRAILERS (M)
MOVIES (1) ───────────────< POPULARITY_SNAPSHOTS (M)
MOVIES (1) ───────────────< SENTIMENT_OBSERVATIONS (M)
MOVIES (1) ───────────────< FEATURE_SNAPSHOTS (M)
MOVIES (1) ───────────────< PREDICTIONS (M)
PREDICTIONS (1) ──────────< PREDICTION_HISTORY (M)
MODEL_VERSIONS (1) ───────< PREDICTIONS (M)
```

---

## 5. Ten Production SQL Query Patterns

### Query 1: Top 10 Highest Predicted Upcoming Films
```sql
SELECT m.movie_id, m.title, m.release_date, m.market_segment, m.poster_path,
       p.expected_gross_usd, p.predicted_worldwide_gross_inr, 
       p.predicted_success_category, p.pessimistic_gross_usd, p.optimistic_gross_usd
FROM movies m
JOIN predictions p ON m.movie_id = p.movie_id
WHERE p.is_active = TRUE 
  AND m.release_date >= CURRENT_DATE
ORDER BY p.expected_gross_usd DESC
LIMIT 10;
```

### Query 2: Retrieve Full Dossier with Active Prediction and Cast
```sql
SELECT m.*, f.production_budget_real_usd, f.india_gross_inr,
       p.expected_gross_usd, p.predicted_success_category, p.shap_feature_importance,
       json_agg(json_build_object('name', pers.name, 'role', mc.role_type, 'order', mc.billing_order)) AS credits
FROM movies m
LEFT JOIN movie_financials f ON m.movie_id = f.movie_id
LEFT JOIN predictions p ON m.movie_id = p.movie_id AND p.is_active = TRUE
LEFT JOIN movie_cast mc ON m.movie_id = mc.movie_id
LEFT JOIN persons pers ON mc.person_id = pers.person_id
WHERE m.movie_id = 'c1a84f32-8419-4b16-831e-436f56d81234'
GROUP BY m.movie_id, f.financial_id, p.prediction_id;
```

---

## 6. Database Tuning & Storage Sizing Recommendations

- **Storage Estimate (50,000 Movies + 5-Year History)**:
  - Tabular metadata and relational credits: $\sim 850\text{MB}$.
  - Immutable JSONB feature snapshots: $\sim 1.4\text{GB}$.
  - Total operational database footprint: $<3.0\text{GB}$ (fits completely within free-tier databases like Supabase or local PostgreSQL).
- **PostgreSQL Configuration Settings (`postgresql.conf`)**:
  - `shared_buffers = 512MB`
  - `work_mem = 16MB`
  - `maintenance_work_mem = 128MB`
  - `random_page_cost = 1.1` (SSD-optimized)
