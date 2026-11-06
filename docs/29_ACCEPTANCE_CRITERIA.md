# CineMetrics — Master Quality Standards & Project Acceptance Criteria

**Document ID:** 29  
**Version:** 1.0  
**Status:** Approved Master Acceptance Specification  
**Last Updated:** 2026-11  
**Related Docs:** [Requirements Specification](02_REQUIREMENTS_SPECIFICATION.md) | [Testing & Validation](23_TESTING_AND_VALIDATION.md) | [Phase Roadmap](26_PHASE_WISE_ROADMAP.md)

---

## Table of Contents

1. [Acceptance Governance & Sign-Off Framework](#1-acceptance-governance--sign-off-framework)
2. [Data Engineering & Lake Acceptance Standards](#2-data-engineering--lake-acceptance-standards)
3. [Machine Learning Scientific Benchmarks & Quality Gates](#3-machine-learning-scientific-benchmarks--quality-gates)
4. [Backend API Architecture & Performance SLAs](#4-backend-api-architecture--performance-slas)
5. [Frontend UI/UX, Aesthetics & Accessibility Standards](#5-frontend-ui-ux-aesthetics--accessibility-standards)
6. [End-to-End User Experience Acceptance Criteria](#6-end-to-end-user-experience-acceptance-criteria)
7. [Automated Discovery Engine Operational Standards](#7-automated-discovery-engine-operational-standards)
8. [Portfolio Presentation & Academic Defense Criteria](#8-portfolio-presentation--academic-defense-criteria)
9. [The Master One-Hundred-Item Verification Checklist](#9-the-master-one-hundred-item-verification-checklist)

---

## 1. Acceptance Governance & Sign-Off Framework

This document establishes the binding, non-negotiable **Definition of Done (DoD)** for the CineMetrics platform. No implementation phase is considered complete, and the project cannot be designated as production-ready, until all criteria defined herein are demonstrably satisfied.

### Sign-Off Tiers:
- **Level 1 (Data & Scientific Integrity)**: Mathematical correctness, absence of temporal leakage, validated calibration.
- **Level 2 (Software Engineering & Reliability)**: Unit/integration pass rates, API latency SLAs, zero unhandled 500 errors.
- **Level 3 (User Experience & Aesthetic Polish)**: Lighthouse scores, WCAG accessibility, fluid 60fps animations.
- **Level 4 (Portfolio & Governance Rigor)**: Legal attribution compliance, comprehensive documentation, reproducible setup.

---

## 2. Data Engineering & Lake Acceptance Standards

1. **Entity Resolution Accuracy**: Record linkage combining TMDB IDs, IMDb tconsts, and RapidFuzz title-year matching must achieve $\ge 95.0\%$ precision and recall on the 200-film manually curated ground-truth test set.
2. **Zero Duplicate Entities**: The canonical `movies` table must contain zero duplicate physical releases across foreign and regional titles.
3. **Financial Standardization Consistency**:
   - 100% of historical theatrical collections and budgets must be standardized to constant 2024 Real USD and INR Crores using valid release-date FX and monthly CPI series.
   - Preserves original local nominal currency and source provenance on 100% of financial records.
4. **Target Integrity (Zero Imputed Targets)**: Target variables (`worldwide_gross`, `opening_weekend_gross`) must never be imputed. Films lacking reported revenue targets are excluded from training splits.
5. **Schema Conformance**: 100% of Silver and Gold Parquet records must pass Pandera declarative schema validation suites without a single fatal exception.

---

## 3. Machine Learning Scientific Benchmarks & Quality Gates

1. **Holdout Test Accuracy (SMAPE Gate)**:
   - The primary CatBoost Regressor must achieve a Symmetric Mean Absolute Percentage Error of $\text{SMAPE} \le 40.0\%$ on the holdout test split (films released 2023–2024).
2. **Complexity Justification Gate**:
   - The primary GBDT model must achieve at least a $20\%$ relative error reduction over the 5-Feature Ordinary Least Squares (OLS) baseline on the identical holdout test set.
3. **Temporal Leakage Audit**:
   - 100% pass rate on `tests/test_leakage.py`. Absolute zero presence of post-release signals (IMDb ratings, vote counts, lifetime grosses) in Stage 1, Stage 2, or Stage 3 feature matrices.
4. **Conformal Uncertainty Empirical Coverage**:
   - MAPIE 80% conformal prediction intervals must achieve an empirical coverage rate between $78.0\%$ and $83.0\%$ on unseen holdout test data.
5. **Commercial Success Classification Performance**:
   - Quadratic Weighted Kappa $\kappa_w \ge 0.65$ across the 7 commercial tiers (Blockbuster to Disaster).
   - Multi-class Brier Calibration Score $\text{BS} < 0.20$.
6. **Explainability Additivity (SHAP Axioms)**:
   - 100% of generated TreeSHAP local explanations must satisfy the local accuracy axiom:
     $$f(x) = \phi_0 + \sum_{i=1}^M \phi_i \quad (\text{tolerance } \pm 10^{-4})$$

---

## 4. Backend API Architecture & Performance SLAs

1. **Search & Catalog Query Latency**:
   - 95th percentile response time for `GET /api/v1/movies/search` must be $<60\text{ms}$ under 50 concurrent virtual users.
2. **ML Inference & Explanation Latency**:
   - 95th percentile response time for `GET /api/v1/movies/{id}/prediction` (including forward GBDT pass, conformal interval calculation, and TreeSHAP waterfall) must be $<250\text{ms}$.
3. **What-If Simulation SLA**:
   - 95th percentile round-trip latency for `POST /api/v1/simulate/what-if` must be $<80\text{ms}$.
4. **Error Handling & RFC-7807 Conformance**:
   - 100% of 4xx and 5xx responses must return structured JSON envelopes conforming to RFC-7807 problem details specifications.
5. **Rate Limiting Enforcement**:
   - `slowapi` must strictly throttle public IP requests exceeding 60 requests/minute with `HTTP 429`.

---

## 5. Frontend UI/UX, Aesthetics & Accessibility Standards

1. **Dark Cinematic Theme Adherence**:
   - Visual presentation strictly adheres to the approved palette (`#0A0A0F` base, `#111118` cards, `#E8B74A` cinema gold accents).
2. **Lighthouse Audit Performance**:
   - Google Lighthouse scores across production desktop builds:
     - Performance: $\ge 85 / 100$
     - Accessibility: $\ge 95 / 100$
     - Best Practices: $\ge 90 / 100$
     - SEO: $\ge 90 / 100$
3. **Accessibility Compliance (WCAG 2.1 AA)**:
   - Automated `axe-core` test suite passes with zero critical or serious accessibility violations.
   - All text elements satisfy the $4.5:1$ contrast ratio against dark backgrounds.
4. **Responsive Fluidity**:
   - Zero layout breakage or horizontal overflow verified across Mobile (375px), Tablet (768px), and Desktop (1440px).
5. **Animation Frame Rate**:
   - Framer Motion page transitions, prediction bar fills, and modal animations maintain a smooth 60fps refresh rate on standard devices.

---

## 6. End-to-End User Experience Acceptance Criteria

1. **Mode 1 (Movie Explorer Journey)**:
   - User searches any catalog title $\rightarrow$ receives instant debounced suggestions $\rightarrow$ selects film $\rightarrow$ analytical dossier loads in $<300\text{ms}$ showing poster, metadata, predicted revenue tiers, conformal interval bands, success probability distribution, and local SHAP waterfall.
2. **Mode 2 (Upcoming Releases Dashboard Journey)**:
   - Dashboard loads with all 14 curated sections populated from real model inference $\rightarrow$ user applies regional filter (e.g., Tollywood) $\rightarrow$ view re-renders instantly showing only Telugu releases with grosses formatted in INR Crores.
3. **What-If Simulation Workflow**:
   - User drags budget slider from ₹150 Cr to ₹250 Cr $\rightarrow$ prediction bar dynamically animates to the new expected gross $\rightarrow$ UI clearly presents disclaimer: *"Model-inferred statistical correlation, not guaranteed causal outcome."*
4. **Dual-Currency Formatting**:
   - Single-click toggle switches all revenue metrics platform-wide between INR Crores (`₹1,040 Cr`) and USD Millions (`$125M`).

---

## 7. Automated Discovery Engine Operational Standards

1. **Autonomous Execution**:
   - Discovery jobs execute on a scheduled 02:00 IST cron loop via APScheduler without requiring human command triggers.
2. **Entity Ingestion Parity**:
   - New upcoming titles announced on TMDB across Hindi, Telugu, Tamil, Malayalam, Kannada, and English appear on the dashboard within 24 hours of public announcement.
3. **Prediction Readiness Enforcement**:
   - Films with Data Completeness $<40\%$ are displayed with an *"Awaiting Baseline Metadata"* badge; zero speculative numbers are fabricated.
4. **Audit Immutability**:
   - Prediction revisions are permanently appended to `prediction_history` with trigger attribution; past predictions are never deleted.

---

## 8. Portfolio Presentation & Academic Defense Criteria

1. **Interview Feasibility**:
   - The developer can comfortably explain and defend all architectural decisions, temporal leakage prevention mechanisms, and mathematical metric justifications in an interview setting.
2. **Scientific Honesty**:
   - The platform never claims unrealistic precision (e.g., "99% accurate"). It transparently presents prediction intervals and discusses box-office volatility with professional humility.
3. **Zero Enterprise Bloat**:
   - The entire stack runs locally on a consumer laptop via Docker Compose and requires zero paid third-party subscriptions.

---

## 9. The Master One-Hundred-Item Verification Checklist

```markdown
### I. Project Identity & Planning Documentation (Items 1–10)
- [ ] 1. README.md complete with professional badges, architecture summary, and quickstart.
- [ ] 2. docs/01_PROJECT_VISION.md complete with problem statement, scope, and philosophy.
- [ ] 3. docs/02_REQUIREMENTS_SPECIFICATION.md complete with functional and non-functional requirements.
- [ ] 4. docs/03_PRODUCT_MODES_AND_USER_FLOWS.md complete with dual-mode workflows and wireframes.
- [ ] 5. docs/04_DATASET_RESEARCH.md complete with official links, TMDB/IMDb details, and licenses.
- [ ] 6. docs/05_DATA_ACQUISITION_GUIDE.md complete with step-by-step download instructions.
- [ ] 7. docs/06_UNIFIED_DATASET_DESIGN.md complete with canonical schema and conflict resolution.
- [ ] 8. docs/07_DATA_ENGINEERING_PIPELINE.md complete with all 16 pipeline steps.
- [ ] 9. docs/08_HISTORICAL_SNAPSHOT_STRATEGY.md complete with leakage prevention rules.
- [ ] 10. docs/09_FEATURE_ENGINEERING.md complete with 65+ feature definitions and formulas.

### II. Machine Learning Architecture & Research (Items 11–20)
- [ ] 11. docs/10_MACHINE_LEARNING_RESEARCH.md complete with algorithm comparisons and loss functions.
- [ ] 12. docs/11_MODEL_SELECTION_AND_EVALUATION.md complete with SMAPE, kappa, and walk-forward CV.
- [ ] 13. docs/12_NLP_SENTIMENT_ARCHITECTURE.md complete with Google MuRIL and multilingual design.
- [ ] 14. docs/13_UPCOMING_MOVIE_DISCOVERY.md complete with autonomous discovery algorithms.
- [ ] 15. docs/14_AUTOMATED_DATA_INGESTION.md complete with job tables, retry rules, and schedules.
- [ ] 16. docs/15_PREDICTION_LIFECYCLE.md complete with Stages 1–5 and Readiness Score (0–100).
- [ ] 17. docs/16_DATA_UPDATE_AND_RETRAINING_POLICY.md complete with drift thresholds.
- [ ] 18. docs/17_SYSTEM_ARCHITECTURE.md complete with modular monolith topology and structure.
- [ ] 19. docs/18_DATABASE_AND_ER_DIAGRAM.md complete with 19 DDL table definitions and queries.
- [ ] 20. docs/19_API_SPECIFICATION.md complete with OpenAPI 3.1 endpoints and JSON payloads.

### III. UI/UX, Operations & Roadmap Specifications (Items 21–30)
- [ ] 21. docs/20_UI_UX_DESIGN_GUIDE.md complete with dark cinematic design system and tokens.
- [ ] 22. docs/21_MLOPS_AND_TRAINING_WORKFLOW.md complete with MLflow, Optuna, and DVC design.
- [ ] 23. docs/22_SECURITY_AND_GOVERNANCE.md complete with RBAC, slowapi, and legal attribution.
- [ ] 24. docs/23_TESTING_AND_VALIDATION.md complete with pytest, pandera, and playwright suites.
- [ ] 25. docs/24_DEPLOYMENT_AND_INFRASTRUCTURE.md complete with Docker Compose and cloud tiers.
- [ ] 26. docs/25_RESOURCE_AND_FEASIBILITY_ANALYSIS.md complete with hardware and compute profiling.
- [ ] 27. docs/26_PHASE_WISE_ROADMAP.md complete with all 17 phase breakdowns and dependencies.
- [ ] 28. docs/27_RISKS_AND_MITIGATION.md complete with master risk register and contingencies.
- [ ] 29. docs/28_FINAL_TECHNICAL_DECISIONS.md complete with 15 Architecture Decision Records.
- [ ] 30. docs/29_ACCEPTANCE_CRITERIA.md complete with sign-off gates and 100-item checklist.

### IV. Visual Diagrams & Planning Trackers (Items 31–40)
- [ ] 31. diagrams/system_architecture.mmd parses cleanly as valid Mermaid flowchart.
- [ ] 32. diagrams/data_pipeline.mmd parses cleanly as valid 16-step Mermaid flowchart.
- [ ] 33. diagrams/automated_discovery.mmd parses cleanly as valid Mermaid flowchart.
- [ ] 34. diagrams/ml_training_pipeline.mmd parses cleanly as valid Mermaid flowchart.
- [ ] 35. diagrams/prediction_lifecycle.mmd parses cleanly as valid Mermaid stateDiagram-v2.
- [ ] 36. diagrams/database_erd.mmd parses cleanly as valid 19-entity Mermaid erDiagram.
- [ ] 37. diagrams/application_flow.mmd parses cleanly as valid dual-mode Mermaid flowchart.
- [ ] 38. planning/DATASET_TRACKER.md populated with all candidate sources and tracking status.
- [ ] 39. planning/DATA_SOURCE_COMPARISON.md populated with feature, license, and cost matrices.
- [ ] 40. planning/MODEL_COMPARISON_MATRIX.md populated with candidate GBDTs and baseline models.

### V. Feature Dictionaries, Snapshots & API Trackers (Items 41–50)
- [ ] 41. planning/FEATURE_DICTIONARY.md populated with all 65+ engineered features.
- [ ] 42. planning/HISTORICAL_SNAPSHOT_TRACKER.md populated with reconstruction status.
- [ ] 43. planning/API_ENDPOINT_TRACKER.md populated with all OpenAPI REST endpoints.
- [ ] 44. planning/PHASE_TRACKER.md populated with all 17 roadmap phases.
- [ ] 45. planning/OPEN_DECISIONS.md populated with 25+ architectural decisions and contexts.
- [ ] 46. planning/RESEARCH_REFERENCES.md populated with verified links and academic citations.
- [ ] 47. docs/00_INDEX.md complete with reading orders and document cross-reference matrix.
- [ ] 48. docs/QUICK_START_PLANNING.md complete with immediate developer onboarding instructions.
- [ ] 49. docs/INTERVIEW_PREP_LOCATION.md points to private off-repo interview guide.
- [ ] 50. Master .gitignore verified covering secrets, data lakes, model weights, and node_modules.

### VI. Data Engineering & Pipeline Verification (Items 51–60)
- [ ] 51. Raw API ingestion stores unmodified payloads in partitioned Bronze Parquet.
- [ ] 52. Provenance metadata (_source_id, _retrieval_timestamp) present on every raw row.
- [ ] 53. RapidFuzz entity resolution resolves TMDB and IMDb IDs with >= 95% accuracy.
- [ ] 54. Deduplication eliminates duplicate foreign/regional movie records.
- [ ] 55. Financial arbitration hierarchy consistently resolves conflicting reported numbers.
- [ ] 56. Multi-currency engine converts nominal collections to standardized USD and INR.
- [ ] 57. Inflation engine deflates nominal values to constant 2024 Real USD via monthly CPI.
- [ ] 58. KNN missing budget imputation executes with binary is_budget_imputed flags.
- [ ] 59. Target variables (worldwide gross, opening gross) strictly zero percent imputed.
- [ ] 60. Pandera schema validation executes across all Silver tables with zero fatal errors.

### VII. Machine Learning & Model Performance (Items 61–70)
- [ ] 61. All training, validation, and holdout splits strictly chronological (zero random splits).
- [ ] 62. Absolute absence of post-release signals in pre-release feature sets verified via tests.
- [ ] 63. Point-in-time talent star power strictly ignores films released after snapshot date.
- [ ] 64. CatBoost Regressor trained using native categorical target statistics.
- [ ] 65. Optuna hyperparameter optimization executes 100 trials exclusively on validation split.
- [ ] 66. Primary CatBoost model achieves Holdout Test SMAPE <= 40.0%.
- [ ] 67. Complexity justification gate met: model beats 5-feature OLS baseline by >= 20%.
- [ ] 68. Success classifier achieves Quadratic Weighted Kappa (κ_w) >= 0.65 on holdout set.
- [ ] 69. MAPIE 80% conformal prediction intervals achieve empirical coverage between 78% and 83%.
- [ ] 70. TreeSHAP feature attributions mathematically sum to raw model prediction.

### VIII. Natural Language Processing & Sentiment (Items 71–80)
- [ ] 71. Google MuRIL quantized to INT8 executes inference on CPU in < 1.5s per 100 comments.
- [ ] 72. Script detection routes native Indic scripts to IndicBERT/MuRIL and Latin to MuRIL.
- [ ] 73. Sentiment engine accurately scores Romanized Indic (Hinglish/Tanglish) commentary.
- [ ] 74. Pre-release commentary collected strictly prior to movie release date (zero leakage).
- [ ] 75. Comment sentiment aggregated into 5 continuous movie-level feature attributes.
- [ ] 76. Sentiment controversy index identifies highly polarized movie releases.
- [ ] 77. Aggregated sentiment observations stored and indexed in PostgreSQL table.
- [ ] 78. User-level PII (usernames, IP addresses) stripped prior to embedding computation.
- [ ] 79. Sentiment processing runs asynchronously in background (never blocks user HTTP reads).
- [ ] 80. Sentiment fallback assigns neutral baseline (0.0) when digital buzz is absent.

### IX. Backend API & Ingestion Architecture (Items 81–90)
- [ ] 81. FastAPI application loads CatBoost .cbm and TreeSHAP explainers at startup.
- [ ] 82. REST endpoints conform strictly to OpenAPI 3.1 specification contracts.
- [ ] 83. Search queries resolve in < 60ms (p95) using pg_trgm trigram indexing.
- [ ] 84. Prediction and SHAP waterfall responses resolve in < 250ms (p95).
- [ ] 85. What-If counterfactual simulation engine resolves in < 80ms on CPU.
- [ ] 86. RFC-7807 problem details returned for all 4xx and 5xx error responses.
- [ ] 87. Slowapi rate limiting actively enforces 60 req/min limits on public endpoints.
- [ ] 88. APScheduler background jobs execute autonomous movie discovery daily at 02:00 IST.
- [ ] 89. Prediction revisions logged to prediction_history with trigger attribution.
- [ ] 90. Database connection pooling configured cleanly via SQLAlchemy 2.0 and asyncpg.

### X. Frontend UI/UX, Deployment & Governance (Items 91–100)
- [ ] 91. React 18 TypeScript application renders dark cinematic theme (#0A0A0F).
- [ ] 92. Movie Explorer displays comprehensive dossier, intervals, probabilities, and SHAP waterfall.
- [ ] 93. Upcoming Releases dashboard renders all 14 curated analytical sections.
- [ ] 94. Single-click toggle switches currency between INR Crores and USD Millions.
- [ ] 95. Interactive What-If Simulator provides responsive parameter sliders and instant updates.
- [ ] 96. Prediction Readiness Score clearly communicates stage maturity (Stages 1 to 5).
- [ ] 97. Mandatory legal financial prediction disclaimers visible across all prediction views.
- [ ] 98. Mandatory TMDB and IMDb non-commercial attribution notices displayed in footer.
- [ ] 99. Docker Compose orchestrates database, backend, frontend, and MLflow locally for $0.00.
- [ ] 100. Private interview preparation guide verified stored outside Git repository.
```
