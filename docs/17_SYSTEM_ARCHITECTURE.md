# CineMetrics — Complete System Architecture Blueprint

**Document ID:** 17  
**Version:** 1.0  
**Status:** Approved System Architecture Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [Product Modes & User Flows](03_PRODUCT_MODES_AND_USER_FLOWS.md) | [Database & ERD](18_DATABASE_AND_ER_DIAGRAM.md) | [API Specification](19_API_SPECIFICATION.md) | [System Architecture Diagram](../diagrams/system_architecture.mmd)

---

## Table of Contents

1. [Architectural Philosophy: The Pragmatic Modular Monolith](#1-architectural-philosophy-the-pragmatic-modular-monolith)
2. [High-Level System Topology](#2-high-level-system-topology)
3. [Complete Technology Stack](#3-complete-technology-stack)
4. [Comprehensive Repository & Directory Structure](#4-comprehensive-repository--directory-structure)
5. [Subsystem Specifications & Internal Boundaries](#5-subsystem-specifications--internal-boundaries)
   - 5.1 [Presentation Layer (React + Vite + TypeScript)](#51-presentation-layer-react--vite--typescript)
   - 5.2 [API & Application Service Layer (FastAPI)](#52-api--application-service-layer-fastapi)
   - 5.3 [Machine Learning Serving & Inference Layer](#53-machine-learning-serving--inference-layer)
   - 5.4 [Data Engineering & Ingestion Worker Subsystem](#54-data-engineering--ingestion-worker-subsystem)
   - 5.5 [Persistence & Analytical Storage Layer](#55-persistence--analytical-storage-layer)
6. [Component Inter-Communication Protocols](#6-component-inter-communication-protocols)
7. [End-to-End Runtime Data Flow Scenarios](#7-end-to-end-runtime-data-flow-scenarios)
8. [Cross-Cutting Concerns: Caching, Observability & Error Handling](#8-cross-cutting-concerns-caching-observability--error-handling)

---

## 1. Architectural Philosophy: The Pragmatic Modular Monolith

CineMetrics intentionally rejects the unnecessary operational overhead of microservices architectures (service discovery, distributed transactions, gRPC networking, container mesh orchestration). For a data science / machine learning platform developed by an ambitious student developer, distributed microservices introduce massive devops friction without tangible business benefits.

Instead, CineMetrics adopts a **Pragmatic Modular Monolith**:
- **Single Deployable Unit**: The core backend application, ML model inference, and background discovery schedulers execute within a single coordinated Python process tree.
- **Strict In-Process Decoupling**: Code modules (`api`, `services`, `ml`, `jobs`, `db`) maintain clean interfaces. Business logic never executes raw database queries directly; API controllers never interact directly with ML model internals.
- **Shared In-Memory Efficiency**: Machine learning models and feature lookups reside directly in the memory space of the ASGI worker process, eliminating network serialization latency and achieving $<50\text{ms}$ inference response times.

---

## 2. High-Level System Topology

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               USER CLIENT LAYER                                  │
│             React 18 SPA (TypeScript + Vite + Tailwind CSS + Framer)             │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ HTTPS / JSON REST
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION BACKEND                             │
│                                                                                  │
│   ┌─────────────────────┐   ┌──────────────────────┐   ┌─────────────────────┐  │
│   │   REST API Router   │   │  Application Services│   │   APScheduler Jobs  │  │
│   │  (/api/v1/movies,   │──►│  (PredictionService, │◄──│  (Daily Discovery,  │  │
│   │   /upcoming, etc.)  │   │   EnrichmentService) │   │   Enrichment Queue) │  │
│   └─────────────────────┘   └──────────┬───────────┘   └──────────┬──────────┘  │
│                                        │                          │             │
│   ┌────────────────────────────────────┼──────────────────────────┼──────────┐  │
│   │ IN-PROCESS ML ENGINE               ▼                          ▼          │  │
│   │ • CatBoost Global Regressor (.cbm) ◄───────────────┐                     │  │
│   │ • CatBoost Classifier (Success Tier)                │                     │  │
│   │ • TreeSHAP Explainer (In-Memory)                    │                     │  │
│   │ • MAPIE Conformal Uncertainty Bands                 │                     │  │
│   └─────────────────────────────────────────────────────┼─────────────────────┘  │
│                                                         │                        │
└─────────────────────────────────────────────────────────┼────────────────────────┘
                                                          │
                                     ┌────────────────────┴────────────────────┐
                                     ▼                                         ▼
┌──────────────────────────────────────────────┐  ┌────────────────────────────────┐
│           PRIMARY RELATIONAL STORE           │  │       ANALYTICAL LAKE STORE    │
│            PostgreSQL 15+ Instance           │  │      DuckDB + Apache Parquet   │
│  - Canonical Movies, Persons, Credits        │  │  - Raw Multi-Source Bronze     │
│  - Immutable Feature Snapshots (JSONB)       │  │  - Gold Training/Val/Test Sets │
│  - Active Predictions & Audit History        │  │  - Historical Financial Dumps  │
└──────────────────────────────────────────────┘  └────────────────────────────────┘
```

---

## 3. Complete Technology Stack

| Layer | Component | Selected Technology | Version | Architectural Justification |
|---|---|---|---|---|
| **Frontend** | Framework | React + TypeScript | 18.2+ | Component ecosystem, strict typing, high performance. |
| | Build Tool | Vite | 5.0+ | Instant hot-module replacement, optimized Rollup bundle. |
| | Styling | Tailwind CSS | 3.4+ | Utility-first, zero runtime CSS overhead, dark theme system. |
| | Micro-Interactions | Framer Motion | 11.0+ | Physics-based spring animations for cinematic feel. |
| | Visualization | Recharts + Lucide Icons | 2.12+ | Declarative SVG charting for SHAP waterfalls and intervals. |
| | State Management | Zustand + TanStack Query | 4.5+ / 5.0+ | Lightweight client state + powerful async cache/revalidation. |
| **Backend** | Web Framework | FastAPI | 0.110+ | High-throughput asynchronous ASGI, automatic OpenAPI docs. |
| | App Server | Uvicorn (uvloop) | 0.28+ | High-performance async event loop. |
| | Validation | Pydantic v2 | 2.6+ | Rust-backed blazing-fast data validation & serialization. |
| | ORM & Migrations | SQLAlchemy 2.0 + Alembic | 2.0+ / 1.13+ | Modern typed async relational mapping and schema migrations. |
| | Scheduling | APScheduler | 3.10+ | Lightweight in-process cron and interval task scheduling. |
| **Machine Learning**| Primary GBDT | CatBoost | 1.2+ | Native target statistics for categorical features, TreeSHAP. |
| | Secondary GBDT | LightGBM / XGBoost | 4.3+ / 2.0+ | Fast secondary benchmarking and ensemble validation. |
| | Explainability | SHAP (TreeSHAP) | 0.45+ | Exact additive feature attributions in polynomial time. |
| | Uncertainty | MAPIE | 0.8+ | Conformal prediction intervals with formal coverage guarantees. |
| | Tuning | Optuna | 3.5+ | Bayesian TPE hyperparameter optimization. |
| | Tracking | MLflow (Local Server) | 2.11+ | Zero-cost experiment logging and model artifact versioning. |
| | NLP Sentiment | Google MuRIL via HuggingFace | Transformers 4.38+ | Romanized Indic and code-mixed (Hinglish) understanding. |
| **Data & Storage** | Relational DB | PostgreSQL | 15.0+ | ACID transactions, JSONB indexing, robust geospatial/text search. |
| | Columnar Storage | Apache Parquet (Snappy) | PyArrow 15.0+ | High-compression analytical storage for training matrices. |
| | In-Process SQL | DuckDB | 0.10+ | Direct SQL execution over Parquet without database setup. |

---

## 4. Comprehensive Repository & Directory Structure

```
CineMetrics/
├── .gitignore                          # Strict gitignore covering secrets, data, and models
├── README.md                           # Master architectural overview and setup guide
│
├── docs/                               # 29 Technical Planning & Architecture Specifications
│   ├── 00_INDEX.md
│   ├── 01_PROJECT_VISION.md
│   ├── ...
│   └── 29_ACCEPTANCE_CRITERIA.md
│
├── diagrams/                           # 7 Mermaid System & Workflow Diagrams
│   ├── system_architecture.mmd
│   ├── data_pipeline.mmd
│   ├── automated_discovery.mmd
│   ├── ml_training_pipeline.mmd
│   ├── prediction_lifecycle.mmd
│   ├── database_erd.mmd
│   └── application_flow.mmd
│
├── planning/                           # 12 Operational Tracking Matrices
│   ├── DATASET_TRACKER.md
│   ├── FEATURE_DICTIONARY.md
│   └── ...
│
├── data/                               # Local Data Lake (Completely Gitignored)
│   ├── raw/                            # Bronze: Unmodified API JSONs and TSV dumps
│   ├── processed/                      # Silver: Conformed and deduplicated data
│   ├── unified/                        # Canonical unified master tables
│   └── snapshots/                      # Gold: Historical training/val/test splits
│
├── backend/                            # FastAPI Application Package
│   ├── app/
│   │   ├── main.py                     # ASGI entrypoint & lifespan lifecycle hooks
│   │   ├── config.py                   # Pydantic BaseSettings loading from .env
│   │   ├── database.py                 # Async SQLAlchemy session factory & engine
│   │   │
│   │   ├── models/                     # SQLAlchemy 2.0 Declarative Relational Models
│   │   │   ├── movie.py                # movies, movie_financials, aliases
│   │   │   ├── talent.py               # persons, movie_cast, crew
│   │   │   ├── prediction.py           # predictions, prediction_history
│   │   │   ├── snapshot.py             # feature_snapshots, popularity_snapshots
│   │   │   └── ingestion.py            # ingestion_jobs, movie_history
│   │   │
│   │   ├── schemas/                    # Pydantic v2 Request & Response Contracts
│   │   │   ├── movie_schemas.py
│   │   │   ├── prediction_schemas.py
│   │   │   ├── simulation_schemas.py
│   │   │   └── admin_schemas.py
│   │   │
│   │   ├── api/                        # REST API Router Endpoints
│   │   │   ├── v1/
│   │   │   │   ├── router.py           # Master aggregated router (/api/v1)
│   │   │   │   ├── movies.py           # Search, movie details, catalog
│   │   │   │   ├── upcoming.py         # Dashboard sections, upcoming feeds
│   │   │   │   ├── predictions.py      # Active forecast, SHAP waterfall, history
│   │   │   │   ├── simulations.py      # What-If counterfactual scenario engine
│   │   │   │   ├── analytics.py        # Market trends, actor/director dossiers
│   │   │   │   └── admin.py            # Ingestion controls, manual curation
│   │   │
│   │   ├── services/                   # Encapsulated Business Logic Services
│   │   │   ├── movie_service.py        # Movie querying and entity assembly
│   │   │   ├── prediction_service.py   # Forecast coordination & interval assembly
│   │   │   ├── enrichment_service.py   # External API multi-source data gathering
│   │   │   ├── sentiment_service.py    # Text batch processing & polarity scoring
│   │   │   └── simulation_service.py   # What-If in-memory feature perturbation
│   │   │
│   │   └── ml/                         # In-Process Machine Learning Runtime
│   │       ├── model_loader.py         # Singleton loading CatBoost/SHAP at startup
│   │       ├── predictor.py            # Forward inference & milestone prediction
│   │       ├── explainer.py            # Local TreeSHAP waterfall generation
│   │       └── uncertainty.py          # Conformal prediction interval calculations
│   │
│   ├── jobs/                           # Background Tasks & Schedulers
│   │   ├── scheduler.py                # APScheduler configuration & worker loop
│   │   ├── discovery_job.py            # Daily TMDB upcoming scan & entity ingest
│   │   ├── buzz_update_job.py          # Daily YouTube & Trends popularity poll
│   │   └── post_release_job.py         # Actuals collection for recently released films
│   │
│   ├── migrations/                     # Alembic Schema Migrations
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── tests/                          # Backend Pytest Suite
│   └── requirements.txt                # Python backend dependencies
│
├── ml/                                 # Machine Learning Engineering & Training Code
│   ├── data_acquisition/               # Bulk downloaders (IMDb, The Numbers, TMDB)
│   ├── preprocessing/                  # Data cleaning, currency & inflation engines
│   ├── feature_engineering/            # Time-locked feature calculation modules
│   ├── training/                       # Offline training scripts (train_catboost.py)
│   ├── evaluation/                     # Metric evaluation & cross-validation scripts
│   ├── models/                         # Serialized Model Artifacts (Gitignored)
│   │   ├── production/                 # Active symlinked production models (.cbm)
│   │   └── archive/                    # Historical versioned model artifacts
│   └── notebooks/                      # Exploratory Data Analysis (EDA) Notebooks
│
└── frontend/                           # React 18 TypeScript Single-Page Application
    ├── src/
    │   ├── main.tsx                    # React DOM root entrypoint
    │   ├── App.tsx                     # Top-level routing & layout shell
    │   ├── api/                        # Typed Axios / Fetch HTTP client layer
    │   ├── components/                 # Reusable UI Component Library
    │   │   ├── layout/                 # Navbar, Sidebar, Footer, PageShell
    │   │   ├── cards/                  # MovieCard, PredictionCard, MetricCard
    │   │   ├── charts/                 # SHAPWaterfall, PredictionIntervalBar
    │   │   └── ui/                     # Badges, Buttons, Inputs, Sliders, Modals
    │   ├── pages/                      # Primary View Destinations
    │   │   ├── OverviewPage.tsx
    │   │   ├── MovieExplorerPage.tsx
    │   │   ├── UpcomingReleasesPage.tsx
    │   │   ├── WhatIfSimulatorPage.tsx
    │   │   ├── MarketAnalyticsPage.tsx
    │   │   └── ModelIntelligencePage.tsx
    │   ├── hooks/                      # Custom React Hooks (useMovie, usePrediction)
    │   ├── stores/                     # Zustand lightweight UI stores
    │   ├── types/                      # TypeScript Interface Definitions
    │   └── utils/                      # Currency formatters, date utilities
    ├── public/                         # Static assets, branding, and fallback art
    ├── package.json
    ├── tailwind.config.js
    └── vite.config.ts
```

---

## 5. Subsystem Specifications & Internal Boundaries

### 5.1 Presentation Layer (React + Vite + TypeScript)
- **Role**: Renders the dark cinematic interface, delivers responsive views, manages interactive What-If simulation inputs, and presents SHAP visualizations.
- **Boundaries**: Strictly client-side. The frontend holds zero business logic and zero prediction formulas; it communicates solely via typed REST requests to `/api/v1/`.

### 5.2 API & Application Service Layer (FastAPI)
- **Role**: Acts as the central orchestrator. Validates incoming requests via Pydantic schemas, queries PostgreSQL via async SQLAlchemy sessions, and delegates analytical requests to the ML runtime.
- **Boundaries**: Controllers contain no SQL queries; they invoke `Services`, which mediate between database repositories and ML predictors.

### 5.3 Machine Learning Serving & Inference Layer
- **Role**: Encapsulated within `backend/app/ml/`. Loads serialized CatBoost binary models (`.cbm`) and TreeSHAP explainers into memory during application startup (`lifespan`).
- **Boundaries**: Pure algorithmic computation. Accepts raw Python dictionaries of feature values; returns structured predictions, conformal bounds, and SHAP attribution vectors. It executes no direct I/O or network calls.

### 5.4 Data Engineering & Ingestion Worker Subsystem
- **Role**: Autonomous background jobs powered by APScheduler. Executes scheduled queries to TMDB, YouTube Data API, and Google Trends; performs entity matching and triggers forecast recalculations.
- **Boundaries**: Operates asynchronously in background threads; writes directly to PostgreSQL tables (`movies`, `feature_snapshots`, `predictions`).

### 5.5 Persistence & Analytical Storage Layer
- **Role**: Dual-storage strategy: PostgreSQL handles transactional metadata, relational entities, and real-time active forecasts; Apache Parquet files store the multi-gigabyte raw ingestion data lake and historical ML training splits.

---

## 6. Component Inter-Communication Protocols

```
Frontend (Browser) 
      │
      ▼ HTTP/1.1 JSON (RESTful)
FastAPI Router (Uvicorn Async Worker)
      │
      ▼ In-Process Method Invocations (Python Typed Calls)
Service Layer (PredictionService)
      │
      ├──────────────────────────────┐
      ▼ In-Memory Pointer Call       ▼ Async SQL Query (pg8000/asyncpg)
ML Model Engine (CatBoost C++)     PostgreSQL Database
      │                              │
      ▼ In-Memory Array Return       ▼ Relational Tuple Return
PredictionService Composes Aggregate Response Schema
      │
      ▼ JSON Serialization (<15ms)
Frontend (Browser)
```

---

## 7. End-to-End Runtime Data Flow Scenarios

### Scenario A: User Explores a Film in Movie Explorer
1. User searches `"Pushpa 2: The Rule"` in the frontend Omnibox.
2. Frontend dispatches `GET /api/v1/movies/search?q=pushpa%202`.
3. `MovieService` performs a fuzzy title match on PostgreSQL `movies` table; returns matching candidate records.
4. User clicks title $\rightarrow$ frontend navigates to `/movies/{uuid}` and requests `GET /api/v1/movies/{uuid}/prediction`.
5. `PredictionService` checks PostgreSQL `predictions` table for active pre-computed forecast:
   - If active forecast exists and is fresh ($<24\text{h}$ old), it returns immediately.
   - If stale or missing, `PredictionService` retrieves latest `feature_snapshot`, calls `Predictor.predict()`, generates SHAP waterfall via `Explainer.explain()`, persists the result, and returns the response in $<180\text{ms}$.

### Scenario B: Scheduled Autonomous Movie Discovery
1. At 02:00 IST, `scheduler` triggers `discovery_job.py`.
2. Job polls TMDB `/movie/upcoming` and `/discover/movie` for Indian languages (`hi`, `te`, `ta`, `ml`, `kn`) and Global markets.
3. For each candidate payload, `EnrichmentService` executes entity resolution against canonical IDs:
   - If new film: Inserts into `movies`, schedules credits/trailer enrichment, computes Stage 1 features, writes `feature_snapshots`, generates initial prediction, and logs to `prediction_history`.
   - If existing film: Checks for date shifts or trailer drops; if changed, creates new snapshot and updates active prediction.

---

## 8. Cross-Cutting Concerns: Caching, Observability & Error Handling

1. **In-Memory Caching**: FastAPI caches static movie metadata and market intelligence aggregations using an in-process LRU cache (`cachetools`), avoiding repeated database hits for popular catalog titles.
2. **Structured Logging**: Structured JSON logging via `structlog` records execution time, query parameters, model inference latency, and error tracebacks.
3. **Resilient Error Responses**: All API errors adhere to RFC-7807 problem details specifications, returning consistent error objects:
   ```json
   {
     "error": {
       "code": "INSUFFICIENT_DATA_FOR_PREDICTION",
       "message": "Film data completeness score is 32% (below 40% minimum threshold).",
       "details": {"missing_attributes": ["production_budget", "primary_director"]}
     }
   }
   ```
