# CineMetrics — Master Documentation Index & Architectural Directory

**Document ID:** 00  
**Version:** 1.0  
**Status:** Approved Documentation Index  
**Last Updated:** 2026-11  

---

## Welcome to the CineMetrics Documentation Suite

This directory contains the complete technical blueprint, research specifications, database designs, machine learning benchmarks, and phase-wise implementation roadmap for **CineMetrics** — an AI-Powered Movie Revenue Prediction, Box-Office Forecasting & Cinema Intelligence Platform.

**CRITICAL INSTRUCTION FOR DEVELOPERS & AI AGENTS:**  
**THE PROJECT IS CURRENTLY IN THE PLANNING STAGE ONLY.**  
Do not begin implementation, execute code development phases, train models, build APIs, or deploy infrastructure until explicitly instructed to transition to Phase 2.

---

## Complete 29-Document Technical Blueprint Directory

| Doc # | Filename | Primary Domain | Core Description & Purpose | Status |
|:---:|---|---|---|:---:|
| **01** | [01_PROJECT_VISION.md](01_PROJECT_VISION.md) | Vision & Scope | Executive summary, 10 core philosophies, target audience, and scope boundaries. | **Approved** |
| **02** | [02_REQUIREMENTS_SPECIFICATION.md](02_REQUIREMENTS_SPECIFICATION.md) | Requirements | Full Functional (FR) and Non-Functional (NFR) software requirements matrix. | **Approved** |
| **03** | [03_PRODUCT_MODES_AND_USER_FLOWS.md](03_PRODUCT_MODES_AND_USER_FLOWS.md) | Product Architecture | Dual operating modes (Movie Explorer & Upcoming Intelligence), wireframes, edge cases. | **Approved** |
| **04** | [04_DATASET_RESEARCH.md](04_DATASET_RESEARCH.md) | Data Sourcing | Official investigation of TMDB, IMDb, The Numbers, Sacnilk, and YouTube APIs. | **Approved** |
| **05** | [05_DATA_ACQUISITION_GUIDE.md](05_DATA_ACQUISITION_GUIDE.md) | Data Engineering | Step-by-step acquisition guide, API key setup, rate limits, and raw lake layout. | **Approved** |
| **06** | [06_UNIFIED_DATASET_DESIGN.md](06_UNIFIED_DATASET_DESIGN.md) | Data Modeling | Canonical identity schema, title normalisation, and missing value imputation rules. | **Approved** |
| **07** | [07_DATA_ENGINEERING_PIPELINE.md](07_DATA_ENGINEERING_PIPELINE.md) | Data Pipeline | End-to-end 16-step data engineering pipeline from raw ingestion to Gold ML splits. | **Approved** |
| **08** | [08_HISTORICAL_SNAPSHOT_STRATEGY.md](08_HISTORICAL_SNAPSHOT_STRATEGY.md) | Temporal Integrity | Leakage prevention protocols, snapshot reconstruction, and 30-feature matrix. | **Approved** |
| **09** | [09_FEATURE_ENGINEERING.md](09_FEATURE_ENGINEERING.md) | Feature Engineering | Full dictionary and mathematical formulas for all 65+ engineered features. | **Approved** |
| **10** | [10_MACHINE_LEARNING_RESEARCH.md](10_MACHINE_LEARNING_RESEARCH.md) | ML Research | Comprehensive GBDT research (CatBoost, LightGBM, XGBoost) and log-transforms. | **Approved** |
| **11** | [11_MODEL_SELECTION_AND_EVALUATION.md](11_MODEL_SELECTION_AND_EVALUATION.md) | Model Evaluation | Temporal walk-forward validation, SMAPE, kappa, Optuna tuning, and baseline gates. | **Approved** |
| **12** | [12_NLP_SENTIMENT_ARCHITECTURE.md](12_NLP_SENTIMENT_ARCHITECTURE.md) | Multilingual NLP | Google MuRIL sentiment engine, Hinglish text handling, and feature synthesis. | **Approved** |
| **13** | [13_UPCOMING_MOVIE_DISCOVERY.md](13_UPCOMING_MOVIE_DISCOVERY.md) | Discovery Engine | Autonomous discovery algorithms, TMDB regional matrix, and enrichment queuing. | **Approved** |
| **14** | [14_AUTOMATED_DATA_INGESTION.md](14_AUTOMATED_DATA_INGESTION.md) | Ingestion Systems | APScheduler cron jobs, retry policies, freshness thresholds, and admin workflows. | **Approved** |
| **15** | [15_PREDICTION_LIFECYCLE.md](15_PREDICTION_LIFECYCLE.md) | ML Lifecycle | Prediction Stages 1–5, Prediction Readiness Score (0–100), and history tracking. | **Approved** |
| **16** | [16_DATA_UPDATE_AND_RETRAINING_POLICY.md](16_DATA_UPDATE_AND_RETRAINING_POLICY.md) | MLOps Policy | Data updates vs. model retraining triggers, performance drift thresholds. | **Approved** |
| **17** | [17_SYSTEM_ARCHITECTURE.md](17_SYSTEM_ARCHITECTURE.md) | Architecture | Modular monolith topology, complete tech stack, directory tree, and data flows. | **Approved** |
| **18** | [18_DATABASE_AND_ER_DIAGRAM.md](18_DATABASE_AND_ER_DIAGRAM.md) | Database Design | Production DDL SQL for all 19 relational entities, indexing, and 10 query patterns. | **Approved** |
| **19** | [19_API_SPECIFICATION.md](19_API_SPECIFICATION.md) | REST API | OpenAPI 3.1 specification for 23 endpoints, schemas, and sample JSON payloads. | **Approved** |
| **20** | [20_UI_UX_DESIGN_GUIDE.md](20_UI_UX_DESIGN_GUIDE.md) | Frontend UI/UX | Dark cinematic design system (`#0A0A0F`), typography, components, and animations. | **Approved** |
| **21** | [21_MLOPS_AND_TRAINING_WORKFLOW.md](21_MLOPS_AND_TRAINING_WORKFLOW.md) | MLOps Workflow | 20-step ML training workflow, local MLflow setup, Optuna spaces, and serialization. | **Approved** |
| **22** | [22_SECURITY_AND_GOVERNANCE.md](22_SECURITY_AND_GOVERNANCE.md) | Security & Ethics | API key safety, slowapi rate limits, attribution licenses, and prediction disclaimers. | **Approved** |
| **23** | [23_TESTING_AND_VALIDATION.md](23_TESTING_AND_VALIDATION.md) | QA & Testing | Test pyramid, Pandera data checks, ML leakage tests, and 50-item checklist. | **Approved** |
| **24** | [24_DEPLOYMENT_AND_INFRASTRUCTURE.md](24_DEPLOYMENT_AND_INFRASTRUCTURE.md) | DevOps & Deploy | Multi-container Docker Compose, zero-cost cloud (Vercel/Fly/Supabase) blueprint. | **Approved** |
| **25** | [25_RESOURCE_AND_FEASIBILITY_ANALYSIS.md](25_RESOURCE_AND_FEASIBILITY_ANALYSIS.md) | Feasibility | Hardware compute profiling, local CPU training feasibility, and $0 monthly cost. | **Approved** |
| **26** | [26_PHASE_WISE_ROADMAP.md](26_PHASE_WISE_ROADMAP.md) | Implementation | Exhaustive 17-phase execution roadmap with tasks, deliverables, and dependencies. | **Approved** |
| **27** | [27_RISKS_AND_MITIGATION.md](27_RISKS_AND_MITIGATION.md) | Risk Governance | Comprehensive risk register (30+ risks) across data, ML, tech, and legal. | **Approved** |
| **28** | [28_FINAL_TECHNICAL_DECISIONS.md](28_FINAL_TECHNICAL_DECISIONS.md) | Architecture Decisions | 15 Architecture Decision Records (ADRs) with rationale and trade-offs. | **Approved** |
| **29** | [29_ACCEPTANCE_CRITERIA.md](29_ACCEPTANCE_CRITERIA.md) | Acceptance Gates | Binding Definition of Done and master 100-item verification checklist. | **Approved** |

---

## Architectural Diagrams (`diagrams/`)

All diagrams are self-contained, valid Mermaid `.mmd` files:
1. [`system_architecture.mmd`](../diagrams/system_architecture.mmd): Flowchart of Frontend $\rightarrow$ FastAPI $\rightarrow$ ML Engine $\rightarrow$ DB.
2. [`data_pipeline.mmd`](../diagrams/data_pipeline.mmd): 16-step data engineering flow from raw APIs to Gold splits.
3. [`automated_discovery.mmd`](../diagrams/automated_discovery.mmd): APScheduler autonomous discovery and enrichment loop.
4. [`ml_training_pipeline.mmd`](../diagrams/ml_training_pipeline.mmd): Feature engineering, Optuna tuning, and MLflow logging.
5. [`prediction_lifecycle.mmd`](../diagrams/prediction_lifecycle.mmd): State diagram of prediction progression across Stages 1–5.
6. [`database_erd.mmd`](../diagrams/database_erd.mmd): 19-entity relational Entity-Relationship Diagram.
7. [`application_flow.mmd`](../diagrams/application_flow.mmd): User interaction flow across Mode 1 and Mode 2.

---

## Operational Trackers (`planning/`)

1. [`DATASET_TRACKER.md`](../planning/DATASET_TRACKER.md): Raw dataset acquisition status and checksum registry.
2. [`DATA_SOURCE_COMPARISON.md`](../planning/DATA_SOURCE_COMPARISON.md): Multi-source comparison matrix and zero-cost stack.
3. [`MODEL_COMPARISON_MATRIX.md`](../planning/MODEL_COMPARISON_MATRIX.md): Benchmark matrix for 14 candidate algorithms.
4. [`FEATURE_DICTIONARY.md`](../planning/FEATURE_DICTIONARY.md): Complete 65-feature master dictionary.
5. [`HISTORICAL_SNAPSHOT_TRACKER.md`](../planning/HISTORICAL_SNAPSHOT_TRACKER.md): Temporal reconstructibility audit and benchmark ledger.
6. [`API_ENDPOINT_TRACKER.md`](../planning/API_ENDPOINT_TRACKER.md): Implementation tracker for 23 REST endpoints.
7. [`PHASE_TRACKER.md`](../planning/PHASE_TRACKER.md): Master phase tracking dashboard (Phases 1–17).
8. [`OPEN_DECISIONS.md`](../planning/OPEN_DECISIONS.md): 25+ architectural decisions and trade-offs.
9. [`RESEARCH_REFERENCES.md`](../planning/RESEARCH_REFERENCES.md): Academic literature, official doc links, and visual benchmarks.

---

## Recommended Developer Reading Orders

### Path A: Machine Learning & Data Science Focus
1. [01_PROJECT_VISION.md](01_PROJECT_VISION.md) $\rightarrow$ Core principles.
2. [08_HISTORICAL_SNAPSHOT_STRATEGY.md](08_HISTORICAL_SNAPSHOT_STRATEGY.md) $\rightarrow$ Leakage prevention rules.
3. [09_FEATURE_ENGINEERING.md](09_FEATURE_ENGINEERING.md) $\rightarrow$ Feature formulas.
4. [10_MACHINE_LEARNING_RESEARCH.md](10_MACHINE_LEARNING_RESEARCH.md) $\rightarrow$ Algorithm research.
5. [11_MODEL_SELECTION_AND_EVALUATION.md](11_MODEL_SELECTION_AND_EVALUATION.md) $\rightarrow$ Evaluation & metrics.
6. [12_NLP_SENTIMENT_ARCHITECTURE.md](12_NLP_SENTIMENT_ARCHITECTURE.md) $\rightarrow$ MuRIL sentiment.
7. [15_PREDICTION_LIFECYCLE.md](15_PREDICTION_LIFECYCLE.md) $\rightarrow$ Stages & readiness scoring.
8. [21_MLOPS_AND_TRAINING_WORKFLOW.md](21_MLOPS_AND_TRAINING_WORKFLOW.md) $\rightarrow$ Training pipeline.

### Path B: Full-Stack Engineering & Architecture Focus
1. [01_PROJECT_VISION.md](01_PROJECT_VISION.md) $\rightarrow$ Vision & philosophy.
2. [03_PRODUCT_MODES_AND_USER_FLOWS.md](03_PRODUCT_MODES_AND_USER_FLOWS.md) $\rightarrow$ Dual-mode UX workflows.
3. [17_SYSTEM_ARCHITECTURE.md](17_SYSTEM_ARCHITECTURE.md) $\rightarrow$ Modular monolith blueprint.
4. [18_DATABASE_AND_ER_DIAGRAM.md](18_DATABASE_AND_ER_DIAGRAM.md) $\rightarrow$ DDL SQL schema (19 tables).
5. [19_API_SPECIFICATION.md](19_API_SPECIFICATION.md) $\rightarrow$ OpenAPI 3.1 endpoints.
6. [20_UI_UX_DESIGN_GUIDE.md](20_UI_UX_DESIGN_GUIDE.md) $\rightarrow$ Dark cinematic UI tokens.
7. [24_DEPLOYMENT_AND_INFRASTRUCTURE.md](24_DEPLOYMENT_AND_INFRASTRUCTURE.md) $\rightarrow$ Docker Compose & cloud setup.
8. [26_PHASE_WISE_ROADMAP.md](26_PHASE_WISE_ROADMAP.md) $\rightarrow$ 17-phase execution plan.
