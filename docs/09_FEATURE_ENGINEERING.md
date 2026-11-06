# CineMetrics — Feature Engineering Strategy & Dictionary

**Document ID:** 09  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [Unified Dataset Design](06_UNIFIED_DATASET_DESIGN.md) | [Historical Snapshot Strategy](08_HISTORICAL_SNAPSHOT_STRATEGY.md) | [ML Research](10_MACHINE_LEARNING_RESEARCH.md) | [Model Selection](11_MODEL_SELECTION_AND_EVALUATION.md)

---

## Table of Contents

1. [Feature Engineering Principles](#1-feature-engineering-principles)
2. [Complete Feature Dictionary (65+ Engineered Features)](#2-complete-feature-dictionary-65-engineered-features)
   - 2.1 [Cast Power & Star Equity Features (15 Features)](#21-cast-power--star-equity-features-15-features)
   - 2.2 [Director Track Record & Pedigree Features (10 Features)](#22-director-track-record--pedigree-features-10-features)
   - 2.3 [Core Movie & Structural Attributes (15 Features)](#23-core-movie--structural-attributes-15-features)
   - 2.4 [Release Strategy & Calendar Scheduling (12 Features)](#24-release-strategy--calendar-scheduling-12-features)
   - 2.5 [Audience Anticipation & Digital Velocity (12 Features)](#25-audience-anticipation--digital-velocity-12-features)
   - 2.6 [Macro Market & Genre Dynamics (10 Features)](#26-macro-market--genre-dynamics-10-features)
3. [Algorithmic Feature Calculators (Python Pseudocode)](#3-algorithmic-feature-calculators-python-pseudocode)
4. [Feature Importance Priority & Expected SHAP Contribution](#4-feature-importance-priority--expected-shap-contribution)
5. [Feature Store Architecture: Offline Training vs. Online Inference](#5-feature-store-architecture-offline-training-vs-online-inference)

---

## 1. Feature Engineering Principles

Tabular machine learning models — specifically Gradient Boosted Decision Trees (GBDTs) like CatBoost, LightGBM, and XGBoost — derive their predictive power directly from the domain-informed quality of their input feature space.

CineMetrics engineers features according to four rigorous criteria:
1. **Temporal Isolation**: Feature values are mathematically computed using point-in-time window functions strictly prior to the prediction snapshot date.
2. **Nonlinear Interaction Capture**: Cross-features combine talent star power with production budget scale and distribution footprint (e.g., Star Power × Budget Ratio).
3. **Multi-Market Relevance**: Formulas apply seamlessly across both Hollywood studio models and Indian territory-based theatrical setups.
4. **Missingness Robustness**: Every engineered feature defines a mathematically grounded fallback or imputation policy accompanied by a missingness indicator token.

---

## 2. Complete Feature Dictionary (65+ Engineered Features)

### 2.1 Cast Power & Star Equity Features (15 Features)

| Feature Name | Type | Description & Mathematical Formula | Stage | Missing Value Policy | Leakage Risk | Expected Imp. |
|---|---|---|:---:|---|:---:|:---:|
| `lead_actor_avg_gross_last5` | Float | Mean inflation-adjusted worldwide gross of lead actor's last 5 theatrical releases strictly prior to snapshot: $\frac{1}{k}\sum_{i=1}^k \text{Gross}_{\text{real}}(m_i)$ ($k \le 5$). | Stage 1 | Impute industry/language median; set `is_lead_debut=1`. | None (Strict temporal filter) | Very High |
| `lead_actor_median_gross_last5` | Float | Median gross of last 5 films; robust against one-off outlier mega-blockbusters. | Stage 1 | Industry median. | None | High |
| `lead_actor_success_rate_last5` | Float | Proportion of last 5 releases categorized as "Hit", "Super Hit", or "Blockbuster": $\frac{N_{\text{hits}}}{N_{\text{total}}}$. Range $[0.0, 1.0]$. | Stage 1 | Default to 0.25 (industry historical baseline). | None | High |
| `lead_actor_career_film_count` | Int | Cumulative count of theatrical feature films released prior to snapshot. | Stage 1 | 0 (Indicates debut). | None | Medium |
| `lead_actor_box_office_draw_trend`| Float | Slope of linear regression fitted over last 4 release grosses: positive indicates ascending trajectory. | Stage 1 | 0.0 (Neutral trajectory). | None | Medium |
| `supporting_cast_composite_power` | Float | Weighted average of star power for billed actors 2, 3, and 4: $0.5 \cdot S_2 + 0.3 \cdot S_3 + 0.2 \cdot S_4$. | Stage 1 | Impute 0.3 × industry median. | None | High |
| `ensemble_star_power_index` | Float | Log-sum of star power across top 5 billed cast members: $\ln(1 + \sum_{i=1}^5 S_i)$. | Stage 1 | Compute on available cast. | None | Very High |
| `lead_actor_genre_affinity` | Float | Historical average gross of lead actor specifically within the target movie's primary genre. | Stage 1 | Fall back to `lead_actor_avg_gross_last5`. | None | High |
| `lead_actor_is_blockbuster_proven`| Binary | 1 if lead actor has headlined at least one film exceeding $100M USD (or ₹300 Cr INR) in career; else 0. | Stage 1 | 0. | None | High |
| `lead_actor_days_since_last_film` | Int | Days elapsed between previous theatrical release and current scheduled release. | Stage 1 | 730 (2 years default). | None | Low |
| `cast_gender_diversity_index` | Float | Ratio of female to male actors in top 6 billing positions. | Stage 1 | 0.33 (median). | None | Low |
| `lead_actor_recent_awards_count` | Int | Count of major acting awards (National Award, Oscar, Filmfare) in preceding 3 years. | Stage 1 | 0. | None | Low |
| `lead_actor_market_crossover_score`| Float | Ratio of overseas collections to domestic collections across actor's prior 3 films. | Stage 1 | 0.15 (standard domestic). | None | Medium |
| `cast_untested_pairing_flag` | Binary | 1 if lead actor and director have never previously collaborated; 0 if proven combo. | Stage 1 | 1. | None | Low |
| `lead_actor_debut_flag` | Binary | 1 if `lead_actor_career_film_count` == 0; else 0. | Stage 1 | Derived. | None | Medium |

### 2.2 Director Track Record & Pedigree Features (10 Features)

| Feature Name | Type | Description & Mathematical Formula | Stage | Missing Value Policy | Leakage Risk | Expected Imp. |
|---|---|---|:---:|---|:---:|:---:|
| `director_avg_gross_last3` | Float | Mean inflation-adjusted worldwide gross of director's last 3 released features. | Stage 1 | Market-segment median; set `is_director_debut=1`. | None | Very High |
| `director_career_success_rate` | Float | Career hit ratio: $\frac{N_{\text{commercial\_hits}}}{N_{\text{total\_films}}}$. | Stage 1 | 0.30 (baseline). | None | High |
| `director_career_film_count` | Int | Number of prior directed feature films. | Stage 1 | 0. | None | Medium |
| `director_genre_specialization` | Float | Fraction of director's prior filmography belonging to the same primary genre. | Stage 1 | 0.0. | None | High |
| `director_has_all_time_record` | Binary | 1 if director has previously delivered an industry-record all-time grosser. | Stage 1 | 0. | None | High |
| `director_budget_experience_tier` | Categorical| Max budget tier previously handled: `micro`, `mid`, `high`, `mega`. | Stage 1 | `micro`. | None | High |
| `director_box_office_volatility` | Float | Standard deviation of historical grosses: measures consistency vs. boom-or-bust. | Stage 1 | 0.0. | None | Medium |
| `director_screenwriter_overlap` | Binary | 1 if the director is also credited as primary screenwriter or story creator. | Stage 1 | 0. | None | Low |
| `director_days_since_last_release`| Int | Inactivity gap in days. | Stage 1 | 1095 (3 years default). | None | Low |
| `is_director_debut` | Binary | 1 if first-time director; 0 otherwise. | Stage 1 | Derived. | None | Medium |

### 2.3 Core Movie & Structural Attributes (15 Features)

| Feature Name | Type | Description & Mathematical Formula | Stage | Missing Value Policy | Leakage Risk | Expected Imp. |
|---|---|---|:---:|---|:---:|:---:|
| `production_budget_usd_real` | Float | Estimated production budget in constant 2024 USD (CPI-adjusted). | Stage 1 | KNN-imputed from genre + company; flag `is_budget_imputed=1`. | Low | Critical |
| `budget_to_talent_equity_ratio` | Float | $\frac{\text{Budget}}{\text{Lead Actor Star Power}}$: detects over-budgeted or under-star-powered productions. | Stage 1 | Imputed from median. | None | Very High |
| `budget_tier` | Categorical| Five tiers: `micro` (<$5M), `low` ($5M–$20M), `mid` ($20M–$75M), `high` ($75M–$150M), `mega` (>$150M). | Stage 1 | Derived. | None | High |
| `is_budget_imputed` | Binary | Indicator flag signaling whether budget was estimated via model. | Stage 1 | 0. | None | Medium |
| `runtime_minutes` | Int | Cleaned duration of the film in minutes. | Stage 1 | Genre-specific median runtime. | None | Medium |
| `primary_genre` | Categorical| Top canonical genre (Action, Drama, Comedy, Sci-Fi, Horror, Romance, Thriller, etc.). | Stage 1 | Mandatory; reject if missing. | None | High |
| `genre_combination_encoded` | String | Alphabetically sorted top 2 genres (e.g., `Action_SciFi`, `Comedy_Romance`). | Stage 1 | `Drama_Other`. | None | High |
| `is_franchise` | Binary | 1 if film belongs to an officially recognized cinematic franchise / intellectual property. | Stage 1 | 0. | None | Very High |
| `is_sequel` | Binary | 1 if film is an explicit narrative continuation of a prior release. | Stage 1 | 0. | None | Very High |
| `sequel_number` | Int | Sequence position (1 = original, 2 = sequel, 3 = trilogy capper, etc.). | Stage 1 | 1. | None | High |
| `prior_franchise_avg_gross` | Float | Average gross of previous entries in the same franchise. | Stage 1 | 0.0 if not franchise. | None | Very High |
| `is_remake` | Binary | 1 if film is an official remake of a prior language/regional film. | Stage 1 | 0. | None | Medium |
| `original_film_success_tier` | Categorical| Success level of original film if remake (`Hit`, `Blockbuster`, `Flop`, `None`). | Stage 1 | `None`. | None | Medium |
| `production_company_tier` | Categorical| `Tier 1 Major` (Disney, WB, YRF, Mythri), `Tier 2 Mid`, `Tier 3 Indie`. | Stage 1 | `Tier 3 Indie`. | None | High |
| `is_pan_india_release` | Binary | 1 if scheduled for wide simultaneous theatrical distribution in $\ge 3$ Indian languages. | Stage 2 | 0. | None | Very High |

### 2.4 Release Strategy & Calendar Scheduling (12 Features)

| Feature Name | Type | Description & Mathematical Formula | Stage | Missing Value Policy | Leakage Risk | Expected Imp. |
|---|---|---|:---:|---|:---:|:---:|
| `release_month` | Int | Calendar month of theatrical debut (1 to 12). | Stage 1 | Mandatory. | None | High |
| `release_quarter` | Int | Quarter of release (1 to 4). | Stage 1 | Derived. | None | Medium |
| `release_season` | Categorical| Seasonality bucket: `Holiday/Festive`, `Summer Blockbuster`, `Spring/Fall`, `Dump Month`. | Stage 1 | Derived. | None | High |
| `is_major_holiday_release` | Binary | 1 if release occurs within 3 days of major national/international holiday. | Stage 1 | Calculated from calendar. | None | Very High |
| `is_cultural_festival_release` | Binary | 1 if release coincides with Diwali, Eid, Christmas, Pongal/Sankranti, or Thanksgiving. | Stage 1 | Calculated from festival DB. | None | Very High |
| `days_to_nearest_holiday` | Int | Absolute integer distance in days to nearest public holiday. | Stage 1 | Calculated. | None | Medium |
| `competing_releases_same_week` | Int | Total count of other wide theatrical releases scheduled on the identical calendar week. | Stage 2 | Recomputed daily; 0 default. | Medium | High |
| `competing_clash_star_power` | Float | Sum of star power of all competing films sharing the release weekend: measures clash severity. | Stage 2 | 0.0. | Medium | Very High |
| `scheduled_screen_count_tier` | Categorical| Estimated screen scale: `Limited` (<500), `Moderate` (500–1500), `Wide` (1500–3500), `Ultra-Wide` (3500+). | Stage 3 | Imputed from budget tier. | Low | High |
| `has_imax_premium_screens` | Binary | 1 if secured premium large-format (IMAX, Dolby Cinema, 4DX) theatrical release. | Stage 3 | 0. | Low | High |
| `theatrical_window_announced` | Int | Promised exclusive theatrical window duration in days prior to OTT debut (e.g., 45, 60, 90). | Stage 3 | 45 (industry standard). | None | Medium |
| `day_of_week_release` | Int | Standard Friday release (5) vs. Thursday preview (4) or Festival Mid-week (2/3). | Stage 1 | 5 (Friday). | None | Medium |

### 2.5 Audience Anticipation & Digital Velocity (12 Features)

| Feature Name | Type | Description & Mathematical Formula | Stage | Missing Value Policy | Leakage Risk | Expected Imp. |
|---|---|---|:---:|---|:---:|:---:|
| `trailer_lead_time_days` | Int | Number of days between first official teaser drop and theatrical release date. | Stage 2 | 0 (No trailer yet). | Medium | Medium |
| `youtube_views_first_24h` | Float | Log-transformed views on official teaser/trailer in initial 24 hours: $\ln(1 + \text{Views})$. | Stage 2 | 0.0. | High | Very High |
| `youtube_trailer_view_velocity` | Float | Average daily views accrued between trailer launch and snapshot date: $\frac{\text{Views}}{\text{Days}}$. | Stage 3 | 0.0. | High | Very High |
| `youtube_trailer_like_ratio` | Float | Engagement ratio: $\frac{\text{Likes}}{\text{Views}} \times 100$. Typical range $2.0\% - 8.0\%$. | Stage 3 | 4.0 (median). | High | High |
| `google_trends_relative_score` | Float | Google Trends search interest normalized against 5-year cinema baseline (0 to 100). | Stage 2 | 10.0 (low baseline). | High | High |
| `google_trends_momentum_30d` | Float | Percentage change in search interest between 60d–30d window and 30d–0d window. | Stage 3 | 0.0. | High | High |
| `reddit_discussion_volume` | Int | Total post and comment mentions across tracked film subreddits in preceding 30 days. | Stage 3 | 0. | Medium | Medium |
| `pre_release_sentiment_polarity`| Float | Mean VADER/Transformer sentiment polarity score of online discussions: range $[-1.0, +1.0]$. | Stage 3 | 0.0 (neutral). | Medium | High |
| `sentiment_positive_ratio` | Float | Fraction of pre-release social mentions classified as strongly positive ($>+0.5$). | Stage 3 | 0.50 (median). | Medium | Medium |
| `advance_booking_day1_inr_crores`| Float | Advance ticket sales revenue tracked 24h prior to release (where legally observable). | Stage 4 | 0.0. | Critical | Extreme |
| `tmdb_popularity_at_snapshot` | Float | TMDB internal popularity metric captured strictly at point of snapshot. | Stage 2 | 5.0 (untracked). | High | Medium |
| `ormax_anticipation_score` | Float | Ormax Cinematix anticipation index (0–100) if observed via trade reports; else missing. | Stage 3 | Imputed / Flagged optional. | Medium | High |

### 2.6 Macro Market & Genre Dynamics (10 Features)

| Feature Name | Type | Description & Mathematical Formula | Stage | Missing Value Policy | Leakage Risk | Expected Imp. |
|---|---|---|:---:|---|:---:|:---:|
| `genre_market_share_trailing_year`| Float | Proportion of total annual theatrical box office grossed by target genre in preceding 12 months. | Stage 1 | Calculated from rolling DB. | None | High |
| `market_segment` | Categorical| Primary cinematic market: `Bollywood`, `Tollywood`, `Kollywood`, `Mollywood`, `Hollywood`, `Global`. | Stage 1 | Mandatory. | None | Very High |
| `annual_theatrical_admissions_trend`| Float | Macroeconomic cinema admissions year-over-year growth rate ($+/- \%$). | Stage 1 | 0.0. | None | Low |
| `cpi_inflation_deflator` | Float | Ratio of base year CPI to release year CPI: $\frac{\text{CPI}_{2024}}{\text{CPI}_{\text{year}}}$. | Stage 1 | 1.0. | None | Control |
| `average_ticket_price_real_usd`| Float | Historical average theatrical admission ticket price adjusted for inflation. | Stage 1 | Historical series average. | None | Low |
| `post_pandemic_recovery_index` | Float | Step indicator modeling box-office behavioral shifts before 2020 vs. 2020–2022 vs. 2023+. | Stage 1 | Derived from release date. | None | High |
| `exchange_rate_usd_to_inr` | Float | Historical conversion rate active at time of theatrical release. | Stage 1 | Looked up from FX table. | None | Control |
| `state_entertainment_tax_regime`| Categorical| Tax structure flag: Pre-GST state entertainment tax vs. Post-2017 GST uniform 18%/28% regime. | Stage 1 | Derived. | None | Control |
| `genre_fatigue_index` | Float | Number of same-genre releases in preceding 60 days: high values indicate audience saturation. | Stage 1 | 1. | None | Medium |
| `market_addressable_screens` | Int | Total operational commercial screens in primary territory for target language. | Stage 1 | Industry lookup table. | None | Medium |

---

## 3. Algorithmic Feature Calculators (Python Pseudocode)

```python
import numpy as np
import pandas as pd

def calculate_talent_star_power(
    person_id: str,
    snapshot_date: pd.Timestamp,
    historical_movies_df: pd.DataFrame,
    lookback_count: int = 5
) -> dict:
    """
    Computes point-in-time star power metrics strictly prior to snapshot_date.
    Ensures zero lookahead leakage into future film revenues.
    """
    # 1. Temporal filter: release date strictly before snapshot
    prior_films = historical_movies_df[
        (historical_movies_df["lead_actor_id"] == person_id) &
        (historical_movies_df["release_date"] < snapshot_date)
    ].sort_values("release_date", ascending=False).head(lookback_count)
    
    # 2. Check for debutant talent
    if len(prior_films) == 0:
        return {
            "actor_avg_gross_last5": np.nan, # Imputed downstream via market median
            "actor_success_rate_last5": 0.25,
            "actor_career_count": 0,
            "is_lead_debut": 1,
            "has_proven_blockbuster": 0
        }
    
    # 3. Compute real-term financial metrics
    grosses = prior_films["worldwide_gross_real_usd"].values
    success_flags = (prior_films["commercial_category"].isin(["Hit", "Super Hit", "Blockbuster"])).astype(int).values
    
    return {
        "actor_avg_gross_last5": float(np.mean(grosses)),
        "actor_median_gross_last5": float(np.median(grosses)),
        "actor_success_rate_last5": float(np.mean(success_flags)),
        "actor_career_count": len(historical_movies_df[
            (historical_movies_df["lead_actor_id"] == person_id) &
            (historical_movies_df["release_date"] < snapshot_date)
        ]),
        "is_lead_debut": 0,
        "has_proven_blockbuster": int(any(g >= 100_000_000 for g in grosses))
    }

def calculate_clash_competition(
    target_release_date: pd.Timestamp,
    target_movie_id: str,
    all_scheduled_movies_df: pd.DataFrame,
    window_days: int = 4
) -> dict:
    """
    Computes competitive clash density on the scheduled release weekend.
    """
    start_window = target_release_date - pd.Timedelta(days=window_days)
    end_window = target_release_date + pd.Timedelta(days=window_days)
    
    competitors = all_scheduled_movies_df[
        (all_scheduled_movies_df["release_date"] >= start_window) &
        (all_scheduled_movies_df["release_date"] <= end_window) &
        (all_scheduled_movies_df["movie_id"] != target_movie_id)
    ]
    
    clash_count = len(competitors)
    clash_star_sum = float(competitors["lead_actor_star_power"].sum()) if clash_count > 0 else 0.0
    
    return {
        "competing_releases_count": clash_count,
        "competing_clash_star_power": clash_star_sum,
        "is_solo_release": int(clash_count == 0)
    }
```

---

## 4. Feature Importance Priority & Expected SHAP Contribution

Based on empirical box-office literature and domain knowledge across Indian and Hollywood industries, the expected global SHAP importance hierarchy is partitioned as follows:

```
RANK  FEATURE DOMAIN                   EXPECTED GLOBAL SHAP CONTRIBUTION (%)
─────────────────────────────────────────────────────────────────────────────
1     Production Budget (Real USD)       [████████████████████]  26%
2     Lead Actor Historical Star Power   [████████████████]      20%
3     Franchise / Sequel Brand Scale     [████████████]          16%
4     Director Historical Track Record   [████████]              11%
5     Audience Digital Buzz (Trailer)    [██████]                 9%
6     Market Segment & Pan-India Footprint[████]                  6%
7     Release Calendar Proximity & Clash [███]                    5%
8     Genre & Seasonality Compatibility  [███]                    4%
9     Runtime & Structural Factors       [█]                      2%
10    Social Sentiment Polarity          [█]                      1%
─────────────────────────────────────────────────────────────────────────────
```

---

## 5. Feature Store Architecture: Offline Training vs. Online Inference

To guarantee complete consistency between offline model training and real-time backend inference without code duplication:

1. **Shared Feature Engineering Module (`ml/feature_engineering/`)**:
   - Both the batch offline training pipeline and the FastAPI backend `PredictionService` import the exact same calculation classes.
2. **Offline Store (Parquet)**:
   - Gold layer Parquet partitions storing historical pre-computed feature snapshots for all training, validation, and test splits.
3. **Online Store (PostgreSQL `feature_snapshots`)**:
   - The relational database indexes the latest JSONB feature payload for all tracked upcoming and catalog movies.
4. **On-The-Fly Simulation Engine**:
   - For What-If counterfactual scenarios, the frontend sends user-adjusted parameters; the online engine updates the base JSONB vector in memory and invokes model inference in $<50\text{ms}$.
