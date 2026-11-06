# CineMetrics — Resource and Feasibility Analysis

**Document ID:** DOC-25  
**Version:** 1.0  
**Status:** Approved for Planning  
**Last Reviewed:** 2024-01-01  
**Owner:** Project Architecture Team  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Hardware Requirements Assessment](#2-hardware-requirements-assessment)
3. [Financial Cost Assessment](#3-financial-cost-assessment)
4. [Dataset Size Estimates](#4-dataset-size-estimates)
5. [Feasibility Verdict Per Model](#5-feasibility-verdict-per-model)
6. [Time Estimates Per Phase](#6-time-estimates-per-phase)
7. [Risk Mitigation for Student Resources](#7-risk-mitigation-for-student-resources)
8. [Overall Feasibility Verdict](#8-overall-feasibility-verdict)

---

## 1. Executive Summary

CineMetrics is designed to be **fully buildable by a single student developer** without cloud GPU access, enterprise tools, or significant financial outlay. This document provides a realistic assessment of the hardware, software, financial, and time resources required at each project phase.

**Key conclusions:**

- **Cost:** $0/month if staying within free tiers. Maximum $30/month if opting for convenience upgrades.
- **Hardware:** Any modern laptop (2019 or later) with 8GB RAM is sufficient for all phases except NLP model fine-tuning, which is handled via Google Colab free tier.
- **Time:** 6–8 months at a part-time student pace (15–20 hours/week). 3–4 months full-time.
- **Feasibility:** All planned ML models are feasible. CatBoost, LightGBM, and XGBoost are the primary candidates and run comfortably on a student laptop.
- **Main bottleneck:** Data engineering and entity resolution, not ML training.

> [!IMPORTANT]
> This analysis is calibrated for a **single student developer** with intermediate Python skills. Teams of 2-3 developers would complete this significantly faster.

---

## 2. Hardware Requirements Assessment

### 2.1 Data Engineering Phase

The data engineering phase is I/O and memory-bound, not compute-bound. The following hardware assessment applies:

| Resource | Minimum | Preferred | Notes |
|---|---|---|---|
| RAM | 8 GB | 16 GB | IMDb title.basics loads ~500MB into pandas; with joins, peak usage ~4-6 GB |
| Storage | 15 GB free | 30 GB free | 10GB raw data + 5GB processed + 10GB working space |
| CPU | Intel i5 (2018+) / M1 | Intel i7 / M2 | CPU is barely a factor; disk I/O dominates |
| Disk type | HDD (slower) | SSD | IMDb dataset loading: ~10 min HDD, ~3 min SSD |
| Internet | 10 Mbps | 50+ Mbps | For initial dataset downloads only |

**Memory-intensive operations and their expected RAM usage:**

| Operation | Estimated Peak RAM |
|---|---|
| Load IMDb title.basics (~10M rows) | ~600 MB |
| Load TMDB paginated results (~500K movies) | ~200 MB |
| Merge IMDb + TMDB on tmdb_id / imdb_id | ~1.5 GB (pre-dedup) |
| Fuzzy title matching (rapidfuzz, 10K unresolved) | ~300 MB |
| Full unified_movies DataFrame (all columns, 15K movies) | ~50 MB |
| Pandas groupby + feature aggregation | ~500 MB peak |

**Mitigation for 8GB RAM systems:**
- Use `dtype` specification when loading CSVs to reduce memory footprint by ~40%.
- Load IMDb files in chunks using `pandas.read_csv(chunksize=100000)`.
- Use DuckDB for large joins (DuckDB has excellent out-of-core query support).
- Filter to movies-only before loading into pandas (IMDb includes TV, shorts, etc.).

### 2.2 ML Training Phase

**CatBoost (Primary Model)**

| Dataset size | Features | CPU Time | GPU Time | RAM |
|---|---|---|---|---|
| 5,000 movies | 50 features | ~5 min | ~30 sec | ~500 MB |
| 10,000 movies | 50 features | ~15 min | ~2 min | ~800 MB |
| 15,000 movies | 50 features | ~25 min | ~3 min | ~1.2 GB |

- CatBoost natively handles categorical features without one-hot encoding, reducing memory vs. sklearn models.
- CatBoost has excellent CPU parallelization; `-thread_count -1` uses all cores.
- **Verdict:** Fully feasible on any modern laptop.

**LightGBM**

| Dataset size | Features | CPU Time | RAM |
|---|---|---|---|
| 10,000 movies | 50 features | ~5 min | ~400 MB |

- LightGBM is the fastest gradient boosting library for CPU training.
- **Verdict:** Fully feasible on any modern laptop.

**XGBoost**

| Dataset size | Features | CPU Time | RAM |
|---|---|---|---|
| 10,000 movies | 50 features | ~8 min | ~600 MB |

- XGBoost uses slightly more memory than LightGBM for equivalent datasets.
- **Verdict:** Fully feasible on any modern laptop.

**Optuna Hyperparameter Search**

| Trials | Model | Estimated CPU Time |
|---|---|---|
| 100 trials | CatBoost | 3–5 hours |
| 100 trials | LightGBM | 1–2 hours |
| 100 trials | XGBoost | 2–4 hours |

- Optuna supports parallel trial execution (`n_jobs=-1`) which halves time on quad-core machines.
- **Strategy:** Run Optuna overnight or on Google Colab.
- **Verdict:** Feasible on laptop (run overnight); faster on Colab.

**NLP Model Fine-Tuning (DistilBERT / MuRIL)**

| Task | Hardware | Estimated Time |
|---|---|---|
| DistilBERT inference only (no fine-tuning) | CPU | 1–2 sec/prediction (batch OK) |
| DistilBERT fine-tuning (5K samples, 3 epochs) | CPU (8GB RAM) | 4–8 hours |
| DistilBERT fine-tuning (5K samples, 3 epochs) | Colab T4 GPU | 15–30 minutes |
| MuRIL inference only | CPU | 2–4 sec/prediction |
| MuRIL fine-tuning | CPU | 6–12 hours (impractical) |
| MuRIL fine-tuning | Colab T4 GPU | 30–60 minutes |

> [!WARNING]
> Fine-tuning transformer models on CPU is technically feasible but strongly not recommended. Use Google Colab's free T4 GPU for all fine-tuning tasks. CPU fine-tuning risks session timeout and thermal throttling on laptops.

**TabNet and Deep Learning Tabular Models**

| Model | CPU Time | GPU Time | Assessment |
|---|---|---|---|
| TabNet (PyTorch) | ~40 min (10K samples) | ~5 min | Poor ROI — worse than CatBoost for small tabular datasets |
| MLP Neural Network | ~20 min | ~2 min | Feasible; likely worse than CatBoost |

- **Recommendation:** Do not use TabNet or MLP for primary revenue prediction. CatBoost/LightGBM consistently outperform deep learning on small (<50K sample) tabular datasets.

### 2.3 Inference / Backend Serving

| Component | Hardware | Latency | Notes |
|---|---|---|---|
| CatBoost inference | CPU (any) | < 100 ms | Well within API response time SLA |
| SHAP TreeExplainer | CPU (any) | 200–500 ms | Acceptable for on-demand API calls |
| SHAP on CatBoost (batch, 100 movies) | CPU | ~5–10 sec | Pre-compute in background job |
| Conformal predictor interval | CPU (any) | < 10 ms | Negligible |
| DistilBERT sentiment inference | CPU | 1–2 sec | Pre-compute batch; not real-time |
| DistilBERT sentiment inference | GPU (Colab/cloud) | 50–100 ms | Real-time feasible with GPU |
| FastAPI endpoint (full prediction) | CPU | ~300–700 ms | CatBoost + SHAP + serialization |

**Recommended architecture for student hardware:**
- Pre-compute sentiment scores nightly in a batch job.
- Pre-compute SHAP explanations nightly for all active movies.
- Serve pre-computed values via FastAPI endpoints with sub-50ms response time.
- Only compute live predictions on demand when triggered by the prediction update policy.

### 2.4 Google Colab Free Tier — Capabilities and Limitations

| Capability | Detail |
|---|---|
| GPU type | NVIDIA T4 (15GB VRAM) — not guaranteed |
| Session limit | ~12 hours continuous runtime |
| RAM | ~12.7 GB system RAM |
| Storage | ~100 GB temporary disk |
| Cost | FREE |
| Availability | Not always guaranteed (may queue) |

**Recommended use cases for Colab:**
1. NLP model fine-tuning (MuRIL, DistilBERT, IndicBERT).
2. Optuna hyperparameter search (run as long training session).
3. Initial large dataset preprocessing (if local RAM is 8 GB).

**NOT suitable for Colab:**
- Persistent scheduled jobs (Colab sessions terminate after inactivity).
- Production serving (not a server; use Fly.io or Railway instead).
- Storing data permanently (Colab disk is wiped on session end — always save to Google Drive or local).

**Colab workflow:**
1. Mount Google Drive: `drive.mount('/content/drive')`.
2. Copy datasets from Drive to Colab `/content/` for speed.
3. Train model and save checkpoint back to Drive every epoch.
4. Download final model files after training.

---

## 3. Financial Cost Assessment

### 3.1 Free Tier — Recommended Starting Point

The entire CineMetrics project can be built and operated at **$0/month** using the following free-tier resources:

| Service | Use Case | Free Tier Details | Cost |
|---|---|---|---|
| **TMDB API** | Movie metadata, cast, trailers | Unlimited non-commercial requests | FREE |
| **IMDb Datasets** | Movie catalog, ratings | Non-commercial download | FREE |
| **Kaggle Datasets** | TMDB 5000, Movies Dataset | Registered account required | FREE |
| **Google Trends (pytrends)** | Search trend signals | Unofficial; rate limited | FREE |
| **YouTube Data API v3** | Trailer views, search | 10,000 units/day quota | FREE |
| **Reddit API (PRAW)** | Sentiment from r/bollywood etc. | 100 QPM rate limit (OAuth) | FREE |
| **PostgreSQL (local)** | Primary database | Local installation | FREE |
| **Supabase Free Tier** | Cloud PostgreSQL hosting | 500MB database, 2 projects | FREE |
| **MLflow (local)** | Experiment tracking | Self-hosted | FREE |
| **GitHub** | Version control, CI/CD | Unlimited public/private repos | FREE |
| **Google Colab** | GPU for NLP training | T4 GPU, 12h sessions | FREE |
| **Vercel** | Frontend deployment | 100GB bandwidth/month | FREE |
| **Fly.io** | Backend deployment | 3 shared-CPU VMs, 160GB bandwidth | FREE |
| **DuckDB** | Analytical queries during dev | Python library | FREE |
| **SQLite** | Development database | Python built-in | FREE |
| **HuggingFace Hub** | Model downloads (MuRIL, DistilBERT) | Public models | FREE |

**Total monthly cost (free tier): $0**

### 3.2 Potential Paid Upgrades (Optional)

These upgrades are **not required** for initial build but may be considered if free tier limitations become a bottleneck:

| Service | Use Case | Cost | Trigger for Purchase |
|---|---|---|---|
| **Supabase Pro** | Larger database, more API calls | $25/month | When free 500MB is insufficient |
| **Railway Pro** | Always-on backend (no sleep) | $5/month | When Fly.io free tier is too restrictive |
| **Render Starter** | Alternative backend hosting | $7/month | Alternative to Railway |
| **Google Colab Pro** | Priority GPU access, longer sessions | $9.99/month | If T4 availability becomes unreliable |
| **Cloudflare Workers** | Edge caching for API responses | ~$5/month | When frontend traffic grows |
| **Upstash Redis** | Serverless Redis for caching | $0–10/month | When caching is needed in production |

**Maximum plausible monthly cost (all paid upgrades): ~$60/month**  
**Realistic cost for a solo student project: $0–$10/month**

### 3.3 Data Sources — Commercial Pricing (SKIP for initial build)

The following data sources offer richer or more reliable data but at commercial pricing. They should be **skipped** for the initial build:

| Source | Data Type | Estimated Cost | Decision |
|---|---|---|---|
| **Ormax Media** | Indian box office, OTT viewership | Custom enterprise pricing | SKIP — too expensive |
| **The Numbers (data license)** | Hollywood financial data | Contact for pricing | SKIP — use public data |
| **Box Office Mojo (data export)** | Box office history | Contact for pricing | SKIP — use IMDB datasets |
| **Comscore** | Box office, screen counts | Enterprise pricing | SKIP |
| **Sacnilk API (commercial)** | Indian collections | Unknown pricing | SKIP — scrape public data only |

### 3.4 API Rate Limit Summary

| API | Daily Limit | Rate Limit | Mitigation |
|---|---|---|---|
| TMDB | No hard daily limit (non-commercial fair use) | 50 requests/second | Add `time.sleep(0.02)` between calls |
| YouTube Data API v3 | 10,000 units/day | — | 1 search = 100 units; 1 video detail = 1 unit |
| Google Trends (pytrends) | No official limit | Aggressive rate limiting | Use `time.sleep(1)` between queries |
| Reddit (PRAW) | 100 QPM (OAuth app) | — | Batch requests; cache results |
| IMDb datasets | One-time download | — | No API; download once |
| HuggingFace Inference API | 30K chars/month (free) | — | Use local inference; not the API |

---

## 4. Dataset Size Estimates

### 4.1 Raw Dataset Sizes

| Dataset | Source | Raw File Size | Row Count | After Movie Filter | Notes |
|---|---|---|---|---|---|
| IMDb title.basics.tsv.gz | IMDb | ~200 MB compressed (~700MB uncompressed) | ~10 million | ~700,000 (movies only) | Includes TV, shorts, etc. |
| IMDb title.ratings.tsv.gz | IMDb | ~25 MB | ~1.5 million | ~700,000 | Ratings for all title types |
| IMDb title.crew.tsv.gz | IMDb | ~200 MB | ~10 million | ~700,000 | Directors and writers |
| IMDb title.principals.tsv.gz | IMDb | ~500 MB | ~50 million | ~3.5 million | Cast and crew |
| IMDb name.basics.tsv.gz | IMDb | ~300 MB | ~12 million | ~12 million | Person records |
| TMDB paginated discovery | TMDB API | N/A (API) | ~500,000 | ~500,000 | JSON responses; ~2GB stored |
| Kaggle TMDB 5000 | Kaggle | ~5 MB | 4,803 | 4,803 | Has budgets and revenues |
| Kaggle Movies Dataset | Kaggle | ~50 MB | ~45,000 | ~45,000 | Multiple CSV files |
| Bollywood dataset (best Kaggle) | Kaggle | 1–10 MB (ESTIMATED) | 5,000–15,000 | 5,000–15,000 | Quality varies by dataset |
| **Total raw storage** | — | **~10 GB** | — | — | Including API cache |

### 4.2 Processed Dataset Sizes

| Artifact | Format | Estimated Size | Row Count | Notes |
|---|---|---|---|---|
| unified_movies.parquet | Parquet | ~50 MB | 15,000–50,000 | After dedup and merge |
| features_v1.parquet | Parquet | ~30 MB | 15,000 | Feature-engineered training data |
| training_set.parquet | Parquet | ~20 MB | 10,000–12,000 | Train split only |
| validation_set.parquet | Parquet | ~5 MB | 1,500–2,000 | Val split |
| test_set.parquet | Parquet | ~5 MB | 1,500–2,000 | Test split |
| sentiment_corpus.parquet | Parquet | ~200 MB | 500,000 comments | Raw scraped text |
| **Total processed storage** | — | **~500 MB** | — | Parquet compression efficient |

### 4.3 Usable Training Data Estimates

This is the most critical figure for ML model quality:

| Region / Industry | Estimated Movies with Full Features | Estimated Movies with Verified Financials | Notes |
|---|---|---|---|
| Hollywood (English) | 20,000–50,000 | 5,000–10,000 | TMDB + Kaggle + IMDb |
| Bollywood (Hindi) | 3,000–8,000 | 1,000–3,000 (ESTIMATED) | Quality varies; best Kaggle datasets |
| South Indian (combined) | 1,000–3,000 | 500–1,500 (ESTIMATED) | Tamil, Telugu, Kannada, Malayalam |
| Other Indian languages | 500–1,000 | 100–300 (ESTIMATED) | Very sparse data |
| **Total usable training set** | **~5,000–15,000** | — | Conservative estimate after cleaning |

> [!NOTE]
> The 5,000–15,000 estimate is for movies that have BOTH complete feature data AND verified financial targets. Many movies will have partial features and can be used for feature engineering but not for target-supervised training.

**Implications for model selection:**
- 5,000–15,000 labeled examples: Gradient boosting (CatBoost/LightGBM/XGBoost) is the optimal choice — no need for deep learning.
- Neural networks typically need >100,000 labeled examples to outperform tree methods on tabular data.
- With this dataset size, model performance is primarily limited by **data quality**, not **model capacity**.

---

## 5. Feasibility Verdict Per Model

### 5.1 Regression Models (Revenue Prediction)

| Model | Local Laptop Feasible? | GPU Needed? | Expected Relative Performance | Recommendation |
|---|---|---|---|---|
| **Mean Baseline** | ✅ Trivial | No | Worst (baseline floor) | Use as baseline sanity check |
| **Median Baseline** | ✅ Trivial | No | Slightly better than mean | Use as baseline |
| **Linear Regression** | ✅ Trivial | No | Poor (box office is nonlinear) | Use for feature selection insights |
| **Ridge / Lasso** | ✅ Trivial | No | Slightly better than Linear | Useful for regularization study |
| **Random Forest** | ✅ ~10–20 min | No | Good baseline | Use for comparison |
| **Extra Trees** | ✅ ~5–10 min | No | Similar to Random Forest | Use for comparison |
| **Gradient Boosting (sklearn)** | ✅ ~15–30 min | No | Good; slower than XGB/LGB | Useful for comparison |
| **XGBoost** | ✅ ~8 min | Optional | Very good | Strong candidate |
| **LightGBM** | ✅ ~5 min | Optional | Very good; fastest | Strong candidate |
| **CatBoost** | ✅ ~15 min | Optional | **Best for categorical-heavy data** | **PRIMARY RECOMMENDATION** |
| **HistGradientBoosting** | ✅ ~10 min | No | Very good; sklearn native | Useful comparison |
| **SVR (RBF kernel)** | ⚠️ Slow >5K samples | No | Moderate | Skip for large dataset |
| **MLP Neural Network** | ✅ ~20 min | Recommended | Below CatBoost for this data size | Low priority |
| **TabNet** | ⚠️ Slow on CPU | Recommended | Below CatBoost for this data size | **NOT RECOMMENDED** |

### 5.2 Classification Models (Success Category)

| Model | Local Laptop Feasible? | Notes |
|---|---|---|
| **Logistic Regression** | ✅ | Good baseline for classification |
| **Random Forest Classifier** | ✅ | Solid; good feature importance |
| **LightGBM Classifier** | ✅ | Very fast; strong performance |
| **CatBoost Classifier** | ✅ | Best for multi-class with categoricals |
| **XGBoost Classifier** | ✅ | Strong |
| **MLP Classifier** | ✅ | Lower priority |

### 5.3 NLP Sentiment Models

| Task | Feasibility | Hardware | Notes |
|---|---|---|---|
| **Inference-only (DistilBERT)** | ✅ FULLY FEASIBLE | CPU (8GB RAM) | 1–2 sec/prediction; batch OK |
| **Fine-tuning DistilBERT** | ⚠️ FEASIBLE but slow | CPU: 4–8 hours | Strongly recommend Colab GPU |
| **Inference-only (MuRIL)** | ✅ FEASIBLE | CPU (8GB RAM) | Slower than DistilBERT; acceptable for batch |
| **Fine-tuning MuRIL** | ⚠️ CHALLENGING on CPU | CPU: 8–16 hours | Use Colab T4 GPU |
| **inference-only (IndicBERT)** | ✅ FEASIBLE | CPU | Good for Indian language tasks |
| **Real-time sub-100ms sentiment** | ❌ CHALLENGING on CPU | GPU required | Pre-compute instead |

**Recommended architecture for sentiment:**
- Fine-tune MuRIL/DistilBERT on Colab (once).
- Save model locally.
- Run batch inference nightly on new comments.
- Store results in `sentiment_snapshots` table.
- API serves pre-computed sentiment — no live inference on request.

### 5.4 Uncertainty Quantification

| Method | Feasibility | Implementation Complexity | Notes |
|---|---|---|---|
| **Conformal Prediction (MAPIE)** | ✅ FULLY FEASIBLE | Low | pip install mapie; wraps any sklearn model |
| **Quantile Regression (LightGBM)** | ✅ FULLY FEASIBLE | Low | Native LightGBM parameter |
| **Bootstrap Ensemble** | ✅ FEASIBLE | Medium | Train N models; compute interval |
| **Bayesian optimization (Optuna)** | ✅ FEASIBLE | Low–Medium | For hyperparameter search only |
| **Deep Ensembles** | ⚠️ Resource-intensive | High | Low priority for this project |

### 5.5 Explainability

| Method | Feasibility | Performance Impact | Notes |
|---|---|---|---|
| **SHAP TreeExplainer** | ✅ FULLY FEASIBLE | 200–500ms/prediction | Purpose-built for tree models |
| **SHAP DeepExplainer** | ⚠️ Slow on CPU | 2–5 sec/prediction | For NLP model only |
| **LIME** | ✅ FEASIBLE | ~1 sec/prediction | Fallback if SHAP issues arise |
| **Permutation importance** | ✅ FULLY FEASIBLE | 1–5 min batch | For global feature importance |
| **CatBoost built-in importance** | ✅ Instant | Negligible | Good supplement to SHAP |

---

## 6. Time Estimates Per Phase

The following estimates assume a **single student developer** working part-time (15–20 hours/week). Full-time estimates are roughly 3× faster.

| Phase | Name | Estimated Duration | Key Bottleneck | Notes |
|---|---|---|---|---|
| **1** | Research and Requirements | 1–2 weeks | Writing/decisions | ✅ COMPLETE — this documentation |
| **2** | Dataset Acquisition | 1–2 weeks | API setup, download time | IMDb download is fast; TMDB pagination takes time |
| **3** | Unified Data Engineering | 2–3 weeks | Entity resolution | Fuzzy matching and conflict resolution are complex |
| **4** | Exploratory Data Analysis | 1 week | Interpretation | Jupyter notebooks; relatively quick |
| **5** | Feature Engineering | 2 weeks | Implementation complexity | 60+ features across multiple categories |
| **6** | Baseline Machine Learning | 1 week | — | Quick wins; scikit-learn pipelines |
| **7** | Advanced Revenue Prediction | 2–3 weeks | Optuna tuning (overnight) | CatBoost/LightGBM/XGBoost; hyperparameter search |
| **8** | Success Classification | 1–2 weeks | — | Builds on Phase 7 infrastructure |
| **9** | Audience Sentiment Analysis | 2 weeks | Fine-tuning on Colab | Multilingual complexity; Colab sessions |
| **10** | Explainability and Uncertainty | 1 week | SHAP integration | MAPIE + SHAP + API layer |
| **11** | Automated Movie Discovery | 2–3 weeks | Scheduler complexity | APScheduler + TMDB polling + dedup logic |
| **12** | Continuous Data Updates | 1–2 weeks | — | Builds on Phase 11 infrastructure |
| **13** | Backend Development | 3–4 weeks | Schema design, authentication | FastAPI + SQLAlchemy + Alembic |
| **14** | Frontend Development | 4–6 weeks | Most time-consuming phase | Next.js + Tailwind + Recharts + animations |
| **15** | Advanced Product Features | 2–3 weeks | — | Comparison, watchlist, alerts |
| **16** | Integration and Deployment | 2–3 weeks | Infrastructure setup | Fly.io + Vercel + CI/CD |
| **17** | Testing and Final Evaluation | 2 weeks | Writing tests | Pytest + E2E + load testing |
| **TOTAL** | — | **28–44 weeks** | — | **6–8 months part-time; 3–4 months full-time** |

### 6.1 Critical Path

The following phases are **on the critical path** (each must complete before the next can begin):

```
Phase 2 → Phase 3 → Phase 5 → Phase 7 → Phase 10 → Phase 13 → Phase 14 → Phase 16 → Phase 17
```

The following phases can be developed **in parallel** with phases on the critical path:

- Phase 4 (EDA) can begin during Phase 3.
- Phase 6 (Baseline ML) can begin during Phase 5.
- Phase 8 (Classification) can begin during Phase 7.
- Phase 9 (Sentiment) can begin any time after Phase 3.
- Phase 11 (Discovery) can begin any time after Phase 3.

### 6.2 Minimum Viable Product (MVP) Timeline

If the goal is an MVP (working predictions for major movies + basic API + basic UI), the minimum path is:

| Phase | Effort |
|---|---|
| Phase 2: Dataset Acquisition | 1 week |
| Phase 3: Data Engineering (simplified) | 1–2 weeks |
| Phase 7: CatBoost training (no Optuna) | 1 week |
| Phase 13: FastAPI backend (3 endpoints) | 1–2 weeks |
| Phase 14: Frontend (single prediction page) | 2 weeks |

**MVP timeline: 6–8 weeks of focused work.**

---

## 7. Risk Mitigation for Student Resources

### 7.1 Compute Mitigation

| Risk | Mitigation |
|---|---|
| Local GPU unavailable for NLP fine-tuning | Use Google Colab free T4 GPU |
| Colab session times out during long training | Save checkpoint every epoch to Google Drive; resume from checkpoint |
| 8GB RAM insufficient for large pandas operations | Use DuckDB for large joins; chunk-load CSVs |
| Optuna search takes too long | Reduce to 50 trials; run overnight; use Colab |
| CatBoost training slow | Use `task_type='GPU'` on Colab; use `border_count=32` for faster CPU training |

### 7.2 Storage Mitigation

| Risk | Mitigation |
|---|---|
| Raw datasets take >15GB disk space | Store compressed (gzip); delete duplicates after processing |
| Model artifacts accumulate | Use MLflow to track only the top-N models; delete inferior runs |
| API cache grows unbounded | Implement 30-day TTL on TMDB cache; re-fetch only changed records |

### 7.3 Cost Mitigation

| Risk | Mitigation |
|---|---|
| YouTube API quota exhausted (10K units/day) | Batch trailer searches; cache results aggressively |
| TMDB API rate-limited | Use exponential backoff; cache responses in SQLite |
| Reddit API pricing changes | Cache posts; reduce polling frequency; use pushshift.io alternatives if needed |
| Cloud hosting costs spike | Use Fly.io free tier with scale-to-zero; monitor usage |

### 7.4 Development Time Mitigation

| Risk | Mitigation |
|---|---|
| Entity resolution takes longer than expected | Use rapidfuzz pre-built functions; cap fuzzy matching at 10K unresolved records |
| NLP multilingual complexity | Start with English-only sentiment; add Hindi later as Phase 9b |
| Frontend development time underestimated | Use pre-built Recharts/shadcn components; don't reinvent UI |
| Testing phase skipped due to time pressure | Write at least smoke tests for all API endpoints; use pytest fixtures |
| Feature engineering bugs cause data leakage | Implement temporal validation checks in CI pipeline |

### 7.5 Development Environment Recommendations

| Component | Recommended Tool | Reason |
|---|---|---|
| Package management | `uv` (ultra-fast pip replacement) or `conda` | Dependency resolution is faster |
| Notebooks | Jupyter Lab | Better than classic Jupyter |
| IDE | VS Code with Python + Pylance extensions | Best debugging support |
| Database GUI | DBeaver (free) or TablePlus | Visual schema inspection |
| API testing | Bruno (free) or Postman | Test FastAPI endpoints locally |
| Version control | Git + GitHub | Standard |
| Profiling | py-spy or cProfile | For memory/CPU bottleneck detection |
| Environment variables | python-dotenv | For API keys; never commit to git |

---

## 8. Overall Feasibility Verdict

### 8.1 Technical Feasibility

| Dimension | Assessment | Confidence |
|---|---|---|
| Data availability (Hollywood) | ✅ FULLY FEASIBLE | High |
| Data availability (Indian cinema) | ⚠️ PARTIALLY FEASIBLE | Medium — data quality varies |
| ML model training | ✅ FULLY FEASIBLE | High |
| NLP sentiment | ✅ FEASIBLE with Colab | High |
| Real-time inference | ✅ FEASIBLE with pre-computation | High |
| Backend API | ✅ FULLY FEASIBLE | High |
| Frontend dashboard | ✅ FULLY FEASIBLE | High |
| Deployment | ✅ FULLY FEASIBLE (free tier) | High |

### 8.2 Resource Feasibility Summary

| Resource | Required | Available | Gap |
|---|---|---|---|
| Development hardware | 8GB RAM laptop | Standard student hardware | None |
| GPU (training) | Optional (for NLP) | Google Colab free T4 | None |
| Budget | $0 | $0 | None |
| Development time | 6–8 months (part-time) | Student semester(s) | Manageable |
| Python skills | Intermediate | Assumed | None |
| ML knowledge | Intermediate | Assumed | None |

### 8.3 Final Verdict

> **CineMetrics is fully feasible as a student solo project.** The primary challenges are data engineering complexity (entity resolution, currency conversion, multilingual text handling) and the time investment required for the frontend. The ML components are straightforward to implement and train on consumer hardware. With disciplined use of free-tier services and strategic use of Google Colab for GPU-intensive tasks, the project can be completed at zero cost.

---

*Cross-references: [../docs/04_DATA_SOURCES_AND_ACQUISITION.md](04_DATA_SOURCES_AND_ACQUISITION.md) | [../docs/13_ML_TRAINING_PIPELINE.md](13_ML_TRAINING_PIPELINE.md) | [../planning/PHASE_TRACKER.md](../planning/PHASE_TRACKER.md)*
