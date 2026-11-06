# CineMetrics — Developer Quick-Start & Planning Brief

**Document ID:** QS-01  
**Version:** 1.0  
**Status:** Approved Onboarding Guide  
**Last Updated:** 2026-11  

---

## Welcome to CineMetrics

This quick-start guide orientates any new developer or AI coding agent joining the CineMetrics project.

**CRITICAL POLICY REMINDER:**  
**THE PROJECT IS CURRENTLY IN THE PLANNING STAGE ONLY.**  
Do not begin coding implementation, training models, building APIs, or deploying services until explicitly instructed.

---

## 1. What is CineMetrics?

CineMetrics is an intelligent movie analytics and financial forecasting platform that predicts the theatrical performance of upcoming films using our own trained machine learning models (CatBoost GBDT, TreeSHAP, and Google MuRIL NLP). 

It features two interconnected modes sharing a single database and inference engine:
- **Mode 1: Movie Explorer**: Deep analytical dossier for any searched movie (released or upcoming).
- **Mode 2: Upcoming Releases Intelligence**: Autonomous daily discovery radar tracking upcoming cinema across Indian (Hindi, Telugu, Tamil, Malayalam, Kannada) and International film industries.

---

## 2. Reading Order (Start Here)

To gain full context in under 30 minutes, read these documents in order:
1. [`docs/01_PROJECT_VISION.md`](01_PROJECT_VISION.md) — Executive vision, 10 core philosophies.
2. [`docs/03_PRODUCT_MODES_AND_USER_FLOWS.md`](03_PRODUCT_MODES_AND_USER_FLOWS.md) — Dual operating modes.
3. [`docs/08_HISTORICAL_SNAPSHOT_STRATEGY.md`](08_HISTORICAL_SNAPSHOT_STRATEGY.md) — Temporal leakage prevention rules.
4. [`docs/17_SYSTEM_ARCHITECTURE.md`](17_SYSTEM_ARCHITECTURE.md) — Pragmatic modular monolith blueprint.
5. [`docs/26_PHASE_WISE_ROADMAP.md`](26_PHASE_WISE_ROADMAP.md) — 17-phase implementation blueprint.

---

## 3. Key Decisions Already Locked (ADR Summary)

1. **ML Framework**: **CatBoost Regressor** (primary) + LightGBM (secondary). CatBoost was chosen for native handling of high-cardinality categorical variables (actors, directors) and ordered boosting leakage prevention.
2. **Backend**: **FastAPI** on Python 3.11 with Uvicorn (async ASGI, Pydantic v2 validation).
3. **Database**: **PostgreSQL 15+** (relational metadata + JSONB feature snapshots) + **Apache Parquet** (data lake).
4. **Frontend**: **React 18 + TypeScript + Vite + Tailwind CSS** (dark cinematic theme `#0A0A0F`, Framer Motion, Recharts).
5. **Architecture**: **Pragmatic Modular Monolith** — single process tree, shared in-memory ML model inference ($<50\text{ms}$ latency). Zero microservice overhead.
6. **NLP Sentiment**: **Google MuRIL** (`google/muril-base-cased`) — specifically understands Romanized Indic script and code-mixed slang (Hinglish/Tanglish).
7. **Explainability**: **TreeSHAP** — exact additive local feature attributions in polynomial time.
8. **Uncertainty**: **MAPIE Conformal Prediction** — distribution-free 80% & 95% prediction intervals with formal coverage guarantees.
9. **Budget / Infrastructure**: **$0.00 / month** — runs locally via Docker Compose; optionally deploys to free tiers of Vercel, Fly.io, and Supabase.

---

## 4. First Five Concrete Actions When Phase 2 Begins

When the project transition to **Phase 2 (Dataset Acquisition)** is approved:
1. **Acquire Free Developer API Keys**:
   - Register free account at [The Movie Database (TMDB)](https://www.themoviedb.org/) $\rightarrow$ generate API v3 Key.
   - Create free Google Cloud project $\rightarrow$ enable YouTube Data API v3 $\rightarrow$ generate API Key.
2. **Configure Local Environment**:
   - Copy `.env.example` to `.env` in backend root and populate API keys.
3. **Download Bulk IMDb Archives**:
   - Run `ml/data_acquisition/download_imdb.py` to fetch `title.basics.tsv.gz`, `title.ratings.tsv.gz`, and `title.principals.tsv.gz`.
4. **Fetch Kaggle Reference Baselines**:
   - Pull TMDB 5000 and curated Bollywood historical box-office sets.
5. **Initialize Bronze Parquet Lake**:
   - Convert downloaded raw files to partitioned Parquet files under `data/raw/`.

---

## 5. Software Prerequisites to Install

Ensure these tools are installed on your workstation:
- **Python 3.11+** (`python --version`)
- **Node.js 18+ & npm** (`node -v`)
- **Docker Desktop** (for local PostgreSQL 15 & MLflow containers)
- **Git** (`git --version`)
- **VS Code** with Python, Pylance, Tailwind CSS, and Mermaid Preview extensions.
