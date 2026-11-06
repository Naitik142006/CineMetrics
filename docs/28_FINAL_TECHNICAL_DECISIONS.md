# CineMetrics — Final Technical Architecture Decisions (ADR Log)

**Document ID:** 28  
**Version:** 1.0  
**Status:** Approved Architectural Decision Records  
**Last Updated:** 2026-11  
**Related Docs:** [System Architecture](17_SYSTEM_ARCHITECTURE.md) | [Machine Learning Research](10_MACHINE_LEARNING_RESEARCH.md) | [Phase Roadmap](26_PHASE_WISE_ROADMAP.md)

---

## Architecture Decision Record Index

| ADR ID | Decision Title | Status | Primary Decision |
|---|---|:---:|---|
| **ADR-01** | Primary Machine Learning Algorithm for Tabular Revenue Regression | **Accepted** | **CatBoost Regressor** (Yandex GBDT) |
| **ADR-02** | Backend Web Framework & API Runtime | **Accepted** | **FastAPI** (Python 3.11 + Uvicorn) |
| **ADR-03** | Primary System Database & Analytical Storage | **Accepted** | **PostgreSQL 15+** + Apache Parquet Lake |
| **ADR-04** | Client-Side Presentation Framework & UI Stack | **Accepted** | **React 18 + TypeScript + Vite + Tailwind CSS** |
| **ADR-05** | System Architecture Topology: Monolith vs. Microservices | **Accepted** | **Pragmatic Modular Monolith** |
| **ADR-06** | Global vs. Regional Segmented Model Architecture | **Accepted** | **Unified Global Model with Market Categoricals** |
| **ADR-07** | Prediction Lifecycle Stage Modeling Strategy | **Accepted** | **Single Model with Feature-Availability Bitmasks** |
| **ADR-08** | Natural Language Processing & Sentiment Architecture | **Accepted** | **Google MuRIL** (`google/muril-base-cased`) |
| **ADR-09** | Currency Normalisation & Macroeconomic Inflation Strategy | **Accepted** | **Standardized Real 2024 USD via CPI Deflation** |
| **ADR-10** | Machine Learning Experiment Tracking & Model Registry | **Accepted** | **Local MLflow Server** (SQLite backend) |
| **ADR-11** | Automated Movie Discovery Engine Core Source | **Accepted** | **TMDB API Polling with Regional Language Matrix** |
| **ADR-12** | Historical Snapshot & Temporal Leakage Strategy | **Accepted** | **Time-Invariant Feature Subsets + Live Snapshots** |
| **ADR-13** | Model Explainability & Feature Attribution Engine | **Accepted** | **TreeSHAP** (Additive Local Attributions) |
| **ADR-14** | Uncertainty Quantification & Prediction Interval Method | **Accepted** | **MAPIE Conformal Prediction** (80% & 95% Bands) |
| **ADR-15** | Deployment Target & Infrastructure Topology | **Accepted** | **Local Docker Compose + Free Cloud Tier** |

---

## Detailed Architecture Decision Records

### ADR-01: Primary Machine Learning Algorithm for Tabular Revenue Regression
- **Status**: **Accepted**
- **Context**: Movie box-office prediction is a structured tabular regression problem characterized by heterogeneous feature types: continuous numbers (budgets), high-cardinality categoricals (actors, directors, production companies), and extreme right-skewed revenue targets.
- **Options Considered**:
  1. *Ordinary Least Squares / Ridge / Lasso Regression*: Simple, but fails to capture complex nonlinear talent-budget interactions.
  2. *Deep Learning (TabNet / MLP)*: High computational cost, requires large data ($>100\text{k}$ rows), inferior performance on small tabular datasets.
  3. *XGBoost*: Excellent, but requires external target encoding or high-dimensional one-hot encoding for categorical variables.
  4. *LightGBM*: Very fast, but leaves categorical encoding optimization to custom heuristics.
  5. *CatBoost Regressor*: Native Ordered Target Statistics for high-cardinality categoricals; symmetric oblivious trees reduce overfitting on noisy entertainment data; native TreeSHAP integration.
- **Decision**: Adopt **CatBoost Regressor** as the primary revenue forecasting model, with LightGBM maintained as a fast secondary benchmark.
- **Rationale**: CatBoost handles actor IDs, director IDs, and genre combinations natively without explosive one-hot dimensionality. Its ordered boosting algorithm prevents target leakage during categorical encoding.
- **Consequences**: Training is slightly slower than LightGBM, but yields lower holdout SMAPE and superior out-of-the-box generalization.
- **Review Trigger**: If training dataset expands beyond 100,000 films or LightGBM demonstrates $>5\%$ superior validation SMAPE.

---

### ADR-02: Backend Web Framework & API Runtime
- **Status**: **Accepted**
- **Context**: The backend must serve RESTful JSON endpoints, load GBDT models into memory, execute fast $<50\text{ms}$ inferences, and coordinate scheduled background ingestion jobs.
- **Options Considered**:
  1. *Django + Django REST Framework*: Heavyweight ORM, synchronous overhead, excessive boilerplate for a data science API.
  2. *Flask*: Lightweight, but lacks native async ASGI, requires manual OpenAPI doc generation, and lacks built-in request validation.
  3. *FastAPI*: High-performance asynchronous ASGI (Uvicorn), strict Pydantic v2 validation, automatic OpenAPI 3.1 documentation, native dependency injection.
- **Decision**: Adopt **FastAPI** on Python 3.11 with Uvicorn.
- **Rationale**: FastAPI provides the ideal balance of high developer velocity, native async I/O for external API polling, and direct in-process Python ML model execution.
- **Consequences**: Async database sessions require SQLAlchemy 2.0 async conventions (`asyncpg`).
- **Review Trigger**: None. FastAPI is the definitive modern standard for Python ML APIs.

---

### ADR-03: Primary System Database & Analytical Storage
- **Status**: **Accepted**
- **Context**: The system must persist relational movie metadata, credits, historical predictions, and high-density JSONB feature snapshots.
- **Options Considered**:
  1. *SQLite*: Zero setup, but lacks concurrent async connection pooling, JSONB query indexing, and pg_trgm fuzzy matching.
  2. *MongoDB*: Flexible for JSON snapshots, but poor relational integrity across complex movie cast and credit graphs.
  3. *PostgreSQL 15+*: ACID compliance, robust foreign keys, powerful JSONB indexing, native trigram (`pg_trgm`) fuzzy title search, supported on all free-tier cloud platforms.
- **Decision**: Adopt **PostgreSQL 15+** as the relational store, paired with **Apache Parquet (Snappy)** for bulk analytical data lake storage.
- **Rationale**: PostgreSQL satisfies both 3NF transactional requirements and semi-structured snapshot queries via JSONB.
- **Consequences**: Requires a running PostgreSQL instance in development (managed via Docker).
- **Review Trigger**: None.

---

### ADR-04: Client-Side Presentation Framework & UI Stack
- **Status**: **Accepted**
- **Context**: CineMetrics demands a premium, dark cinematic user interface with responsive charts, smooth animations, and interactive What-If simulation sliders.
- **Options Considered**:
  1. *Streamlit / Gradio*: Rapid prototyping, but produces generic "data science demo" UIs with poor styling control and high server latency.
  2. *Next.js (React Server Components)*: Excellent, but introduces dual-server deployment complexity (Node.js server + Python backend).
  3. *React 18 + TypeScript + Vite + Tailwind CSS*: Clean Single Page Application (SPA), static deployment on global CDNs (Vercel), zero runtime CSS overhead, full design freedom.
- **Decision**: Adopt **React 18 + TypeScript + Vite + Tailwind CSS + Framer Motion + Recharts**.
- **Rationale**: Decouples the frontend completely into a static web app deployable for $0.00 on Vercel while delivering a bespoke, high-contrast cinematic aesthetic.
- **Consequences**: Client-side state and async caching must be managed explicitly via TanStack Query.
- **Review Trigger**: None.

---

### ADR-05: System Architecture Topology: Monolith vs. Microservices
- **Status**: **Accepted**
- **Context**: Determine whether to separate backend services (Movie Catalog, ML Predictor, NLP Engine, Ingestion Worker) into independent microservices or unify them.
- **Options Considered**:
  1. *Microservices (Docker Swarm / Kubernetes)*: Excessive operational overhead, network serialization latency, multi-repo complexity for a student developer.
  2. *Pragmatic Modular Monolith*: Single code repository and runtime process, strict internal package boundaries, shared in-memory ML model access.
- **Decision**: Adopt a **Pragmatic Modular Monolith**.
- **Rationale**: Eliminates inter-service network latency and distributed failure modes. An in-memory call to CatBoost takes $<10\text{ms}$; an HTTP microservice hop adds $30\text{ms}–50\text{ms}$.
- **Consequences**: Background jobs run inside the monolith runtime via APScheduler (threads).
- **Review Trigger**: If background ingestion compute spikes severely disrupt API request latency.

---

### ADR-06: Global vs. Regional Segmented Model Architecture
- **Status**: **Accepted**
- **Context**: Indian cinema comprises distinct regional industries (Bollywood, Tollywood, Kollywood, Mollywood) with different budget scales and theatrical dynamics compared to Hollywood.
- **Options Considered**:
  1. *Segmented Architecture (Separate Model per Language)*: Fragmented training sets (e.g. Mollywood has only $\sim 800$ clean training rows), leading to severe overfitting.
  2. *Unified Global Model with Market Categoricals*: Single model trained on all films; features include `market_segment`, `is_pan_india`, and relative budget ratios.
- **Decision**: Adopt a **Unified Global Model with Market Segment Categoricals**.
- **Rationale**: Enables smaller regional film industries to benefit from transfer learning on structural dynamics learned from the larger global dataset (e.g., franchise multipliers, sequel decay).
- **Consequences**: Model evaluation must enforce strict market-specific sub-cohort validation gates.
- **Review Trigger**: If holdout test SMAPE for any regional sub-cohort deviates by $>10\%$ from the global average.

---

### ADR-07: Prediction Lifecycle Stage Modeling Strategy
- **Status**: **Accepted**
- **Context**: A film progresses across 5 stages from 6 months out to post-opening weekend. Available features expand dramatically over time.
- **Options Considered**:
  1. *Five Disjoint Models*: Train five completely separate models (Stage 1 Model, Stage 2 Model, etc.). Multiplies training, tuning, and deployment overhead by 5x.
  2. *Single Model with Feature-Availability Bitmasks*: A unified model trained with feature-availability indicators and missing-signal robustness.
- **Decision**: Adopt a **Unified Stage-Aware Model** for Stages 1–3, with specialized calibration heuristics for Stage 4 (Advance Booking) and Stage 5 (Post-Opening Decay).
- **Rationale**: Dramatically simplifies MLOps and artifact management while maintaining high predictive accuracy across the pre-release lifecycle.
- **Consequences**: Early-stage predictions run with missing digital buzz inputs, which CatBoost natively handles via optimal split routing.
- **Review Trigger**: If a dedicated Stage 1 model proves significantly superior ($>3\%$ SMAPE gain) during Phase 7 validation.

---

### ADR-08: Natural Language Processing & Sentiment Architecture
- **Status**: **Accepted**
- **Context**: Audience sentiment discussions in Indian cinema mix native Indic scripts with Romanized transliterations and code-mixed slang (Hinglish/Tanglish).
- **Options Considered**:
  1. *VADER / TextBlob*: Fails completely on Romanized Indic text and code-mixed slang.
  2. *XLM-RoBERTa / mBERT*: Good cross-lingual transfer, but sub-optimal on transliterated Roman script (e.g., *"film ekdum bawaal hai"*).
  3. *Google MuRIL (`google/muril-base-cased`)*: Specifically pre-trained on native Indic, translated, and transliterated Indian language texts.
- **Decision**: Adopt **Google MuRIL** quantized to INT8 for local CPU inference.
- **Rationale**: MuRIL natively captures the semantic meaning of Indian entertainment discourse without requiring millions of custom labeled training pairs.
- **Consequences**: Model size ($\sim 950\text{MB}$) requires quantized batch processing in background jobs.
- **Review Trigger**: If inference latency on commodity CPU exceeds $2.0\text{s}$ per 100 comments.

---

### ADR-09: Currency Normalisation & Macroeconomic Inflation Strategy
- **Status**: **Accepted**
- **Context**: Comparing theatrical collections spanning 1995 to 2024 across INR, USD, and EUR introduces massive economic distortion without proper deflation.
- **Options Considered**:
  1. *Nominal Conversion at Current Exchange Rates*: Fails to account for 30 years of Rupee depreciation (from ₹35/$ in 1995 to ₹83/$ in 2024).
  2. *Constant 2024 Real USD via Historical FX + Monthly CPI*: Convert transactions to USD using the foreign exchange rate active on the exact release date, then deflate using US Bureau of Labor Statistics CPI-U series.
- **Decision**: Adopt **Constant 2024 Real USD via Historical FX + Monthly CPI Deflation**, while preserving native nominal INR and USD values for transparent audit display.
- **Rationale**: Provides an economically sound, inflation-neutral target variable ($y_{\text{real}}$) for machine learning models.
- **Consequences**: Requires historical FX and monthly CPI lookup tables embedded in the pipeline.
- **Review Trigger**: None. This is standard macroeconomic econometric methodology.

---

### ADR-10: Machine Learning Experiment Tracking & Model Registry
- **Status**: **Accepted**
- **Context**: Hyperparameter tuning, dataset version hashes, and model artifacts must be tracked systematically without recurring SaaS subscription costs.
- **Options Considered**:
  1. *Weights & Biases (W&B)*: Excellent, but introduces cloud dependency and potential team tier costs.
  2. *Manual CSV Tracking*: Fragile, non-reproducible, lacks artifact versioning.
  3. *Local MLflow Server*: Open-source, runs locally via `mlflow server`, stores metrics in SQLite and artifacts on local filesystem for $0.00.
- **Decision**: Adopt **Local MLflow Server**.
- **Rationale**: Delivers enterprise-grade experiment tracking, parameter logging, and artifact versioning on the developer's laptop with zero cloud costs.
- **Consequences**: MLflow server must be launched during offline training sessions.
- **Review Trigger**: None.

---

### ADR-11: Automated Movie Discovery Engine Core Source
- **Status**: **Accepted**
- **Context**: The platform must autonomously discover new movies across Indian and Hollywood industries without requiring human data entry.
- **Options Considered**:
  1. *Wikipedia Release Calendar Scraping*: Fragile, frequent HTML structure changes, prone to vandalized vandalism.
  2. *IMDb Non-Commercial Datasets*: Updated only daily/weekly in bulk; lacks real-time upcoming discovery endpoints.
  3. *TMDB API (`/movie/upcoming` & `/discover/movie`)*: Well-maintained REST endpoints, filtered by release dates and language codes (`hi`, `te`, `ta`, `ml`, `kn`), returns posters and external IDs.
- **Decision**: Adopt **TMDB API** as the primary autonomous discovery anchor, supplemented by admin manual verification for regional edge cases.
- **Rationale**: TMDB provides the highest programmatic stability and richest early metadata for announced global cinema.
- **Consequences**: Must adhere to non-commercial attribution terms and rate limit throttling.
- **Review Trigger**: If TMDB regional Indian upcoming coverage drops below $80\%$ of trade announcements.

---

### ADR-12: Historical Snapshot & Temporal Leakage Strategy
- **Status**: **Accepted**
- **Context**: Training pre-release models on Kaggle dumps containing post-release IMDb ratings causes fatal data leakage.
- **Options Considered**:
  1. *Ignore Leakage (Use Current IMDb Ratings)*: Methodologically fraudulent; guarantees model failure on genuinely upcoming films.
  2. *Attempt Full Wayback Machine Reconstruction on 10k Films*: Unfeasible due to archive gaps and severe rate limits.
  3. *Time-Invariant Feature Subsets + Autonomous Going-Forward Harvest*: Train historical models strictly on pre-release structural attributes (cast, director, budget, franchise, date); harvest daily popularity snapshots going forward.
- **Decision**: Adopt the **Hybrid Time-Invariant + Live Harvest Strategy**.
- **Rationale**: Scientifically sound, fully defensible in technical interviews, and accumulates a proprietary un-leaked dataset over time.
- **Consequences**: Early-stage historical models have wider uncertainty bands ($\text{SMAPE} \approx 38\%–42\%$).
- **Review Trigger**: None. This protects scientific integrity.

---

### ADR-13: Model Explainability & Feature Attribution Engine
- **Status**: **Accepted**
- **Context**: Revenue predictions must be accompanied by transparent, additive explanations showing why a movie was predicted to succeed or flop.
- **Options Considered**:
  1. *LIME (Local Interpretable Model-agnostic Explanations)*: Slow, local perturbation sampling, non-deterministic.
  2. *Global Feature Importance (Gini / MDI)*: Explains the entire model, but cannot explain individual movie predictions.
  3. *TreeSHAP (SHAP)*: Exact additive local feature attributions in polynomial time; satisfies efficiency and symmetry game-theoretic axioms.
- **Decision**: Adopt **TreeSHAP** via the official `shap` library.
- **Rationale**: TreeSHAP computes exact local feature attributions in $<120\text{ms}$ directly from CatBoost tree structures.
- **Consequences**: Background summary dataset must be pre-computed to maintain $<120\text{ms}$ inference latency.
- **Review Trigger**: None. TreeSHAP is the industry benchmark for GBDT explainability.

---

### ADR-14: Uncertainty Quantification & Prediction Interval Method
- **Status**: **Accepted**
- **Context**: Point forecasts ($y = \$150\text{M}$) create a false illusion of precision. The system must communicate probabilistic uncertainty.
- **Options Considered**:
  1. *Arbitrary Heuristic Bands ($\pm 25\%$)*: Mathematically ungrounded; fails to reflect differing data completeness.
  2. *Quantile Regression*: Requires training separate 10th and 90th percentile models; vulnerable to quantile crossing.
  3. *MAPIE Conformal Prediction*: Model-agnostic, distribution-free, guaranteed finite-sample coverage ($\ge 80\%$) on holdout data.
- **Decision**: Adopt **MAPIE Conformal Prediction** to generate Pessimistic, Expected, and Optimistic prediction intervals.
- **Rationale**: Conformal prediction guarantees that $80\%$ of true future box-office collections will fall inside the predicted bounds.
- **Consequences**: Requires a dedicated calibration split.
- **Review Trigger**: None. Conformal prediction represents cutting-edge ML uncertainty quantification.

---

### ADR-15: Deployment Target & Infrastructure Topology
- **Status**: **Accepted**
- **Context**: The platform must run reliably on the developer's laptop and optionally deploy to a public URL on a $0.00 student budget.
- **Options Considered**:
  1. *AWS / GCP Kubernetes Cluster*: High complexity, immediate billing, completely unjustified for a student project.
  2. *Paid Monolithic VPS (DigitalOcean / Linode)*: $10–$25/month recurring cost.
  3. *Local Docker Compose + Free-Tier Cloud (Vercel + Fly.io + Supabase)*: $0.00 recurring cost, professional Git-driven deployment, local multi-container parity.
- **Decision**: Adopt **Local Docker Compose as Primary Development Target**, with **Vercel (Frontend) + Fly.io (Backend) + Supabase (PostgreSQL)** for optional zero-cost public hosting.
- **Rationale**: Eliminates financial barriers while maintaining strict production-grade containerization and cloud architecture.
- **Consequences**: Free-tier backend services may exhibit brief cold-start spin-up delays after prolonged inactivity.
- **Review Trigger**: If sustained public traffic exceeds free-tier memory or database limits.
