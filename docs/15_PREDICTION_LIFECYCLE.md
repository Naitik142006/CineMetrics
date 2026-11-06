# CineMetrics — Prediction Lifecycle, Stage Progression & Readiness Framework

**Document ID:** 15  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [Product Modes & User Flows](03_PRODUCT_MODES_AND_USER_FLOWS.md) | [Feature Engineering](09_FEATURE_ENGINEERING.md) | [Data Update Policy](16_DATA_UPDATE_AND_RETRAINING_POLICY.md) | [Prediction Lifecycle Diagram](../diagrams/prediction_lifecycle.mmd)

---

## Table of Contents

1. [The Dynamic Nature of Movie Predictions](#1-the-dynamic-nature-of-movie-predictions)
2. [The Five Formal Prediction Lifecycle Stages](#2-the-five-formal-prediction-lifecycle-stages)
   - 2.1 [Stage 1: Early Announcement (6+ Months Out)](#21-stage-1-early-announcement-6-months-out)
   - 2.2 [Stage 2: Pre-Production & Teaser Drop (3 Months Out)](#22-stage-2-pre-production--teaser-drop-3-months-out)
   - 2.3 [Stage 3: Pre-Release Marketing Blitz (1 Month Out)](#23-stage-3-pre-release-marketing-blitz-1-month-out)
   - 2.4 [Stage 4: Theatrical Release Eve & Day 0](#24-stage-4-theatrical-release-eve--day-0)
   - 2.5 [Stage 5: Post-Opening Weekend Reconciliation (Day +3)](#25-stage-5-post-opening-weekend-reconciliation-day-3)
3. [The Prediction Readiness Scoring Framework (0–100)](#3-the-prediction-readiness-scoring-framework-0100)
4. [Continuous Forecast Evolution & Delta Tracking](#4-continuous-forecast-evolution--delta-tracking)
5. [Database Architecture for Multi-Stage Predictions](#5-database-architecture-for-multi-stage-predictions)
6. [Frontend Visualization & Uncertainty Communication](#6-frontend-visualization--uncertainty-communication)

---

## 1. The Dynamic Nature of Movie Predictions

Predicting a movie’s commercial performance is not a static, one-time calculation. A film is a multi-year creative, financial, and marketing endeavor whose risk profile evolves continuously:
- Six months before release, only the director, lead cast, and rough production scale are announced.
- Three months out, the teaser drops and audience interest registers on digital platforms.
- One month out, the official trailer releases, music albums trend, and competitive clash dynamics solidify.
- On release eve, physical advance bookings reveal hard consumer willingness-to-pay.
- After opening weekend, real theatrical numbers replace speculative forecasts.

**CineMetrics Core Architectural Principle:**  
A single static prediction is obsolete almost immediately. CineMetrics models movie forecasting as a **living lifecycle**, capturing snapshots and revising forecasts at structured milestones while maintaining full versioned history of how and why predictions changed.

---

## 2. The Five Formal Prediction Lifecycle Stages

```
STAGE 1 (6m+ Out)    STAGE 2 (3m Out)     STAGE 3 (1m Out)     STAGE 4 (Day 0)      STAGE 5 (Day +3)
[Early Baseline] ──► [Preliminary]   ──► [Refined Pre-Rel]──► [Opening Day]   ──► [Lifetime Rec]
Wide Intervals       Initial Buzz         Trailer & Sentiment  Advance Booking      Actual Collections
SMAPE: ±48%          SMAPE: ±40%          SMAPE: ±32%          SMAPE: ±24%          SMAPE: ±16%
```

---

### 2.1 Stage 1: Early Announcement (6+ Months Out)
- **Temporal Horizon**: $T_{\text{snapshot}} \le T_{\text{release}} - 180 \text{ days}$.
- **Trigger**: Film announced with verified director, lead cast, primary genre, and scheduled calendar window.
- **Permitted Features**:
  - `lead_actor_avg_gross_last5`, `director_avg_gross_last3`, `supporting_cast_composite_power`
  - `primary_genre`, `genre_combination_encoded`, `production_company_tier`
  - `is_franchise`, `is_sequel`, `sequel_number`, `prior_franchise_avg_gross`
  - `production_budget_usd_real` (or imputed budget tier)
  - `release_month`, `release_quarter`, `release_season`, `is_major_holiday_release`
  - `market_segment`
- **Strictly Banned Features**: Trailer view counts, YouTube likes, Google Trends scores, advance booking, review sentiment.
- **Model Variant**: Stage 1 Structural Regressor (CatBoost trained on time-invariant core features).
- **Target Metric**: Estimated Lifetime Worldwide Theatrical Gross (Broad Conformal Interval).
- **Expected Accuracy / Uncertainty**: Low certainty ($\text{SMAPE} \approx 45\%–50\%$; 80% interval span: $\pm 60\%$).

---

### 2.2 Stage 2: Pre-Production & Teaser Drop (3 Months Out)
- **Temporal Horizon**: $T_{\text{release}} - 180 \text{ days} < T_{\text{snapshot}} \le T_{\text{release}} - 90 \text{ days}$.
- **Trigger**: First official teaser launch or passage into 90-day release window.
- **Additional Permitted Features**:
  - `trailer_lead_time_days`
  - `youtube_views_first_24h` (if teaser launched)
  - `google_trends_relative_score`
  - `competing_releases_same_week` (initial calendar density)
  - `is_pan_india_release` (confirmed regional dubbing languages)
- **Model Variant**: Stage 2 Comprehensive Regressor.
- **Expected Accuracy / Uncertainty**: Moderate improvement ($\text{SMAPE} \approx 38\%–42\%$; interval shrinks by $\sim 15\%$).

---

### 2.3 Stage 3: Pre-Release Marketing Blitz (1 Month Out)
- **Temporal Horizon**: $T_{\text{release}} - 90 \text{ days} < T_{\text{snapshot}} \le T_{\text{release}} - 7 \text{ days}$.
- **Trigger**: Official theatrical trailer launch and full promotional campaign initiation.
- **Additional Permitted Features**:
  - `youtube_trailer_view_velocity`, `youtube_trailer_like_ratio`
  - `google_trends_momentum_30d`
  - `reddit_discussion_volume`, `pre_release_sentiment_polarity`, `sentiment_positive_ratio`
  - `competing_clash_star_power` (locked competitive clash severity)
  - `scheduled_screen_count_tier`, `has_imax_premium_screens`
- **Model Variant**: Stage 3 Full Multi-Modal GBDT (combines structural + buzz + sentiment).
- **Expected Accuracy / Uncertainty**: Best pre-release forecast ($\text{SMAPE} \approx 30\%–34\%$; interval shrinks by $\sim 30\%$).

---

### 2.4 Stage 4: Theatrical Release Eve & Day 0
- **Temporal Horizon**: $T_{\text{release}} - 7 \text{ days} \le T_{\text{snapshot}} \le T_{\text{release}}$.
- **Trigger**: Opening of physical and digital theatrical advance ticket bookings (BookMyShow, Fandango).
- **Additional Permitted Features**:
  - `advance_booking_day1_inr_crores` (where observable)
  - Final confirmed screen count & show allocations
  - Final censor certificate rating (CBFC / MPAA)
- **Model Variant**: Stage 4 Opening-Day & Weekend Calibrated Predictor.
- **Output Focus**: High-precision Opening-Day Gross & Opening-Weekend Gross forecasts.
- **Expected Accuracy / Uncertainty**: High precision ($\text{SMAPE} \approx 22\%–26\%$).

---

### 2.5 Stage 5: Post-Opening Weekend Reconciliation (Day +3)
- **Temporal Horizon**: $T_{\text{release}} + 3 \text{ days}$ (Monday following opening weekend).
- **Trigger**: Official trade reporting of Friday-to-Sunday opening weekend collections.
- **Additional Permitted Features**:
  - `actual_opening_day_gross`
  - `actual_opening_weekend_gross`
  - `opening_weekend_occupancy_ratio`
  - `early_audience_multiplier_signal` (Sunday vs. Friday growth curve)
- **Model Variant**: Stage 5 Lifetime Collection Extrapolator (Power-law decay multiplier model).
- **Expected Accuracy / Uncertainty**: Highest accuracy ($\text{SMAPE} \le 16\%$). Final forecast locked against historical actuals.

---

## 3. The Prediction Readiness Scoring Framework (0–100)

CineMetrics refuses to publish deceptive forecasts when data is insufficient. A deterministic **Prediction Readiness Score (PRS)** evaluates feature completeness before generating any public forecast:

```
PRS SCORE BREAKDOWN (Total: 100 Points)
─────────────────────────────────────────────────────────────────────────────
CORE STRUCTURAL PREREQUISITES (60 Points - Mandatory Baseline)
• Lead Actor Identified & Star Power Computed ............... 20 Pts
• Primary Director Identified & Pedigree Computed ........... 15 Pts
• Verified Production Budget (or high-confidence tier) ..... 15 Pts
• Locked Release Date & Calendar Month ...................... 10 Pts

DIGITAL BUZZ & PROMOTIONAL SIGNALS (30 Points - Stage 2/3 Refinement)
• Official Trailer / Teaser Launched & Tracked .............. 10 Pts
• Digital Engagement Velocity (YouTube views/likes) ......... 10 Pts
• Competitive Clash Density Computed ........................ 10 Pts

AUDIENCE SENTIMENT & ADVANCE SIGNALS (10 Points - Stage 3/4 Precision)
• Multilingual Sentiment Polarity Evaluated .................  5 Pts
• Screen Count or Advance Booking Observable ................  5 Pts
─────────────────────────────────────────────────────────────────────────────
```

### Readiness Tiers & Governance Rules

| PRS Score | Status Badge | Public Display Action | Model Output Behavior |
|:---:|:---:|---|---|
| **0 – 39** | **Insufficient Data** | Forecast Hidden; Displays *"Awaiting Baseline Metadata"* | Prediction suppressed; zero numbers generated. |
| **40 – 59** | **Early Estimate** | Displayed with Wide Warning Badge (`High Uncertainty`) | Stage 1 model runs with maximum conformal bands ($\pm 65\%$). |
| **60 – 79** | **Preliminary Forecast** | Displayed with Stage 2 Badge (`Moderate Confidence`) | Standard interval display; trends active. |
| **80 – 89** | **Refined Pre-Release** | Displayed with Stage 3 Badge (`High Confidence`) | Full SHAP waterfall and risk breakdown unlocked. |
| **90 – 100** | **Final Pre-Release** | Displayed with Stage 4 Badge (`Production Grade`) | Tightest intervals; milestone day-by-day estimates active. |

---

## 4. Continuous Forecast Evolution & Delta Tracking

When the background ingestion engine detects new signals (e.g., a trailer drops, budget is revised, or a competitor shifts dates):
1. **Delta Calculation**:
   $$\Delta \text{Revenue} = \hat{y}_{\text{new}} - \hat{y}_{\text{previous}}, \quad \%\Delta = \frac{\Delta \text{Revenue}}{\hat{y}_{\text{previous}}} \times 100\%$$
2. **Materialization**: If $|\%\Delta| \ge 5.0\%$ or if the film transitions to a new lifecycle stage, a new immutable record is appended to `predictions` and logged in `prediction_history`.
3. **Change Attribution**: The system records the primary driving feature responsible for the revision (e.g., *"Forecast increased by +18% following strong trailer engagement (42M views in 24h)"*).

---

## 5. Database Architecture for Multi-Stage Predictions

```sql
-- Active Predictions Table (Stores latest active forecast per movie)
CREATE TABLE predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    model_version VARCHAR(100) NOT NULL, -- e.g., 'catboost_v1.2.0'
    prediction_stage VARCHAR(50) NOT NULL, -- 'stage_1_6m', etc.
    prediction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    readiness_score INTEGER NOT NULL CHECK (readiness_score BETWEEN 0 AND 100),
    
    -- Point forecasts
    predicted_worldwide_gross_usd NUMERIC(15, 2) NOT NULL,
    predicted_worldwide_gross_inr NUMERIC(15, 2) NOT NULL,
    predicted_opening_day_gross_usd NUMERIC(15, 2),
    predicted_opening_weekend_gross_usd NUMERIC(15, 2),
    
    -- Conformal Uncertainty Intervals (80% and 95%)
    pessimistic_gross_usd NUMERIC(15, 2) NOT NULL,
    expected_gross_usd NUMERIC(15, 2) NOT NULL,
    optimistic_gross_usd NUMERIC(15, 2) NOT NULL,
    conformal_coverage_guarantee FLOAT DEFAULT 0.80,
    
    -- Success Classification Probabilities
    predicted_success_category VARCHAR(50) NOT NULL, -- 'Blockbuster', 'Hit', etc.
    class_probabilities JSONB NOT NULL, -- {"Blockbuster": 0.62, "Super Hit": 0.22, ...}
    
    -- Explainability artifact
    shap_summary JSONB NOT NULL, -- Top positive and negative feature contributions
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prediction History Table (Audit log of all past predictions)
CREATE TABLE prediction_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movie_id UUID NOT NULL REFERENCES movies(movie_id) ON DELETE CASCADE,
    prediction_id UUID NOT NULL REFERENCES predictions(prediction_id),
    previous_predicted_gross_usd NUMERIC(15, 2),
    new_predicted_gross_usd NUMERIC(15, 2),
    delta_percentage FLOAT,
    trigger_event VARCHAR(100), -- 'trailer_drop', 'stage_advance', 'budget_revision'
    revision_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_predictions_active ON predictions(movie_id) WHERE is_active = TRUE;
CREATE INDEX idx_prediction_history_movie ON prediction_history(movie_id, revision_timestamp);
```

---

## 6. Frontend Visualization & Uncertainty Communication

In the UI/UX design:
1. **The Lifecycle Progression Stepper**: A clean visual milestone track displayed atop the movie dossier showing completed stages and the active stage.
2. **The Dynamic Interval Fan Chart**: A visual timeline showing how the uncertainty bounds (pessimistic to optimistic) narrow as the film approaches release day.
3. **The Delta Callout**: Explicit callout tags (e.g., `▲ +₹120 Cr (+14%) post-trailer`) providing instant visual context on forecast momentum.
