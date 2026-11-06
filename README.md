# 🎬 CineMetrics — AI-Powered Cinema Intelligence Platform

[![Status: Planning](https://img.shields.io/badge/Status-Planning-yellow?style=flat-square)](docs/01_PROJECT_VISION.md)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![React + TypeScript](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61dafb?style=flat-square&logo=react)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## Vision

CineMetrics is an end-to-end cinema intelligence platform that combines structured box-office data, NLP-based sentiment analysis, and gradient-boosted machine learning to predict movie revenues, classify commercial success tiers, and surface actionable insights — all within a visually immersive, dark-themed interface. It is purpose-built for the Indian film ecosystem (Hindi, Telugu, Tamil, Malayalam, Kannada) while also covering Hollywood and select international markets. CineMetrics is not merely a prediction tool; it is a research-grade, explainable ML system designed to demonstrate what rigorous data science looks like applied to the entertainment industry.

---

## Two Core Modes

### 🔍 Mode 1 — Movie Explorer
Search any released or upcoming film and receive a full intelligence dossier: revenue predictions at multiple pre-release stages, SHAP-driven explanations of every prediction, historical actuals for released films (with retrospective accuracy scoring), sentiment summaries of cast/trailer/review signals, and an interactive what-if simulator to explore counterfactual scenarios (e.g., "What if the budget were 20% higher?").

### 📡 Mode 2 — Upcoming Releases Intelligence
A live dashboard tracking all films currently in production, post-production, and nearing release. Auto-discovery pulls new announcements from TMDB, enriches them with cast, budget, genre, and competitive landscape data, and generates tiered predictions that update as new information becomes available. Fourteen dashboard sections cover everything from "Releasing This Week" to "Major Clash Alerts."

---

## Key Capabilities

| Capability | Description |
|---|---|
| **Multi-Stage Revenue Prediction** | Separate prediction confidence at Announcement, Cast-Lock, Trailer-Drop, Release-Week, and Post-Opening stages |
| **Success Classification** | Probabilistic tiers: Disaster / Below Average / Average / Hit / Super Hit / Blockbuster |
| **NLP Sentiment Analysis** | Aggregated sentiment from trailer comments, critic reviews, and social buzz (DistilBERT / XLM-RoBERTa) |
| **SHAP Explainability** | TreeSHAP force plots, waterfall charts, and global feature importance — mandatory for every prediction |
| **What-If Simulation** | Counterfactual engine: modify budget, cast, release date, genre, competition — see instant prediction delta |
| **Automated Discovery** | Background pipeline finds newly announced films, deduplicates, and queues for data enrichment |
| **Comparison Mode** | Side-by-side comparison of up to four films across all metrics |
| **Financial Risk Scoring** | Budget recovery probability, breakeven threshold analysis, distributor share estimation |

---

## Indian Cinema Coverage

CineMetrics places particular emphasis on the Indian film industries, which are under-served by existing English-language analytics tools:

| Industry | Language | Also Known As |
|---|---|---|
| Bollywood | Hindi | Hindi Film Industry (HFI) |
| Tollywood | Telugu | Telugu Film Industry |
| Kollywood | Tamil | Tamil Film Industry |
| Mollywood | Malayalam | Malayalam Film Industry |
| Sandalwood | Kannada | Kannada Film Industry |

Box-office figures are normalised in INR (₹) with USD conversion available. Regional theatrical windows, festival release patterns (Diwali, Eid, Pongal, Onam, Ugadi), and OTT-sale separation are all accounted for in the data model.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   React + TypeScript                  │
│           (Vite, Tailwind CSS, Framer Motion)        │
│    Movie Explorer UI  <────>  Upcoming Releases UI   │
└──────────────────────┬──────────────────────────────┘
                       │ REST / JSON
┌──────────────────────▼──────────────────────────────┐
│                FastAPI (Python 3.11+)                 │
│  /predict  /sentiment  /explain  /discover  /search  │
│           Pydantic validation + async I/O             │
└────┬────────────┬──────────────┬────────────────────┘
     │            │              │
┌────▼────┐  ┌────▼────┐  ┌─────▼──────┐
│PostgreSQL│  │ML Models│  │ NLP Models │
│ (movies, │  │XGBoost  │  │DistilBERT  │
│ features,│  │LightGBM │  │XLM-RoBERTa │
│ reviews, │  │CatBoost │  │(sentiment) │
│ preds)   │  │+ SHAP   │  └────────────┘
└──────────┘  └─────────┘
```

**Backend:** FastAPI with async endpoints, Pydantic v2 schemas, SQLAlchemy ORM, Alembic migrations.  
**Frontend:** React 18 + TypeScript, Vite bundler, Tailwind CSS v3, Framer Motion animations, Recharts / D3 visualisations.  
**Database:** PostgreSQL 15+ with JSONB for flexible feature storage, full-text search, and row-level partitioning by market.  
**ML Pipeline:** Scikit-learn preprocessing → XGBoost / LightGBM / CatBoost ensemble → SHAP explanations → MLflow experiment tracking.  
**NLP:** Hugging Face Transformers — DistilBERT for English reviews, XLM-RoBERTa or IndicBERT for multilingual Indian reviews.

---

## Documentation Structure

> All 29 planning documents live under `docs/`. They are numbered sequentially and cover every phase from data sourcing to deployment.

| # | Document | Description |
|---|---|---|
| 01 | [Project Vision](docs/01_PROJECT_VISION.md) | Vision, problem statement, philosophy, success metrics |
| 02 | [Requirements Specification](docs/02_REQUIREMENTS_SPECIFICATION.md) | Functional, non-functional, ML, UI requirements |
| 03 | [Product Modes & User Flows](docs/03_PRODUCT_MODES_AND_USER_FLOWS.md) | Mode designs, wireframes, user journeys |
| 04 | [Data Sources & Collection Strategy](docs/04_DATA_SOURCES_AND_COLLECTION_STRATEGY.md) | TMDB, IMDb, Sacnilk, Kaggle — sourcing plan |
| 05 | [Data Schema & Database Design](docs/05_DATA_SCHEMA_AND_DATABASE_DESIGN.md) | PostgreSQL schema, ERD, indexes |
| 06 | [Data Ingestion Pipeline](docs/06_DATA_INGESTION_PIPELINE.md) | ETL architecture, schedulers, deduplication |
| 07 | [Feature Engineering](docs/07_FEATURE_ENGINEERING.md) | 150+ features, derivation logic, temporal guards |
| 08 | [ML Model Architecture](docs/08_ML_MODEL_ARCHITECTURE.md) | Model selection, training strategy, ensembling |
| 09 | [Revenue Prediction — Regression](docs/09_REVENUE_PREDICTION_REGRESSION.md) | Regression models, targets, metrics |
| 10 | [Success Classification](docs/10_SUCCESS_CLASSIFICATION.md) | Six-tier classification, thresholds by market |
| 11 | [Sentiment Analysis Pipeline](docs/11_SENTIMENT_ANALYSIS_PIPELINE.md) | NLP pipeline, models, multilingual handling |
| 12 | [SHAP Explainability](docs/12_SHAP_EXPLAINABILITY.md) | TreeSHAP, force plots, global importance |
| 13 | [What-If Simulation Engine](docs/13_WHAT_IF_SIMULATION_ENGINE.md) | Counterfactual design, constraints, UI |
| 14 | [Automated Discovery System](docs/14_AUTOMATED_DISCOVERY_SYSTEM.md) | TMDB polling, deduplication, enrichment queue |
| 15 | [Upcoming Releases Intelligence](docs/15_UPCOMING_RELEASES_INTELLIGENCE.md) | Dashboard 14-section design, filters |
| 16 | [Financial Metrics & Calculations](docs/16_FINANCIAL_METRICS_AND_CALCULATIONS.md) | Gross, net, distributor share formulas |
| 17 | [Currency & Regional Normalisation](docs/17_CURRENCY_AND_REGIONAL_NORMALISATION.md) | INR/USD, regional box-office differences |
| 18 | [Backend API Design](docs/18_BACKEND_API_DESIGN.md) | FastAPI routes, schemas, auth, rate limiting |
| 19 | [Frontend Architecture](docs/19_FRONTEND_ARCHITECTURE.md) | React component tree, state management, routing |
| 20 | [UI/UX Design System](docs/20_UI_UX_DESIGN_SYSTEM.md) | Dark cinema theme, typography, component library |
| 21 | [Data Quality & Validation](docs/21_DATA_QUALITY_AND_VALIDATION.md) | Validation rules, anomaly detection, QA pipeline |
| 22 | [Model Evaluation Framework](docs/22_MODEL_EVALUATION_FRAMEWORK.md) | Metrics, backtesting, calibration, reporting |
| 23 | [MLOps & Experiment Tracking](docs/23_MLOPS_AND_EXPERIMENT_TRACKING.md) | MLflow, model registry, retraining triggers |
| 24 | [Testing Strategy](docs/24_TESTING_STRATEGY.md) | Unit, integration, E2E, ML-specific tests |
| 25 | [Deployment Architecture](docs/25_DEPLOYMENT_ARCHITECTURE.md) | Local dev, containerisation, self-hosted options |
| 26 | [Implementation Roadmap](docs/26_IMPLEMENTATION_ROADMAP.md) | 8-phase plan with milestones and effort estimates |
| 27 | [Risks & Mitigation](docs/27_RISKS_AND_MITIGATION.md) | Risk register, likelihood/impact matrix |
| 28 | [Final Technical Decisions](docs/28_FINAL_TECHNICAL_DECISIONS.md) | Architecture Decision Records (ADRs) |
| 29 | [Acceptance Criteria](docs/29_ACCEPTANCE_CRITERIA.md) | Phase-by-phase and 100-item final checklist |

---

## Planning Status

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Project setup, documentation, environment scaffold | Not Started |
| Phase 1 | Data collection: TMDB, IMDb, Kaggle datasets | Not Started |
| Phase 2 | Data cleaning, schema design, PostgreSQL setup | Not Started |
| Phase 3 | Feature engineering (150+ features) | Not Started |
| Phase 4 | ML model training (regression + classification) | Not Started |
| Phase 5 | Sentiment analysis pipeline | Not Started |
| Phase 6 | SHAP explainability integration | Not Started |
| Phase 7 | FastAPI backend development | Not Started |
| Phase 8 | React frontend development | Not Started |
| Phase 9 | Automated discovery system | Not Started |
| Phase 10 | Integration, testing, deployment | Not Started |

---

## Planned Dataset Sources

| Source | Type | Coverage | Access |
|---|---|---|---|
| [TMDB API](https://www.themoviedb.org/documentation/api) | Movie metadata, cast, crew, posters | Global, 500K+ movies | Free API key |
| [IMDb Non-Commercial Datasets](https://developer.imdb.com/non-commercial-datasets/) | Ratings, titles, principals | Global | Free download (TSV) |
| [The Numbers](https://www.the-numbers.com/) | Box-office financials | Hollywood, partial India | Public web data |
| [Sacnilk](https://sacnilk.com/) | Indian box-office (day-wise) | Hindi, South Indian | Public web data |
| [Kaggle — TMDB Movie Dataset](https://www.kaggle.com/datasets) | Curated ML-ready movie data | Mixed global | Free download |
| [Kaggle — Bollywood Dataset](https://www.kaggle.com/) | Historical Bollywood grosses | Hindi cinema | Free download |
| YouTube Data API v3 | Trailer view counts, comments | Global | Free quota |
| Google Trends API | Search interest over time | Global | Free |

> **Note:** Web scraping from sources like Sacnilk must comply with each site's terms of service. See [docs/04_DATA_SOURCES_AND_COLLECTION_STRATEGY.md](docs/04_DATA_SOURCES_AND_COLLECTION_STRATEGY.md) for the full data sourcing strategy and legal notes.

---

## Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Language | Python | 3.11+ | Backend, ML, pipelines |
| Backend Framework | FastAPI | 0.111+ | REST API, async routes |
| ORM | SQLAlchemy | 2.x | Database abstraction |
| Migrations | Alembic | 1.13+ | Schema versioning |
| Database | PostgreSQL | 15+ | Primary data store |
| ML — Gradient Boosting | XGBoost / LightGBM / CatBoost | Latest stable | Revenue prediction |
| ML — Preprocessing | Scikit-learn | 1.4+ | Pipelines, transformers |
| Explainability | SHAP | 0.45+ | TreeSHAP explanations |
| NLP | Hugging Face Transformers | 4.40+ | Sentiment models |
| Experiment Tracking | MLflow | 2.x | Model registry, metrics |
| Frontend Framework | React | 18+ | UI |
| Frontend Language | TypeScript | 5.x | Type-safe UI code |
| Bundler | Vite | 5.x | Dev server, build |
| Styling | Tailwind CSS | 3.x | Utility-first CSS |
| Animation | Framer Motion | 11.x | UI animations |
| Charts | Recharts / D3.js | Latest | Data visualisation |
| State Management | Zustand | 4.x | Lightweight global state |
| Data Fetching | TanStack Query | 5.x | Server state, caching |
| Containerisation | Docker + Docker Compose | Latest | Local dev environment |
| Testing (Python) | pytest + pytest-asyncio | Latest | Unit and integration |
| Testing (Frontend) | Vitest + Playwright | Latest | Component and E2E |

---

## Quick Start

> **Implementation has not started.** The following commands are planned placeholders.

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/CineMetrics.git
cd CineMetrics

# 2. Copy environment file and fill in API keys
cp .env.example .env

# 3. Start services with Docker Compose (database, backend, frontend)
docker-compose up --build

# 4. Apply database migrations
docker-compose exec backend alembic upgrade head

# 5. Seed initial data (run data ingestion)
docker-compose exec backend python scripts/seed_initial_data.py

# Frontend available at:  http://localhost:5173
# Backend API at:         http://localhost:8000
# API Docs (Swagger):     http://localhost:8000/docs
# MLflow UI at:           http://localhost:5000
```

---

## Contributing

CineMetrics is currently in the planning and documentation phase. Contribution guidelines, code standards, and branch strategy will be published in `CONTRIBUTING.md` prior to Phase 1 implementation. If you have domain expertise in Indian cinema data, ML for entertainment analytics, or React data visualisation, your input is especially welcome.

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## Disclaimer

> **Financial Prediction Disclaimer:** All revenue predictions generated by CineMetrics are statistical estimates based on historical patterns and publicly available data. They do not constitute financial advice and should not be used for investment decisions. Actual box-office performance depends on many factors beyond any model's scope, including audience reception, marketing execution, geopolitical events, and unforeseen competition. Prediction accuracy targets are aspirational benchmarks for a student research project and are not guaranteed.
