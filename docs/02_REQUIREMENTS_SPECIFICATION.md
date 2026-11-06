# CineMetrics — Software Requirements Specification

**Document ID:** 02  
**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-11  
**Related Docs:** [Project Vision](01_PROJECT_VISION.md) | [Product Modes & User Flows](03_PRODUCT_MODES_AND_USER_FLOWS.md) | [Acceptance Criteria](29_ACCEPTANCE_CRITERIA.md)

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Functional Requirements](#2-functional-requirements)
   - 2.1 [Movie Explorer Module](#21-movie-explorer-module)
   - 2.2 [Upcoming Releases Module](#22-upcoming-releases-module)
   - 2.3 [Automated Discovery Module](#23-automated-discovery-module)
   - 2.4 [Sentiment Analysis Module](#24-sentiment-analysis-module)
   - 2.5 [Explainability Module](#25-explainability-module)
   - 2.6 [What-If Simulation Module](#26-what-if-simulation-module)
   - 2.7 [Comparison Module](#27-comparison-module)
   - 2.8 [Financial Risk Module](#28-financial-risk-module)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Data Requirements](#4-data-requirements)
5. [ML Requirements](#5-ml-requirements)
6. [UI Requirements](#6-ui-requirements)
7. [Integration Requirements](#7-integration-requirements)
8. [Constraint Requirements](#8-constraint-requirements)
9. [Assumptions and Dependencies](#9-assumptions-and-dependencies)
10. [Requirement Traceability Matrix](#10-requirement-traceability-matrix)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the complete functional, non-functional, data, ML, UI, integration, and constraint requirements for the CineMetrics platform. It serves as the authoritative reference for what the system must do and how well it must do it. All implementation work must trace back to requirements defined here.

### 1.2 Document Conventions

- **Priority Levels:** Must (M) = Required for MVP; Should (S) = High value, planned for v1.0; Could (C) = Desirable, may be deferred
- **Requirement IDs:** `FR-NNN` = Functional Requirement; `NFR-NNN` = Non-Functional; `DR-NNN` = Data; `MLR-NNN` = ML; `UIR-NNN` = UI; `IR-NNN` = Integration; `CR-NNN` = Constraint
- **Acceptance Condition:** A verifiable statement that can be checked in a test or review

### 1.3 Scope Reference

This document covers CineMetrics v1.0 as described in [01_PROJECT_VISION.md](01_PROJECT_VISION.md). Features in the "Out of Scope" section of that document are not addressed here.

---

## 2. Functional Requirements

### 2.1 Movie Explorer Module

The Movie Explorer is Mode 1 of CineMetrics — a search-driven interface providing a complete intelligence dossier for any individual film.

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| FR-001 | The system shall provide a full-text search bar that accepts movie titles in English, Hindi (Devanagari), Telugu, Tamil, Malayalam, and Kannada scripts. | M | Search returns relevant results for queries in all six supported language scripts. |
| FR-002 | Search shall return results within 500ms for queries matching indexed titles. | M | 95th percentile search latency < 500ms under normal load. |
| FR-003 | Search results shall display movie poster thumbnail, title, year, language/industry, and a predicted success tier badge for upcoming films. | M | All five fields rendered on the search results card. |
| FR-004 | The system shall display an overview panel for each selected film containing: title, original language, release date, production budget (or "Not Disclosed"), genres, director, top 5 cast members, production company, and a plot synopsis. | M | All listed fields present in the overview panel; missing values displayed as "Not Available" rather than blank. |
| FR-005 | For released films, the system shall display actual box-office collection data: opening day, opening weekend, first week, lifetime India gross, worldwide gross. | M | Actual financial data displayed with source citation and collection date. |
| FR-006 | For released films with historical prediction data, the system shall display a "Retrospective Accuracy" panel showing what the system would have predicted at each pre-release stage vs. actual results. | S | Panel shows predictions at all stages for which training data was available, with percentage error for each. |
| FR-007 | For upcoming films, the system shall display the current prediction stage indicator (Announcement / Cast Lock / Trailer Drop / Release Week / Post Opening). | M | Stage indicator updates automatically as new data is collected. |
| FR-008 | The system shall display revenue predictions as a range (central estimate, 50th percentile interval, 80th percentile interval) rather than a single point estimate. | M | All three interval bounds displayed with explicit labels. |
| FR-009 | The system shall display a success classification prediction showing the probability distribution across all six tiers: Disaster, Below Average, Average, Hit, Super Hit, Blockbuster. | M | Probability distribution sums to 100%; all six tiers displayed. |
| FR-010 | The system shall display a SHAP explanation panel for each prediction, showing the top 10 most influential features and their directional contribution to the prediction. | M | SHAP values summing to prediction delta from base value; correct directional sign; feature names are human-readable. |
| FR-011 | The system shall display a sentiment summary panel aggregating trailer sentiment, critic sentiment, and social buzz score. | S | Panel includes separate scores for trailer, critics, and social; aggregated composite score; trend over time chart. |
| FR-012 | The system shall provide a What-If Simulation panel allowing users to modify key input features and immediately see the updated prediction. | S | Simulation responds within 1 second; all modifiable parameters listed in FR-013. |
| FR-013 | The What-If Simulation shall support modification of: production budget, release date, screen count, lead actor, genre, competing films in same week, and marketing spend indicator. | S | Each parameter has an input control; prediction updates on parameter change. |
| FR-014 | The system shall support adding any film to a Comparison list (maximum 4 films). | C | "Compare" button present on all film cards; comparison view accessible from navigation. |

### 2.2 Upcoming Releases Module

The Upcoming Releases Intelligence Dashboard is Mode 2 — a live, filterable overview of films in the pipeline.

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| FR-020 | The system shall display a dashboard with 14 distinct sections covering different temporal horizons and analytical angles for upcoming films. | M | All 14 sections rendered; each section loads independently. |
| FR-021 | Section 1 — "Releasing This Week": Films releasing in the current 7-day window, ordered by predicted opening weekend gross (descending). | M | Correct films in time window; correct ordering. |
| FR-022 | Section 2 — "Next 30 Days": Films releasing in 8–30 days from current date, with predictions and market. | M | Correct time window filter applied. |
| FR-023 | Section 3 — "High Confidence Predictions": Films for which sufficient data is available for the system to generate a Stage 3 (Trailer Drop) or higher prediction, ordered by prediction confidence score. | M | Only films with Stage 3+ predictions in this section. |
| FR-024 | Section 4 — "Blockbuster Candidates": Films where the predicted probability of Blockbuster or Super Hit tier exceeds 30%. | S | Probability threshold enforced; probability percentage displayed. |
| FR-025 | Section 5 — "Major Clash Alerts": Release weeks where two or more films with predicted gross > ₹50 Cr are releasing simultaneously. | S | Clash detection logic based on release date within same 7-day window. |
| FR-026 | Section 6 — "Pan-India Releases": Films releasing in 3 or more Indian languages simultaneously. | M | Language count filter applied; language badges displayed. |
| FR-027 | Section 7 — "Hollywood Arrivals": English-language international films releasing in India within 60 days. | M | Language and origin country filter applied. |
| FR-028 | Section 8 — "Franchise Entries": Films that are sequels, prequels, remakes, or part of an established franchise. | S | Franchise flag and lineage displayed. |
| FR-029 | Section 9 — "Festival Releases": Films releasing during major Indian festival windows (Diwali, Eid, Pongal, Onam, Christmas, Ugadi). | M | Festival window logic based on calendar; festival name badge displayed. |
| FR-030 | Section 10 — "Debut Vehicles": Films featuring a major debut (first film of an established star's child, major TV-to-film transition). | C | Debut flag manually curated or derived from filmography data. |
| FR-031 | Section 11 — "Award Season Contenders": Films positioning for major awards (National Awards, Filmfare, BAFTA, Oscars) based on festival run or critical acclaim signals. | C | Award positioning flag based on festival premiere data where available. |
| FR-032 | Section 12 — "Newly Discovered": Films added to the database by the automated discovery system in the past 7 days. | M | Discovery timestamp used; sorted by discovery date descending. |
| FR-033 | Section 13 — "Data Confidence Leaderboard": Films currently in the database sorted by data completeness score (percentage of expected features populated). | S | Completeness score computed and displayed per film. |
| FR-034 | Section 14 — "Market Summary": Aggregate statistics for the next 90 days — total films in pipeline, predicted total industry gross by market, number of clash weekends. | M | Aggregate statistics computed server-side; refreshed on dashboard load. |
| FR-035 | The dashboard shall provide a global filter panel allowing filtering by: market/language, genre, budget tier, release window, success tier prediction, and sort order. | M | Filters apply to all sections simultaneously; URL updates to reflect filter state (shareable links). |
| FR-036 | Each film card on the dashboard shall display: poster thumbnail, title, language/industry badge, release date, predicted gross range, success tier badge, data confidence indicator. | M | All seven elements rendered on each card. |
| FR-037 | The dashboard shall auto-refresh every 24 hours or when a user manually triggers refresh. | S | Refresh timestamp displayed; manual refresh button available. |

### 2.3 Automated Discovery Module

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| FR-040 | The system shall run a background discovery job that queries TMDB's "upcoming movies" and "now playing" endpoints on a scheduled basis (minimum daily). | M | Scheduler runs successfully; new films appear in database within 24 hours of TMDB listing. |
| FR-041 | The discovery pipeline shall deduplicate films across sources using a fuzzy title + year + language matching algorithm with a configurable confidence threshold. | M | Deduplication accuracy > 95% on a manually verified test set of 100 known duplicates. |
| FR-042 | For each newly discovered film, the system shall trigger an enrichment job that fetches additional metadata from TMDB (cast, crew, budget if available, genres, poster). | M | Enrichment completes within 1 hour of discovery; all TMDB-available fields populated. |
| FR-043 | The discovery pipeline shall flag films that meet criteria for prediction generation and queue them for initial prediction computation. | M | Films with sufficient data (at minimum: title, release date, genre, at least 1 cast member) are queued. |
| FR-044 | The system shall maintain an audit log of all discovery events: when each film was first seen, which source it came from, what enrichment was performed, and when each prediction was generated. | S | Audit log queryable via admin interface; each discovery event has timestamp and source. |
| FR-045 | The discovery system shall support manual override: an admin user can manually add, correct, merge, or exclude films from the database. | M | Admin interface allows all four operations; audit trail preserved. |

### 2.4 Sentiment Analysis Module

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| FR-050 | The system shall compute a sentiment score for each film's official trailer based on YouTube comment analysis. | S | Sentiment score in range [-1, +1]; computed within 48 hours of trailer being linked in the database. |
| FR-051 | The sentiment pipeline shall process comments in English, Hindi (romanised and Devanagari), Telugu, Tamil, and Malayalam. | S | Multilingual processing validated on a test set with known sentiment labels. |
| FR-052 | The system shall aggregate sentiment from multiple sources: YouTube trailer comments, critic review text (where available), and IMDb user reviews (for released films). | S | Each source contributes a separate sub-score; composite score is weighted average. |
| FR-053 | The sentiment trend shall be tracked over time — from announcement through release — and displayed as a time-series chart. | C | Time-series chart shows daily/weekly sentiment average with volume overlay. |
| FR-054 | Sentiment scores shall be incorporated as features in the revenue prediction model. | M | Sentiment feature included in feature set for Stage 3+ predictions; documented in feature engineering spec. |

### 2.5 Explainability Module

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| FR-060 | Every revenue prediction generated by the system shall be accompanied by a SHAP explanation object containing feature names, SHAP values, and base value. | M | Prediction API response includes shap_explanation field for every prediction. |
| FR-061 | The UI shall display a SHAP force plot or waterfall chart for each prediction, showing which features pushed the prediction above or below the base value. | M | Interactive SHAP chart rendered for every prediction on Movie Explorer page. |
| FR-062 | The UI shall provide natural-language narrative summaries of SHAP explanations (e.g., "The prediction is primarily driven by the film's franchise status and the director's previous box-office track record."). | S | Narrative generated from top-3 SHAP features using a template-based approach; not requiring LLM. |
| FR-063 | The system shall maintain and display global feature importance — a ranked list of which features are most influential across all predictions in a given market. | S | Global importance chart accessible from an "About the Model" page. |
| FR-064 | SHAP explanations shall respect temporal integrity — a prediction made at Stage 1 (Announcement) uses only Stage 1 features, and the explanation reflects only those features. | M | SHAP values computed only over features available at the prediction stage; stage indicator accompanies every explanation. |

### 2.6 What-If Simulation Module

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| FR-070 | The What-If panel shall allow users to change any numeric feature within defined valid ranges and receive an updated prediction. | S | Input validation enforces min/max per feature; prediction updates within 1 second. |
| FR-071 | The What-If panel shall show the prediction delta — the change in predicted gross and change in success tier probability — resulting from the user's changes. | S | Delta displayed as absolute change and percentage change from baseline prediction. |
| FR-072 | The system shall prevent What-If simulations from using features that would not be available at the film's current prediction stage. | M | Locked features display a "Not yet available at this stage" tooltip; they cannot be modified. |
| FR-073 | The What-If panel shall allow users to save and share a simulation scenario via a URL that encodes the modified parameters. | C | URL encodes all modified parameters; loading the URL restores the simulation state. |
| FR-074 | The What-If panel shall provide preset scenarios: "Release a week earlier", "Add a competing blockbuster", "Increase budget by 50%", "Change release to festival window". | C | At least 4 preset buttons with pre-configured parameter sets. |

### 2.7 Comparison Module

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| FR-080 | The system shall allow users to select up to 4 films for simultaneous side-by-side comparison. | C | Selection persists across page navigation; comparison view accessible from navigation. |
| FR-081 | The comparison view shall display, for each film: predicted gross range, success tier distribution, top 5 SHAP features, sentiment score, budget (if known), and release date. | C | All six data dimensions displayed in a comparable tabular/card layout. |
| FR-082 | The comparison view shall highlight the highest value in each comparable metric across the selected films. | C | Highest value in each row visually highlighted. |

### 2.8 Financial Risk Module

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| FR-090 | For films where production budget is known or estimated, the system shall compute a budget recovery probability — the probability that theatrical gross exceeds a minimum recovery threshold. | S | Recovery probability displayed as a percentage with the assumed threshold shown. |
| FR-091 | The system shall display a breakeven analysis: the minimum theatrical gross required for the production to cover its production + estimated marketing costs. | S | Breakeven computed using documented distributor share formula from [docs/16_FINANCIAL_METRICS_AND_CALCULATIONS.md](16_FINANCIAL_METRICS_AND_CALCULATIONS.md). |
| FR-092 | The system shall display the estimated distributor share (the studio/distributor's share of gross revenue after exhibitor split) using market-specific formulas. | M | Formula applied consistently per market; source formula documented and cited. |
| FR-093 | Financial risk labels shall be clearly marked as estimates with stated assumptions about budget and marketing spend. | M | Every financial risk figure includes a disclaimer note with the assumptions used. |

---

## 3. Non-Functional Requirements

### 3.1 Performance

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| NFR-001 | Search endpoint shall respond within 500ms at the 95th percentile under a load of 10 concurrent users. | M | Load test at 10 concurrent users; p95 latency measured with k6 or Locust. |
| NFR-002 | The revenue prediction endpoint shall respond within 2 seconds for a single film prediction (including SHAP computation) at the 95th percentile. | M | Single prediction API call, including SHAP, completes < 2s measured over 100 calls. |
| NFR-003 | The dashboard page (Mode 2) shall achieve an initial page load time (Largest Contentful Paint) < 3 seconds on a standard broadband connection. | M | Lighthouse LCP < 3s measured in development environment. |
| NFR-004 | Database queries for common operations (film lookup, feature retrieval for prediction) shall complete in < 100ms with proper indexing. | M | EXPLAIN ANALYZE shows query time < 100ms for common access patterns. |
| NFR-005 | The sentiment analysis pipeline shall process a 1,000-comment batch within 10 minutes on CPU (no GPU required). | S | Batch processing time measured on reference hardware (Intel Core i7, 16GB RAM). |

### 3.2 Availability and Reliability

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| NFR-010 | The system shall be operable in a fully local/offline mode once the database is seeded and models are trained. | M | All features function without external API connectivity (except real-time auto-discovery which gracefully degrades). |
| NFR-011 | The system shall handle API rate limit failures from TMDB gracefully, retrying with exponential backoff and logging the failure without crashing. | M | TMDB failure simulation test shows graceful degradation and retry behaviour. |
| NFR-012 | The discovery pipeline shall be resumable — if interrupted, it shall resume from the last successfully processed film without reprocessing already-enriched films. | S | Resume capability demonstrated by interrupting and restarting the pipeline mid-run. |

### 3.3 Scalability

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| NFR-020 | The PostgreSQL schema shall support at least 100,000 film records without degradation in query performance, assuming proper indexing. | S | EXPLAIN ANALYZE with 100K records shows acceptable query plans. |
| NFR-021 | The prediction API shall be stateless (no prediction computation on the server retains in-memory state between requests) to allow future horizontal scaling. | S | Prediction endpoint reviewed and confirmed stateless. |

### 3.4 Security

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| NFR-030 | API keys (TMDB, YouTube) shall be stored in environment variables and never committed to version control. | M | .env.example committed; .env in .gitignore; CI scan confirms no secrets in git history. |
| NFR-031 | The admin interface (for manual film corrections) shall require authentication before allowing write operations. | M | Unauthenticated requests to admin endpoints return 401. |
| NFR-032 | All API inputs shall be validated using Pydantic schemas with strict type checking; malformed inputs shall return 422 with descriptive error messages. | M | Fuzz testing with malformed inputs confirms 422 responses and no server crashes. |
| NFR-033 | SQL operations shall use parameterised queries via SQLAlchemy ORM to prevent SQL injection. | M | Code review confirms no raw string interpolation in SQL queries. |

### 3.5 Maintainability

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| NFR-040 | Python backend code shall achieve ≥ 80% test coverage as measured by pytest-cov. | M | Coverage report shows ≥ 80% across all modules excluding migration files. |
| NFR-041 | All public Python functions and classes shall have docstrings following Google-style docstring conventions. | S | Automated docstring check (pydocstyle) passes with < 10 warnings. |
| NFR-042 | The codebase shall pass Black (formatting), Ruff (linting), and mypy (type checking) with no errors on CI. | M | CI pipeline runs all three; build fails on any error. |
| NFR-043 | Database schema changes shall be managed through Alembic migrations; no manual schema changes permitted. | M | All schema changes have corresponding migration files; rollback tested. |
| NFR-044 | All ML experiments shall be tracked in MLflow with: parameters, metrics, model artifacts, and training dataset version. | S | MLflow UI shows complete experiment history; models loadable from registry. |

### 3.6 Accessibility

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| NFR-050 | The frontend application shall conform to WCAG 2.1 Level AA accessibility guidelines. | M | Automated axe-core scan shows zero critical/serious violations; manual keyboard navigation test passes. |
| NFR-051 | All interactive UI elements shall be keyboard-navigable with visible focus indicators. | M | Tab order logical; all actions completable without mouse. |
| NFR-052 | All images shall have descriptive alt text. | M | Automated accessibility scan confirms all images have non-empty alt attributes. |
| NFR-053 | Colour contrast ratios shall meet WCAG AA minimums (4.5:1 for normal text, 3:1 for large text) throughout the dark cinema theme. | M | Contrast ratio check passes for all text/background combinations in the design system. |
| NFR-054 | SHAP charts shall have accessible text alternatives (a data table with the same information). | S | Each SHAP chart has an adjacent accessible data table togglable by keyboard. |

---

## 4. Data Requirements

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| DR-001 | The training dataset shall contain a minimum of 2,000 Indian films with both production information (genre, cast, director, year) and financial outcomes (India gross or worldwide gross). | M | Dataset audit shows ≥ 2,000 Indian films with both fields populated. |
| DR-002 | The training dataset shall contain a minimum of 5,000 Hollywood films with financial data for model generalisation and volume. | M | Dataset audit shows ≥ 5,000 Hollywood films with gross revenue data. |
| DR-003 | Financial data shall be distinguished by collection basis: India Nett, India Gross, Worldwide Gross. All values shall be stored separately; no mixing of bases in a single financial field. | M | Database schema has separate columns for each financial basis; validation rules prevent mixing. |
| DR-004 | All historical financial figures shall be stored with the currency (INR or USD) and the reference exchange rate used for any normalisation. | M | Currency and exchange rate columns present in financial_data table; no implicit currency assumptions. |
| DR-005 | Production budget data shall be stored with a data_source field and a confidence_level (High / Estimated / Unknown). | M | Budget records include source and confidence; queries can filter by confidence level. |
| DR-006 | The dataset shall include release date at the day level (not just year) for temporal feature engineering (day of week, festival proximity, competitive landscape). | M | Release date stored as DATE type; day-level precision confirmed for ≥ 90% of records. |
| DR-007 | Cast and crew data shall include at minimum: lead actor (up to 3), director, music director (for Indian films), production company. | M | Cast/crew data present for ≥ 85% of post-2010 films in the dataset. |
| DR-008 | Upcoming film records shall be refreshed from TMDB at least once every 24 hours during active pipeline operation. | M | Last-refreshed timestamp shows ≤ 24h lag for all active upcoming film records. |
| DR-009 | Duplicate film records across data sources shall be resolved with a master record and cross-reference links to source-specific IDs (TMDB ID, IMDb ID, etc.). | M | Deduplication audit shows < 1% duplicate film entities in production database. |
| DR-010 | Indian box-office figures from sources like Sacnilk shall be stored with their original reporting basis and not silently normalised; normalisation shall be tracked. | M | original_value and original_basis columns in financial_data alongside normalised values. |

---

## 5. ML Requirements

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| MLR-001 | Revenue prediction models shall achieve a Symmetric Mean Absolute Percentage Error (SMAPE) < 40% on the held-out temporal test set. | M | Evaluation report shows SMAPE < 40% on test set with no data leakage. |
| MLR-002 | Success classification models shall achieve accuracy > 70% on the held-out temporal test set. | M | Evaluation report shows accuracy > 70%; confusion matrix shows no systematic misclassification. |
| MLR-003 | The train/test split shall be temporal — all films in the test set shall have release dates after all films in the training set, with no overlap. | M | Data pipeline produces temporally correct splits; documented split dates. |
| MLR-004 | Feature engineering shall enforce temporal integrity — no features shall be derived from information available only after the film's release date, for pre-release stage predictions. | M | Feature audit document lists each feature with its earliest availability stage; code review confirms enforcement. |
| MLR-005 | All revenue predictions shall include calibrated prediction intervals at the 50th and 80th percentile confidence levels. | M | Interval calibration test shows actual coverage within ±5 percentage points of claimed coverage. |
| MLR-006 | Prediction intervals shall be generated using quantile regression, conformal prediction, or ensemble variance — documented method must be justified. | M | Method documented in [docs/09_REVENUE_PREDICTION_REGRESSION.md](09_REVENUE_PREDICTION_REGRESSION.md); implementation traceable to documentation. |
| MLR-007 | SHAP (TreeSHAP) explanations shall be computed for every prediction. SHAP is non-negotiable and cannot be replaced with approximation methods. | M | Prediction response always includes shap_values; never null or empty. |
| MLR-008 | Model training pipelines shall be fully reproducible — given the same training data and hyperparameters, training produces the same results. | M | Random seeds set; deterministic training verified by running twice and comparing metrics. |
| MLR-009 | ML experiments shall be tracked with MLflow, logging: hyperparameters, training/validation metrics, model artifacts, feature list, training dataset version hash. | S | MLflow experiment contains all listed items for every model run. |
| MLR-010 | Models shall be re-trainable when new data is added without manual intervention (beyond approving a retraining trigger). | S | Retraining script documented and tested; produces an improved model on a dataset with synthetic additional data. |
| MLR-011 | The system shall support separate market-specific models (Bollywood, South Indian, Hollywood) to account for different revenue distribution characteristics. | S | Separate model artifacts per market; routing logic selects correct model per prediction. |
| MLR-012 | Model performance shall be monitored for drift — if SMAPE on recently released films exceeds 1.5× the baseline SMAPE, an alert shall be generated. | S | Drift monitoring job runs weekly; alert generated in MLflow or log on threshold breach. |

---

## 6. UI Requirements

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| UIR-001 | The application shall use a dark cinematic colour scheme with deep blacks/dark greys as background and gold/amber accent colours consistent with a premium cinema aesthetic. | M | Design system documented in [docs/20_UI_UX_DESIGN_SYSTEM.md](20_UI_UX_DESIGN_SYSTEM.md); implemented consistently across all pages. |
| UIR-002 | The application shall be fully responsive, functioning correctly on mobile (320px), tablet (768px), and desktop (1280px+) viewport widths. | M | Cross-device testing at all three breakpoints shows no layout breakage. |
| UIR-003 | Page transitions and UI interactions shall use smooth animations (Framer Motion) with no layout shift or jank on modern hardware. | S | Lighthouse CLS score < 0.1; animations run at 60fps on a mid-range device. |
| UIR-004 | Movie poster images shall be lazy-loaded with a cinematic blur-up placeholder effect. | S | Network throttle test shows blur-up placeholder before full image loads. |
| UIR-005 | The Upcoming Releases dashboard shall use a card-based layout with consistent card dimensions and smooth hover states. | M | Card dimensions consistent across all dashboard sections; hover state clearly visible. |
| UIR-006 | SHAP visualisations shall be interactive — hovering over a feature bar shall show a tooltip with the feature value, SHAP value, and a plain-language explanation. | S | Tooltip renders on hover with all three data points. |
| UIR-007 | Revenue prediction ranges shall be visualised as a gradient bar or range chart — not just text numbers. | S | Range visualisation rendered for all predictions; central estimate visually distinguished from interval bounds. |
| UIR-008 | Success tier badges shall use a consistent colour scheme throughout the application: Disaster = red, Below Average = orange, Average = yellow, Hit = green, Super Hit = teal, Blockbuster = gold/purple. | M | Badge colours consistent in all rendered locations. |
| UIR-009 | The application shall implement skeleton loading states for all data-heavy panels (predictions, SHAP, sentiment) so the page structure is visible during loading. | S | Skeleton loaders visible during simulated network delay (Chrome DevTools throttle). |
| UIR-010 | The application shall display meaningful empty states when no results are found (search, filters, sections with no matching films). | M | Empty state component with descriptive message renders when data is absent. |
| UIR-011 | The Lighthouse Performance score shall be ≥ 85, measured on the Movie Explorer page and the Upcoming Releases dashboard. | M | Lighthouse audit run on both pages; both score ≥ 85. |
| UIR-012 | Font rendering shall use system fonts or a single performance-optimised web font (Inter or similar) with font-display: swap. | S | No FOUT visible during load; font performance not a contributor to low Lighthouse score. |

---

## 7. Integration Requirements

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| IR-001 | The system shall integrate with the TMDB API v3 for movie discovery, metadata enrichment, poster images, and cast/crew data. | M | TMDB API client implemented with rate limit handling; data ingested successfully for a test set of 100 films. |
| IR-002 | The system shall use IMDb Non-Commercial Datasets (TSV files) as a supplementary source for ratings, alternate titles, and cast data. | M | IMDb TSV files parsed and loaded into staging tables; entity matching to TMDB records working. |
| IR-003 | The system shall optionally integrate with YouTube Data API v3 for trailer comment collection (sentiment analysis). | S | YouTube client respects daily quota (10,000 units); comment collection works for a test set of 10 trailers. |
| IR-004 | The system shall optionally use the pytrends library (Google Trends unofficial API) for search interest time-series data as a feature. | C | pytrends integration returns meaningful data for a test set of 10 Indian films. |
| IR-005 | TMDB API key shall be configurable via environment variable (TMDB_API_KEY); the application shall fail fast with a clear error message if the key is absent. | M | Application startup check confirms TMDB_API_KEY presence; descriptive error if missing. |
| IR-006 | All external API calls shall implement exponential backoff retry logic with configurable maximum retries (default: 3) and backoff base (default: 2 seconds). | M | Retry logic unit tested with mocked API failures; retries correctly implemented. |
| IR-007 | The system shall respect TMDB's rate limit of 50 requests per second by implementing a client-side rate limiter. | M | Rate limiter tested against TMDB API; no 429 responses received during normal operation. |
| IR-008 | IMDb dataset ingestion shall handle updates to IMDb's TSV file format gracefully — schema changes detected and flagged, not silently dropped. | S | Column name mismatch triggers an alert log entry and halts ingestion for manual review. |

---

## 8. Constraint Requirements

| ID | Requirement | Priority | Acceptance Condition |
|---|---|---|---|
| CR-001 | The system shall not use any paid AI/LLM API (OpenAI, Anthropic, Google Gemini API, etc.) for generating predictions, explanations, or any part of the core pipeline. | M | Dependency audit confirms no paid AI API credentials in codebase or pipeline. |
| CR-002 | The system shall not use any paid data subscriptions or databases as primary data sources. | M | Data sourcing audit confirms all primary sources are free-tier or open access. |
| CR-003 | All ML models shall be trainable on a machine with 16GB RAM and a modern CPU (no GPU requirement) within 4 hours for the full pipeline. | M | Full pipeline training timed on reference hardware; completes within 4 hours. |
| CR-004 | The total footprint of serialised ML models shall not exceed 500MB on disk. | M | Model storage measured; total < 500MB. |
| CR-005 | Web scraping, if used, shall be conducted in compliance with the target site's robots.txt and terms of service; scraping shall use polite rate limits and not overload servers. | M | robots.txt compliance documented per data source; scraping rate < 1 request/second for any single domain. |
| CR-006 | The system shall be operable without an active internet connection for all analysis of already-collected data (offline mode). | S | Offline mode test with network interface disabled; movie lookup and prediction work for seeded data. |
| CR-007 | The project shall not incur cloud infrastructure costs during development. All development services run via Docker Compose locally. | M | No cloud provider accounts required to run the full development stack. |

---

## 9. Assumptions and Dependencies

### 9.1 Assumptions

1. TMDB API will remain free and accessible with the current rate limits throughout the project lifecycle.
2. IMDb Non-Commercial Datasets will continue to be provided as TSV downloads for non-commercial academic use.
3. Indian box-office data for major releases is publicly available from sources like Sacnilk and Bollywood Hungama (subject to terms of service review).
4. Historical Indian box-office data dating back to 2000 can be assembled from Kaggle community datasets supplemented by web collection.
5. YouTube trailer comment data is accessible via the YouTube Data API v3 within the free quota for the development dataset.
6. The developer has access to a machine with at minimum 16GB RAM, 8+ CPU cores, and 100GB available disk space.
7. Production budgets for Indian films will be missing for a significant portion (estimated 60%+) of records; models must handle this via imputation or missing-data-aware algorithms.
8. Currency conversion for historical INR/USD will use annual average exchange rates from the Reserve Bank of India or similar public source.

### 9.2 External Dependencies

| Dependency | Purpose | Risk if Unavailable |
|---|---|---|
| TMDB API | Primary movie discovery and metadata | High — core pipeline depends on this |
| IMDb Non-Commercial TSV | Supplementary ratings and cast | Medium — can partially substitute from TMDB |
| YouTube Data API v3 | Trailer comment collection | Low — sentiment feature becomes unavailable |
| pytrends | Google Trends data | Low — optional feature |
| Hugging Face Hub | Pre-trained NLP model weights | Medium — models must be cached locally after first download |
| Kaggle datasets | Historical financial data | Medium — alternative manual collection possible |

---

## 10. Requirement Traceability Matrix

| Requirement ID | Category | Related Doc(s) | Phase |
|---|---|---|---|
| FR-001 to FR-014 | Movie Explorer | [03](03_PRODUCT_MODES_AND_USER_FLOWS.md), [18](18_BACKEND_API_DESIGN.md), [19](19_FRONTEND_ARCHITECTURE.md) | Phase 7, 8 |
| FR-020 to FR-037 | Upcoming Releases | [03](03_PRODUCT_MODES_AND_USER_FLOWS.md), [15](15_UPCOMING_RELEASES_INTELLIGENCE.md), [18](18_BACKEND_API_DESIGN.md) | Phase 7, 8 |
| FR-040 to FR-045 | Automated Discovery | [14](14_AUTOMATED_DISCOVERY_SYSTEM.md), [06](06_DATA_INGESTION_PIPELINE.md) | Phase 9 |
| FR-050 to FR-054 | Sentiment Analysis | [11](11_SENTIMENT_ANALYSIS_PIPELINE.md), [07](07_FEATURE_ENGINEERING.md) | Phase 5 |
| FR-060 to FR-064 | Explainability | [12](12_SHAP_EXPLAINABILITY.md), [08](08_ML_MODEL_ARCHITECTURE.md) | Phase 6 |
| FR-070 to FR-074 | What-If Simulation | [13](13_WHAT_IF_SIMULATION_ENGINE.md), [19](19_FRONTEND_ARCHITECTURE.md) | Phase 8 |
| FR-080 to FR-082 | Comparison | [19](19_FRONTEND_ARCHITECTURE.md), [20](20_UI_UX_DESIGN_SYSTEM.md) | Phase 8 |
| FR-090 to FR-093 | Financial Risk | [16](16_FINANCIAL_METRICS_AND_CALCULATIONS.md), [17](17_CURRENCY_AND_REGIONAL_NORMALISATION.md) | Phase 7 |
| NFR-001 to NFR-005 | Performance | [18](18_BACKEND_API_DESIGN.md), [25](25_DEPLOYMENT_ARCHITECTURE.md) | Phase 10 |
| NFR-010 to NFR-012 | Reliability | [25](25_DEPLOYMENT_ARCHITECTURE.md), [24](24_TESTING_STRATEGY.md) | Phase 10 |
| NFR-030 to NFR-033 | Security | [18](18_BACKEND_API_DESIGN.md), [25](25_DEPLOYMENT_ARCHITECTURE.md) | Phase 7 |
| NFR-040 to NFR-044 | Maintainability | [24](24_TESTING_STRATEGY.md), [23](23_MLOPS_AND_EXPERIMENT_TRACKING.md) | All phases |
| NFR-050 to NFR-054 | Accessibility | [20](20_UI_UX_DESIGN_SYSTEM.md), [29](29_ACCEPTANCE_CRITERIA.md) | Phase 8 |
| DR-001 to DR-010 | Data | [04](04_DATA_SOURCES_AND_COLLECTION_STRATEGY.md), [05](05_DATA_SCHEMA_AND_DATABASE_DESIGN.md), [21](21_DATA_QUALITY_AND_VALIDATION.md) | Phase 1, 2 |
| MLR-001 to MLR-012 | Machine Learning | [07](07_FEATURE_ENGINEERING.md) to [12](12_SHAP_EXPLAINABILITY.md), [22](22_MODEL_EVALUATION_FRAMEWORK.md), [23](23_MLOPS_AND_EXPERIMENT_TRACKING.md) | Phase 3, 4, 5, 6 |
| UIR-001 to UIR-012 | User Interface | [19](19_FRONTEND_ARCHITECTURE.md), [20](20_UI_UX_DESIGN_SYSTEM.md) | Phase 8 |
| IR-001 to IR-008 | Integration | [04](04_DATA_SOURCES_AND_COLLECTION_STRATEGY.md), [06](06_DATA_INGESTION_PIPELINE.md), [14](14_AUTOMATED_DISCOVERY_SYSTEM.md) | Phase 1, 9 |
| CR-001 to CR-007 | Constraints | [01](01_PROJECT_VISION.md), [28](28_FINAL_TECHNICAL_DECISIONS.md) | All phases |
