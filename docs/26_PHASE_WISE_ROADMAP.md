# CineMetrics — Complete Phase-Wise Implementation Roadmap (17 Phases)

**Document ID:** 26  
**Version:** 1.0  
**Status:** Approved Master Implementation Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [System Architecture](17_SYSTEM_ARCHITECTURE.md) | [Resource & Feasibility](25_RESOURCE_AND_FEASIBILITY_ANALYSIS.md) | [Acceptance Criteria](29_ACCEPTANCE_CRITERIA.md) | [Phase Tracker](../planning/PHASE_TRACKER.md)

---

## Executive Overview & Dependency Graph

The CineMetrics engineering roadmap is organized into **17 sequential, dependency-gated phases**. Each phase specifies concrete objectives, numbered technical tasks, technology tools, expected file deliverables, acceptance gates, and risk mitigations.

**STRICT DIRECTIVE: THIS DOCUMENT DEFINES THE FUTURE ROADMAP ONLY. NO IMPLEMENTATION CODE IS EXECUTED DURING THE CURRENT PLANNING STAGE.**

```
Phase 1: Architecture & Planning (COMPLETE)
   │
   ▼
Phase 2: Dataset Acquisition ──► Phase 3: Data Engineering ──► Phase 4: EDA
                                                                  │
   ┌──────────────────────────────────────────────────────────────┘
   ▼
Phase 5: Feature Engineering ──► Phase 6: Baseline ML ──► Phase 7: Advanced ML (CatBoost)
                                                               │
   ┌───────────────────────────────────────────────────────────┴──────────────────────────┐
   ▼                                                           ▼                          ▼
Phase 8: Success Classification                             Phase 9: Multilingual NLP   Phase 10: SHAP & Conformal
   │                                                           │                          │
   └───────────────────────────────────────────────────────────┼──────────────────────────┘
                                                               │
   ┌───────────────────────────────────────────────────────────┘
   ▼
Phase 11: Automated Movie Discovery ──► Phase 12: Continuous Ingestion
                                           │
   ┌───────────────────────────────────────┘
   ▼
Phase 13: FastAPI Backend ──► Phase 14: React Frontend ──► Phase 15: Advanced Features
                                                              │
   ┌──────────────────────────────────────────────────────────┘
   ▼
Phase 16: Integration & Deployment ──► Phase 17: Verification & Acceptance
```

---

## Detailed Phase Blueprints

### Phase 1: Research, Architecture & Planning (STATUS: COMPLETE)
- **Objective**: Conduct comprehensive architectural research, formulate data strategy, establish ML benchmarks, and author the complete 29-document planning suite.
- **Tasks**:
  1. Formulate Project Vision, Core Philosophy, and Requirement Specifications.
  2. Research and evaluate candidate data sources (TMDB, IMDb, The Numbers, Sacnilk).
  3. Formulate unified schema, historical snapshot strategy, and temporal leakage prevention rules.
  4. Compare machine learning algorithms (GBDTs, Neural Nets, Baselines).
  5. Architect modular monolith, database schema (19 entities), and OpenAPI 3.1 REST specifications.
  6. Design cinematic UI/UX system and component library.
  7. Generate all 7 Mermaid architectural diagrams.
- **Dependencies**: None.
- **Technologies**: Markdown, Mermaid, Architecture Modeling.
- **Deliverables**: All 29 files in `docs/`, 7 files in `diagrams/`, 12 files in `planning/`.
- **Acceptance Criteria**: 100% of planning artifacts written with zero placeholder text.
- **Estimated Effort**: 2 Weeks (Finished).

---

### Phase 2: Multi-Source Dataset Acquisition
- **Objective**: Establish authorized API connections, download bulk non-commercial archives, and build the raw Bronze Parquet data lake.
- **Tasks**:
  1. Set up developer credentials for TMDB API and YouTube Data API v3.
  2. Write resilient download scripts (`ml/data_acquisition/download_imdb.py`) for IMDb dumps (`title.basics`, `title.ratings`, `title.principals`, `title.crew`).
  3. Ingest Kaggle reference datasets (TMDB 5000, The Movies Dataset, Indian Box Office historical sets).
  4. Build automated TMDB paginated fetcher for historical Indian and international movie catalogs.
  5. Store all acquired payloads in partitioned Snappy Parquet files under `data/raw/{source}/`.
  6. Compute SHA-256 checksums and record provenance records in `data_source_records`.
- **Dependencies**: Phase 1.
- **Technologies**: Python 3.11, `httpx`, `pyarrow`, Kaggle CLI.
- **Deliverables**: `ml/data_acquisition/` scripts, `data/raw/` Parquet partitions.
- **Acceptance Criteria**: Minimum 15,000 candidate movie records ingested with verified checksums.
- **Risks**: API rate limit throttling; mitigated via token bucket client throttling.
- **Estimated Effort**: 1.5 Weeks.

---

### Phase 3: Unified Dataset Engineering & Entity Resolution
- **Objective**: Execute cross-source record linkage, deduplication, financial normalization, and inflation adjustment to create the canonical Silver dataset.
- **Tasks**:
  1. Implement title string normalisation pipeline (regex sanitization, diacritic stripping, romanization).
  2. Execute exact foreign key resolution (TMDB $\leftrightarrow$ IMDb IDs via external ID mappings).
  3. Execute multi-pass fuzzy record linkage using RapidFuzz for residual titles (threshold $\ge 0.88$).
  4. Resolve conflicting financial figures using strict source priority hierarchy.
  5. Ingest historical FX tables and convert nominal collections to standardized USD and INR.
  6. Apply US and Indian monthly CPI deflators to produce constant 2024 real-term financial metrics.
  7. Execute KNN missing budget imputation with binary imputation flags.
  8. Enforce Pandera and Pydantic schema validation suites; generate data quality audit report.
- **Dependencies**: Phase 2.
- **Technologies**: Pandas, PyArrow, DuckDB, RapidFuzz, Pandera, Pydantic.
- **Deliverables**: `data/unified/unified_movies.parquet`, `data/unified/unified_financials.parquet`.
- **Acceptance Criteria**: $>95\%$ match accuracy on 200-film test set; zero unhandled schema errors.
- **Risks**: Conflicting Indian trade reports; mitigated via provenance logging.
- **Estimated Effort**: 2.5 Weeks.

---

### Phase 4: Exploratory Data Analysis & Statistical Modeling
- **Objective**: Conduct in-depth exploratory analysis on box-office distributions, talent concentration, seasonality trends, and market correlations.
- **Tasks**:
  1. Analyze target variable distributions: verify log-normal behavior of worldwide gross.
  2. Compute correlation matrices between budget, star power, runtime, and revenue.
  3. Analyze seasonality: evaluate festive release premiums (Diwali, Eid, Christmas, Summer).
  4. Analyze Indian regional cinema dynamics: compare recovery ratios across Bollywood, Tollywood, and Kollywood.
  5. Author exploratory Jupyter notebooks documenting findings and statistical insights.
- **Dependencies**: Phase 3.
- **Technologies**: Jupyter, Seaborn, Matplotlib, SciPy, DuckDB.
- **Deliverables**: `ml/notebooks/01_eda_distributions.ipynb`, `ml/notebooks/02_market_dynamics.ipynb`.
- **Acceptance Criteria**: Quantitative confirmation of target skewness; feature selection hypotheses validated.
- **Estimated Effort**: 1 Week.

---

### Phase 5: Feature Engineering & Time-Locked Feature Store
- **Objective**: Compute all 65+ time-locked engineered features and construct the Gold training, validation, and holdout test splits.
- **Tasks**:
  1. Implement point-in-time rolling talent star power calculator (`calculate_talent_star_power`).
  2. Implement director track record and genre specialization metrics.
  3. Implement calendar clash density and competing star power calculators.
  4. Compute digital engagement velocity metrics (YouTube trailer lead times, view ratios).
  5. Construct immutable feature vectors and populate `feature_snapshots`.
  6. Partition dataset chronologically: Train ($<2020$), Validation ($2020–2022$), Holdout Test ($2023–2024$).
  7. Execute automated temporal leakage test suite (`tests/test_leakage.py`).
- **Dependencies**: Phase 4.
- **Technologies**: Pandas, PyArrow, NumPy, Pytest.
- **Deliverables**: `ml/feature_engineering/` calculators, `data/snapshots/train_v1.parquet`, `val_v1.parquet`, `test_v1.parquet`.
- **Acceptance Criteria**: 100% pass rate on leakage audits; zero lookahead features in Stage 1 matrices.
- **Estimated Effort**: 2 Weeks.

---

### Phase 6: Baseline Machine Learning Benchmarks
- **Objective**: Establish transparent baseline models to establish performance lower-bounds and validate the necessity of advanced architectures.
- **Tasks**:
  1. Implement Baseline 1: Historical Market Segment Median.
  2. Implement Baseline 2: Linear Budget Multiplier Rule ($\hat{y} = 2.2 \times \text{Budget}$).
  3. Implement Baseline 3: 5-Feature Ordinary Least Squares (OLS) Regression.
  4. Implement Baseline 4: Default Random Forest Regressor.
  5. Compute baseline evaluation metrics on holdout test set (SMAPE, MAE, $R^2$).
- **Dependencies**: Phase 5.
- **Technologies**: Scikit-Learn, NumPy.
- **Deliverables**: `ml/training/train_baselines.py`, `planning/MODEL_COMPARISON_MATRIX.md` (baseline rows filled).
- **Acceptance Criteria**: Baseline 3 establishes SMAPE benchmark ($\approx 55\%–65\%$).
- **Estimated Effort**: 1 Week.

---

### Phase 7: Advanced Revenue Prediction (CatBoost Primary Model)
- **Objective**: Train, optimize, and cross-validate production Gradient Boosted Decision Tree (GBDT) regressors.
- **Tasks**:
  1. Train CatBoost Regressor utilizing native categorical target statistics.
  2. Train secondary benchmark models: LightGBM Regressor and XGBoost (Hist) Regressor.
  3. Execute automated hyperparameter optimization via Optuna (100 trials, TPE sampler) on Validation Split.
  4. Track all experiments, hyperparameters, and artifacts in local MLflow server.
  5. Evaluate holdout test performance across global and market-specific cohorts (Bollywood, Tollywood, Hollywood).
  6. Verify complexity justification gate: CatBoost must achieve $\ge 20\%$ relative SMAPE reduction over Baseline 3.
  7. Serialize production artifact to native `.cbm` binary format in `ml/models/production/`.
- **Dependencies**: Phase 6.
- **Technologies**: CatBoost, LightGBM, XGBoost, Optuna, MLflow.
- **Deliverables**: `ml/training/train_catboost.py`, `ml/models/production/catboost_revenue_v1.cbm`.
- **Acceptance Criteria**: Holdout Test $\text{SMAPE} \le 40.0\%$; training completes in $<5\text{ minutes}$ on CPU.
- **Estimated Effort**: 2 Weeks.

---

### Phase 8: Commercial Success Classification Modeling
- **Objective**: Train calibrated multi-class classifiers to predict commercial success tiers (Blockbuster to Disaster).
- **Tasks**:
  1. Map financial recovery ratios into standardized 7-tier labels.
  2. Train CatBoost Classifier with balanced class weights to address rare Blockbuster representation.
  3. Perform probability calibration using Isotonic Regression and Platt Scaling.
  4. Evaluate Macro $F_1$, PR-AUC, and Quadratic Weighted Kappa ($\kappa_w$).
  5. Serialize production classification artifact to `ml/models/production/catboost_classifier_v1.cbm`.
- **Dependencies**: Phase 7.
- **Technologies**: CatBoost Classifier, Scikit-Learn Calibration.
- **Deliverables**: `ml/training/train_classifier.py`, `ml/models/production/catboost_classifier_v1.cbm`.
- **Acceptance Criteria**: Quadratic Weighted Kappa $\kappa_w \ge 0.65$; Brier Multi-Class Score $<0.20$.
- **Estimated Effort**: 1.5 Weeks.

---

### Phase 9: Multilingual NLP & Sentiment Analysis Engine
- **Objective**: Implement the pre-release audience anticipation and multilingual sentiment analysis pipeline.
- **Tasks**:
  1. Build YouTube trailer comment harvesting script via YouTube Data API v3.
  2. Implement text preprocessing and language routing (Latin script vs. Indic script).
  3. Integrate Google MuRIL (`google/muril-base-cased`) via HuggingFace Transformers.
  4. Quantize model weights to 8-bit dynamic INT8 for lightweight CPU inference.
  5. Aggregate comment sentiment into 5 continuous movie-level features.
  6. Materialize sentiment features into `sentiment_observations` table.
- **Dependencies**: Phase 5.
- **Technologies**: PyTorch, HuggingFace Transformers, MuRIL, LangDetect.
- **Deliverables**: `ml/nlp/sentiment_engine.py`, `backend/app/services/sentiment_service.py`.
- **Acceptance Criteria**: CPU inference latency $<1.5\text{s}$ per 100 comments; handles Hinglish commentary.
- **Estimated Effort**: 2 Weeks.

---

### Phase 10: Explainability, Conformal Uncertainty & Risk Engine
- **Objective**: Integrate TreeSHAP explainability and MAPIE conformal prediction intervals.
- **Tasks**:
  1. Initialize in-memory `shap.TreeExplainer` on production CatBoost regressor.
  2. Implement local explanation generator extracting top positive and negative drivers.
  3. Fit MAPIE conformal regressor to generate 80% and 95% prediction intervals.
  4. Implement financial risk calculator (budget recovery probabilities, break-even gap).
  5. Unit test SHAP mathematical additivity property ($f(x) = \phi_0 + \sum \phi_i$).
- **Dependencies**: Phase 7, Phase 8.
- **Technologies**: SHAP, MAPIE, NumPy.
- **Deliverables**: `backend/app/ml/explainer.py`, `backend/app/ml/uncertainty.py`.
- **Acceptance Criteria**: SHAP explanation generated in $<120\text{ms}$; 80% conformal coverage verified.
- **Estimated Effort**: 1.5 Weeks.

---

### Phase 11: Automated Movie Discovery Engine
- **Objective**: Build the autonomous discovery pipeline that continuously monitors for upcoming films.
- **Tasks**:
  1. Build scheduled polling client querying TMDB `/movie/upcoming` and `/discover/movie`.
  2. Implement regional language filters (Hindi, Telugu, Tamil, Malayalam, Kannada).
  3. Implement entity matching against existing database; route new titles to enrichment queue.
  4. Build metadata enrichment worker fetching credits, release dates, and trailer video IDs.
  5. Store execution metrics in `ingestion_jobs` and audit updates in `movie_history`.
- **Dependencies**: Phase 3, Phase 10.
- **Technologies**: Python, `httpx`, SQLAlchemy, APScheduler.
- **Deliverables**: `backend/jobs/discovery_job.py`, `backend/app/services/enrichment_service.py`.
- **Acceptance Criteria**: Autonomous daily discovery runs without user interaction; zero duplicate inserts.
- **Estimated Effort**: 1.5 Weeks.

---

### Phase 12: Continuous Ingestion & Prediction Lifecycle Engine
- **Objective**: Automate daily digital buzz tracking and multi-stage forecast revision.
- **Tasks**:
  1. Build scheduled worker polling YouTube trailer statistics and Google Trends.
  2. Implement Prediction Readiness Score (0–100) evaluation logic.
  3. Detect feature delta triggers and generate new versioned `feature_snapshots`.
  4. Recalculate active predictions when readiness advances or significant deltas occur.
  5. Append prediction revisions and change explanations to `prediction_history`.
- **Dependencies**: Phase 11.
- **Technologies**: APScheduler, PostgreSQL JSONB.
- **Deliverables**: `backend/jobs/buzz_update_job.py`, `backend/app/services/prediction_service.py`.
- **Acceptance Criteria**: Prediction revisions logged with full audit history; inactive predictions archived.
- **Estimated Effort**: 1.5 Weeks.

---

### Phase 13: FastAPI Application & Backend Core
- **Objective**: Develop the high-performance async REST API layer.
- **Tasks**:
  1. Initialize FastAPI application with CORS, exception handlers, and structured logging.
  2. Implement database connection pooling and Alembic migration scripts.
  3. Build all API route handlers matching OpenAPI specification (movies, upcoming, predictions, analytics).
  4. Implement `slowapi` rate limiting on public and simulation endpoints.
  5. Implement JWT authentication and RBAC for administrative routes.
  6. Write comprehensive Pytest integration suite (`tests/api/`).
- **Dependencies**: Phase 10, Phase 12.
- **Technologies**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Slowapi.
- **Deliverables**: Complete `backend/app/` code package.
- **Acceptance Criteria**: 100% of API endpoints functional; search latency $<60\text{ms}$; 0 unhandled 500 errors.
- **Estimated Effort**: 2.5 Weeks.

---

### Phase 14: React Frontend Development (Cinematic UI/UX)
- **Objective**: Build the dark cinematic user interface adhering to design specifications.
- **Tasks**:
  1. Scaffold React 18 TypeScript application using Vite and Tailwind CSS.
  2. Implement global theme variables, typography, and Framer Motion animation wrappers.
  3. Build core component library (MovieCard, PredictionIntervalBar, SHAPWaterfall, MetricCard).
  4. Implement Overview Dashboard and Upcoming Releases Intelligence views.
  5. Implement Movie Explorer analytical dossier view with interactive tabs.
  6. Implement dual-currency formatting utility (INR Crores $\leftrightarrow$ USD Millions).
  7. Audit responsive breakpoints across Mobile, Tablet, and Desktop.
- **Dependencies**: Phase 13.
- **Technologies**: React, TypeScript, Vite, Tailwind CSS, Framer Motion, Recharts, TanStack Query.
- **Deliverables**: Complete `frontend/src/` code package.
- **Acceptance Criteria**: Lighthouse Performance score $\ge 85$; WCAG 2.1 AA accessibility verified.
- **Estimated Effort**: 3.5 Weeks.

---

### Phase 15: Advanced Product Features (Simulation & Intelligence)
- **Objective**: Deliver interactive counterfactual What-If simulation and market comparison workspaces.
- **Tasks**:
  1. Build What-If Simulator interface with budget sliders, director selectors, and clash toggles.
  2. Implement backend in-memory simulation handler (`POST /simulate/what-if`).
  3. Build Movie Comparison workspace comparing multiple releases side-by-side.
  4. Build Talent Dossier pages (Actor and Director historical box-office curves).
  5. Build Model Intelligence page displaying live evaluation metrics and SHAP global importance.
- **Dependencies**: Phase 14.
- **Technologies**: React, Recharts, FastAPI.
- **Deliverables**: `frontend/src/pages/WhatIfSimulatorPage.tsx`, `frontend/src/pages/ComparisonPage.tsx`.
- **Acceptance Criteria**: What-If simulation round-trip latency $<250\text{ms}$; visual comparison functional.
- **Estimated Effort**: 2 Weeks.

---

### Phase 16: System Integration & Multi-Environment Deployment
- **Objective**: Package platform into Docker Compose for local execution and deploy to zero-cost cloud services.
- **Tasks**:
  1. Author production Dockerfiles for backend and frontend.
  2. Configure and verify local multi-container `docker-compose.yml`.
  3. Deploy PostgreSQL instance to Supabase free tier; run Alembic migrations.
  4. Deploy FastAPI backend to Fly.io or Render free tier.
  5. Deploy React frontend SPA to Vercel edge network.
  6. Configure custom domains, SSL certificates, and Sentry error monitoring.
- **Dependencies**: Phase 15.
- **Technologies**: Docker, Vercel, Fly.io, Supabase, Sentry.
- **Deliverables**: `docker-compose.yml`, production cloud deployment URLs.
- **Acceptance Criteria**: Live public URL functional; database connected; models responding to queries.
- **Estimated Effort**: 1.5 Weeks.

---

### Phase 17: Comprehensive Testing, Verification & Final Acceptance
- **Objective**: Execute end-to-end user journey tests and verify all 50 final acceptance criteria.
- **Tasks**:
  1. Execute Playwright automated browser test suite across all core workflows.
  2. Execute security and dependency vulnerability audit (`pip-audit`, `npm audit`).
  3. Audit legal attribution notices in frontend footer (TMDB, IMDb).
  4. Validate all 50 items on the Master Acceptance Checklist (`docs/23_TESTING_AND_VALIDATION.md`).
  5. Finalize portfolio documentation and record interactive platform walkthrough video.
- **Dependencies**: Phase 16.
- **Technologies**: Playwright, Pytest, Axe-Core.
- **Deliverables**: Final Test Report, Portfolio Demonstration Showcase.
- **Acceptance Criteria**: 100% of acceptance criteria verified; platform ready for serious ML portfolio presentation.
- **Estimated Effort**: 1.5 Weeks.

---

## Master Implementation Timeline Summary

| Phase Block | Target Phases | Cumulative Duration | Primary Milestones |
|---|:---:|:---:|---|
| **Phase Block A: Data & Architecture** | Phases 1–4 | 5.5 Weeks | Architecture locked, 15k raw films ingested, Silver conformed lake operational. |
| **Phase Block B: ML & Modeling Core** | Phases 5–8 | 6.5 Weeks | Leakage-free Gold splits, CatBoost model trained (SMAPE $\le 40\%$), calibrated success tiers. |
| **Phase Block C: Intelligence & NLP** | Phases 9–12 | 6.5 Weeks | MuRIL sentiment engine, SHAP waterfalls, autonomous daily discovery operational. |
| **Phase Block D: Full-Stack & UI/UX** | Phases 13–15 | 8.0 Weeks | FastAPI REST endpoints live, dark cinematic React UI complete, What-If simulator active. |
| **Phase Block E: Deployment & Review**| Phases 16–17 | 3.0 Weeks | Docker & Vercel/Fly.io deployed, Playwright tests passing, 50-item checklist verified. |
| **TOTAL PROJECT ESTIMATE** | **17 Phases** | **~29.5 Weeks (~7 Months)** | **Full production-grade cinema intelligence portfolio platform.** |
