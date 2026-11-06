# CineMetrics — Product Modes and User Flows

**Document ID:** 03  
**Version:** 1.0  
**Status:** Approved Architectural Specification  
**Last Updated:** 2026-11  
**Related Docs:** [Project Vision](01_PROJECT_VISION.md) | [Requirements Specification](02_REQUIREMENTS_SPECIFICATION.md) | [System Architecture](17_SYSTEM_ARCHITECTURE.md) | [UI/UX Design Guide](20_UI_UX_DESIGN_GUIDE.md)

---

## Table of Contents

1. [Architectural Overview: Dual-Mode Synergy](#1-architectural-overview-dual-mode-synergy)
2. [Mode 1: Movie Explorer (User-Driven Analysis)](#2-mode-1-movie-explorer-user-driven-analysis)
   - 2.1 [User Journeys & Search Mechanics](#21-user-journeys--search-mechanics)
   - 2.2 [Released vs. Upcoming Workflows](#22-released-vs-upcoming-workflows)
   - 2.3 [Indian Regional Cinema Workflows](#23-indian-regional-cinema-workflows)
   - 2.4 [Wireframe & Layout Descriptions](#24-wireframe--layout-descriptions)
   - 2.5 [Edge Cases & Fallback Paths](#25-edge-cases--fallback-paths)
3. [Mode 2: Upcoming Releases Intelligence (Automated Discovery & Monitoring)](#3-mode-2-upcoming-releases-intelligence-automated-discovery--monitoring)
   - 3.1 [Autonomous Pipeline & Ingestion Trigger](#31-autonomous-pipeline--ingestion-trigger)
   - 3.2 [Dashboard Information Architecture & 14 Dedicated Sections](#32-dashboard-information-architecture--14-dedicated-sections)
   - 3.3 [Filter Engine & Ranking Algorithms](#33-filter-engine--ranking-algorithms)
   - 3.4 [Live Auto-Refresh & Notification Engine](#34-live-auto-refresh--notification-engine)
4. [Shared Infrastructure & Data Convergence](#4-shared-infrastructure--data-convergence)
5. [Step-by-Step Interaction Sequences](#5-step-by-step-interaction-sequences)
6. [What-If Simulator & Counterfactual Workflows](#6-what-if-simulator--counterfactual-workflows)
7. [Administrative & Editorial Governance Workflow](#7-administrative--editorial-governance-workflow)
8. [Responsive & Cross-Platform UX Considerations](#8-responsive--cross-platform-ux-considerations)

---

## 1. Architectural Overview: Dual-Mode Synergy

CineMetrics is engineered around two distinct yet deeply intertwined operating modes:
1. **Mode 1: Movie Explorer** (Active, investigative, user-driven deep dive)
2. **Mode 2: Upcoming Releases Intelligence** (Passive, autonomous, continuous radar and monitoring)

Both modes are backed by an identical data fabric, database schema, entity resolution pipeline, and machine learning inference engine. There are no divergent data stores or disjointed models. An analytical dossier accessed in Mode 1 utilizes the exact feature extraction logic and calibrated CatBoost/LightGBM regressors that calculate the autonomous daily rankings in Mode 2.

```
       ┌────────────────────────────────────────────────────────┐
       │                Shared PostgreSQL & Parquet             │
       │       Unified Movie Schema, Snapshots & ML Models      │
       └───────────────────────────┬────────────────────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│     MODE 1: MOVIE EXPLORER      │         │   MODE 2: UPCOMING INTELLIGENCE │
│ • Ad-hoc Search & Discovery     │         │ • Autonomous Background Monitor │
│ • Released vs Upcoming Dossier  │◄────────┤ • 14 Curated Dashboard Sections │
│ • SHAP Explainability Waterfall │  Click  │ • Continuous Forecast Revision  │
│ • Interactive What-If Simulator │  Card   │ • Industry & Regional Filters   │
└─────────────────────────────────┘         └─────────────────────────────────┘
```

---

## 2. Mode 1: Movie Explorer (User-Driven Analysis)

### 2.1 User Journeys & Search Mechanics

The user enters Movie Explorer to examine a specific title across world cinema or Indian regional industries.

```
[Search Bar / Omnibox]
  │
  ├─ User types query (e.g. "Kalki 2898 AD", "Jawan", "Dune: Part Two")
  ├─ Debounced API call (/api/v1/movies/search?q=...)
  ├─ Multi-attribute matcher queries:
  │    • Canonical Latin title
  │    • Original script / regional title (Devanagari, Telugu, Tamil, Malayalam, Kannada)
  │    • Transliterations and common alternate spellings
  │    • Release year disambiguation
  │
  ▼
[Search Results Dropdown]
  │ Matches rendered with poster thumbnail, release year, language badge, and status
  ▼
[Movie Selection] -> Triggers State Hydration & Prediction Assembly
```

### 2.2 Released vs. Upcoming Workflows

Movie Explorer intelligently adapts its analytical dossier based on the release status of the film:

#### A. Upcoming Movies Workflow
1. **Header & Core Identity**: Title, backdrop, poster, release date, countdown timer, genre chips, language/industry badge, production banners.
2. **Forecast Panel**:
   - Primary Metric: Expected Worldwide Theatrical Gross (USD and INR Crores).
   - Prediction Interval: 80% and 95% conformal prediction bands (Pessimistic, Expected, Optimistic).
   - Milestone Forecasts: Opening-day gross, opening-weekend gross, first-week domestic nett.
3. **Commercial Success Classification**:
   - Probabilistic distribution across 7 standardized financial tiers (Disaster, Flop, Below Average, Average, Hit, Super Hit, Blockbuster).
   - Calibration score and Brier reliability index.
4. **Data Readiness & Maturity Indicator**:
   - Prediction lifecycle stage (Stage 1 to Stage 4).
   - Data completeness meter (0–100%) showing feature presence vs. imputation status.
5. **Explainability Workspace**:
   - Local SHAP waterfall chart breaking down exact positive and negative drivers (e.g., star power +$42M, release holiday +$18M, clash penalty -$12M).
6. **Anticipation & Buzz Trackers**:
   - Trailer view velocity, like ratio, Google Trends relative search momentum, Reddit sentiment polarity.

#### B. Previously Released Movies Workflow
1. **Actual vs. Predicted Comparison**:
   - Displays historical model prediction snapshot taken prior to release alongside verified actual theatrical grosses.
   - Percentage prediction error (SMAPE, relative delta).
2. **Historical Performance Breakdown**:
   - Opening weekend actual vs. forecast.
   - Domestic territory breakdown (e.g., Hindi Belt, AP/Telangana, Tamil Nadu, Overseas).
   - Multiplier analysis (Lifetime Gross / Opening Weekend Gross) reflecting word-of-mouth momentum.
3. **Post-Mortem Attribution**:
   - Post-release SHAP attribution analyzing whether pre-release expectations diverged due to word-of-mouth or exogenous competition.

### 2.3 Indian Regional Cinema Workflows

CineMetrics treats Indian cinema with first-class architectural parity:
- **Territory-Aware Financial Metrics**: Supports reporting in Gross Box Office (GBOC) and Nett Box Office (NBOC) after Goods and Services Tax (GST) deductions.
- **Multi-Lingual Title Disambiguation**: Resolves regional titles across Bollywood (Hindi), Tollywood (Telugu), Kollywood (Tamil), Mollywood (Malayalam), and Sandalwood (Kannada).
- **Pan-India Release Factor**: Detects multi-lingual wide releases, dubbing scale, and cross-state theatrical penetration.
- **Distributor Share Estimates**: Models theatrical recovery against estimated theatrical rights valuation.

### 2.4 Wireframe & Layout Descriptions

```
+------------------------------------------------------------------------------------+
|  [Logo] CineMetrics    [Search Movie...]    Upcoming   Explorer   Market   Admin   |
+------------------------------------------------------------------------------------+
|                                                                                    |
|  +--------------------+  KALKI 2898 AD (2024)                    [Stage 3: 30-Day] |
|  |                    |  Dir: Nag Ashwin | Lead: Prabhas, Amitabh  Readiness: 92%  |
|  |                    |  Telugu / Hindi / Tamil / Pan-India                        |
|  |     POSTER ART     |------------------------------------------------------------|
|  |      (2:3 Ratio)   |  PREDICTED WORLDWIDE GROSS:                                |
|  |                    |  ₹ 1,040 Cr  [$125.0M USD]                                 |
|  |                    |  Pessimistic: ₹880 Cr | Expected: ₹1,040 Cr | Optimistic: ₹1,260 Cr|
|  +--------------------+------------------------------------------------------------|
|                          SUCCESS PROBABILITY:                                      |
|                          [■■■■■■■■■■■■■■■■■■□□□□] Blockbuster (68%) / Super Hit (24%)|
+------------------------------------------------------------------------------------+
|  [TAB: Revenue Details]  [TAB: SHAP Explainability]  [TAB: Audience Buzz] [TAB: What-If]
+------------------------------------------------------------------------------------+
|  SHAP FEATURE ATTRIBUTION (Waterfall):                                             |
|  Base Value (Global Mean): ₹ 140 Cr                                                |
|  + Lead Actor Historical Star Power (Prabhas)  ............ + ₹ 380 Cr  [████████]  |
|  + Franchise / Mythological Sci-Fi Genre Scale ............ + ₹ 210 Cr  [█████]     |
|  + Multi-Language Pan-India Footprint .................. + ₹ 190 Cr  [████]      |
|  + High Digital Engagement (YouTube Trailer Velocity) ..... + ₹  80 Cr  [██]        |
|  - High Production Budget Risk (>₹600 Cr) ................. - ₹  60 Cr  [██]        |
|  --------------------------------------------------------------------------------  |
|  = Final Expected Prediction .............................. = ₹ 1,040 Cr            |
+------------------------------------------------------------------------------------+
```

### 2.5 Edge Cases & Fallback Paths

1. **Zero Financial History / Debut Talent**:
   - If a director or lead actor has no prior theatrical credits, the system assigns market-segment median baseline values with an explicit "Debut Penalty Uncertainty Flag", expanding conformal intervals by 40%.
2. **Unannounced Budget**:
   - Falls back to genre-and-production-tier regression imputation. A visual banner warns: *"Budget estimated via industry heuristic ($25M–$35M); financial risk metrics are tentative."*
3. **Data Completeness < 40%**:
   - Predictive calculation is suppressed. The system displays a clear **"Awaiting Verification & Baseline Signals"** badge rather than fabricating speculative numbers.

---

## 3. Mode 2: Upcoming Releases Intelligence (Automated Discovery & Monitoring)

### 3.1 Autonomous Pipeline & Ingestion Trigger

Mode 2 operates completely decoupled from end-user search queries. The **Cinemetrics Data Intelligence Engine** runs scheduled workers (via APScheduler) to poll discovery endpoints, resolve newly registered films, construct feature vectors, and write updated forecasts directly to PostgreSQL.

```
[Nightly 02:00 IST Cron Worker]
       │
       ▼
[TMDB Upcoming & Regional Discover Endpoints]
       │
       ├─ Filters: India (hi, te, ta, ml, kn) + US/Global
       ├─ Discovers 30–80 Candidate Titles
       │
       ▼
[Entity Resolution & Deduplication Pipeline]
       │ Matches against canonical movies table via TMDB ID, IMDb tconst, Title+Year
       │
       ├─ Existing Film -> Check for delta (Release date shift, trailer drop, cast update)
       │                   If delta found -> Generate new Feature Snapshot -> Re-predict
       │
       └─ New Film      -> Ingest metadata -> Trigger Enrichment Worker -> Predict
```

### 3.2 Dashboard Information Architecture & 14 Dedicated Sections

The Upcoming Releases Dashboard organizes the tracking universe into 14 distinct data-driven sections:

| # | Section Name | Logic / Inclusion Filter | Key Visual Metric |
|---|--------------|--------------------------|-------------------|
| 1 | **Upcoming This Week** | Release date within current calendar week (Mon–Sun) | Opening day forecast & screen count |
| 2 | **Upcoming This Month** | Release date within current 30-day rolling window | Expected opening weekend gross |
| 3 | **Upcoming This Year** | Release date within current calendar year | Expected lifetime gross & stage badge |
| 4 | **Indian Cinema Releases** | Production country India or primary language in Hindi/South Indian | Gross in INR Crores + Nett breakdown |
| 5 | **Regional Industry Spotlight** | Filterable sub-views: Tollywood, Kollywood, Mollywood, Sandalwood | Regional star power index |
| 6 | **International & Hollywood** | Primary industry Hollywood / Global wide releases | Gross in USD Millions |
| 7 | **Newly Discovered Movies** | Ingested into database within the last 7 calendar days | Ingestion timestamp & initial stage |
| 8 | **Recently Updated Forecasts** | Forecast revised within last 48 hours due to incoming signals | Delta indicator (e.g. `+14% ▲` post-trailer) |
| 9 | **Highest Predicted Earners** | Top 10 upcoming films ranked by expected worldwide gross | Lifetime gross ranking leaderboard |
| 10 | **Most Anticipated Movies** | Top ranked by engagement velocity (YouTube + Trends + Reddit) | Anticipation Buzz Score (0–100) |
| 11 | **Potential Blockbusters** | Predicted category probability for "Blockbuster" > 50% | Profitability / ROI forecast multiplier |
| 12 | **High-Risk Releases** | High budget combined with wide prediction variance / low recovery | Break-even gap indicator |
| 13 | **Insufficient Information** | Discovered titles with Data Readiness Score < 40% | Missing features checklist (e.g. Needs Budget) |
| 14 | **Awaiting Verification** | Conflicting metadata or disputed release dates requiring admin review | Editorial review action prompt |

### 3.3 Filter Engine & Ranking Algorithms

The Mode 2 dashboard provides a real-time reactive filtering engine:
- **Temporal**: Release horizon slider (7 days, 30 days, 90 days, 180 days, 365 days).
- **Geographic & Industry**: All, Bollywood, Tollywood, Kollywood, Mollywood, Sandalwood, Hollywood, European Cinema.
- **Budgetary**: Micro (<$2M), Mid-Tier ($2M–$25M), Big-Budget ($25M–$100M), Mega-Spectacle (>$100M / ₹300Cr+).
- **Readiness Tier**: Stage 1 (6m+), Stage 2 (3m), Stage 3 (1m), Stage 4 (Release week).
- **Sorting**: Expected Gross, Buzz Momentum, Release Proximity, Risk Index.

### 3.4 Live Auto-Refresh & Notification Engine

- Front-end queries the server via optimized query hooks (TanStack Query) with stale-while-revalidate caching.
- If a film's prediction changes significantly (>10% shift due to trailer metrics or release date clash), a visual indicator badge (`UPDATED FORECAST`) highlights the card.

---

## 4. Shared Infrastructure & Data Convergence

Both Mode 1 and Mode 2 leverage the identical unified data stack:

```
[Mode 1: Movie Explorer Request]         [Mode 2: Scheduled Dashboard Query]
             │                                              │
             └──────────────────────┬───────────────────────┘
                                    │
                                    ▼
                     [FastAPI /api/v1/ Endpoint Layer]
                                    │
                                    ▼
               [PredictionService & FeatureEngineeringService]
                                    │
            ┌───────────────────────┴───────────────────────┐
            ▼                                               ▼
[PostgreSQL Database]                           [Serialized ML Models (.cbm)]
- movies (canonical records)                     - CatBoost Regressor (Global)
- feature_snapshots (temporal records)          - CatBoost Classifier (Success Tier)
- predictions & prediction_history               - TreeSHAP Explainer
- popularity_snapshots                          - MAPIE Conformal Intervals
```

---

## 5. Step-by-Step Interaction Sequences

### 5.1 End-to-End User Flow: Discovery to Deep Exploration

```sequence
User->>UpcomingDashboard: 1. Opens Mode 2 Dashboard
UpcomingDashboard->>API: 2. GET /api/v1/upcoming/dashboard
API->>Database: 3. Query sorted upcoming titles & predictions
Database-->>API: 4. Return cached predictions & metadata
API-->>UpcomingDashboard: 5. Render 14 curated sections
User->>UpcomingDashboard: 6. Clicks movie card "War 2"
UpcomingDashboard->>MovieExplorer: 7. Navigate to /movies/{id} (Mode 1)
MovieExplorer->>API: 8. GET /api/v1/movies/{id}/prediction
API->>Predictor: 9. Retrieve active prediction & SHAP attribution
Predictor-->>MovieExplorer: 10. Hydrate full analytical dossier
User->>MovieExplorer: 11. Explores SHAP Waterfall & launches What-If Simulator
```

---

## 6. What-If Simulator & Counterfactual Workflows

The What-If Simulator enables interactive sensitivity analysis without corrupting canonical database records:

1. **Parameter Alterations**:
   - Budget slider (e.g., increase production spend from ₹150 Cr to ₹250 Cr).
   - Release Date picker (e.g., shift from a crowded clash weekend to solo Diwali festival window).
   - Cast / Director replacement (e.g., test revenue impact of substituting director or co-star).
   - Promotion intensity adjustment (simulating 2x YouTube trailer engagement).
2. **Execution**:
   - Frontend dispatches payload to `POST /api/v1/simulate/what-if`.
   - Backend constructs an in-memory synthetic feature snapshot.
   - The frozen production CatBoost model computes instant counterfactual inference (<80ms).
3. **Guardrails & Disclaimers**:
   - UI explicitly displays: *"Simulation shows model-inferred statistical correlation, not guaranteed causal outcome."*
   - Simulated forecasts are never persisted to the canonical prediction history table.

---

## 7. Administrative & Editorial Governance Workflow

To ensure data integrity when dealing with unstandardized Indian trade figures or disputed release dates:

1. **Flagged Records Queue**: Movies with conflicting box-office numbers or mismatched release dates are routed to `/admin/verification`.
2. **Provenance Audit**: Admins can inspect the data source provenance log (e.g., Sacnilk vs. Bollywood Hungama vs. TMDB).
3. **Manual Override**: Authorized admins can manually update release dates, lock verified budgets, or mark anomalous data points.
4. **Audit Trail**: Every edit is recorded in `movie_history` with an editor ID, timestamp, and justification reason.

---

## 8. Responsive & Cross-Platform UX Considerations

- **Desktop (1440px+)**: Multi-column comprehensive command dashboard, side-by-side SHAP waterfall and financial indicators.
- **Laptop / Tablet (768px–1024px)**: Collapsible sidebar, stacked analytical panels with sticky scenario toggles.
- **Mobile (375px–430px)**: Focused single-column view, horizontal swipeable cards for upcoming releases, simplified SHAP summary cards (Top 3 Positive / Top 3 Negative factors). Touch-optimized sliders for What-If scenarios.
