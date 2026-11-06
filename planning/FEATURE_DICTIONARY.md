# CineMetrics — Master Feature Dictionary & Feature Engineering Matrix

**Document ID:** PLN-04  
**Version:** 1.0  
**Status:** Operational Tracking Matrix  
**Last Updated:** 2026-11  
**Related Docs:** [Feature Engineering](../docs/09_FEATURE_ENGINEERING.md) | [Historical Snapshot Strategy](../docs/08_HISTORICAL_SNAPSHOT_STRATEGY.md)

---

## Complete 65-Feature Master Registry

| # | Feature Name | Category | Description | Mathematical Formula / Calculation | Primary Source | Type | Stage | Missing Value Treatment | Leakage Risk | Importance |
|---|---|---|---|---|---|:---:|:---:|---|:---:|:---:|
| 1 | `lead_actor_avg_gross_last5` | Talent Power | Mean inflation-adjusted worldwide gross of lead actor's last 5 films prior to snapshot. | $\frac{1}{k}\sum_{i=1}^k \text{Gross}_{\text{real}}(m_i), k \le 5$ | Unified DB | Float | Stage 1 | Impute market median; `is_lead_debut=1` | None | Very High |
| 2 | `lead_actor_median_gross_last5` | Talent Power | Median gross of last 5 films; robust against mega-blockbuster outliers. | $\text{median}(\text{Gross}_{\text{real}}(m_1..m_5))$ | Unified DB | Float | Stage 1 | Impute market median | None | High |
| 3 | `lead_actor_success_rate_last5` | Talent Power | Proportion of last 5 releases categorized as Hit or above. | $\frac{N_{\text{hits}}}{N_{\text{total}}}$ ($[0.0, 1.0]$) | Unified DB | Float | Stage 1 | 0.25 (market historical baseline) | None | High |
| 4 | `lead_actor_career_film_count` | Talent Power | Cumulative theatrical films released prior to snapshot. | $\sum \mathbb{I}(\text{film released})$ | IMDb / TMDB | Int | Stage 1 | 0 (Indicates debut) | None | Medium |
| 5 | `lead_actor_box_office_draw_trend` | Talent Power | Slope of linear regression over last 4 release grosses. | Linear regression slope $\beta$ | Unified DB | Float | Stage 1 | 0.0 (Neutral trajectory) | None | Medium |
| 6 | `supporting_cast_composite_power` | Talent Power | Weighted star power of actors billed 2, 3, and 4. | $0.5 \cdot S_2 + 0.3 \cdot S_3 + 0.2 \cdot S_4$ | Unified DB | Float | Stage 1 | 0.3 × market median | None | High |
| 7 | `ensemble_star_power_index` | Talent Power | Log-sum of star power across top 5 billed cast members. | $\ln(1 + \sum_{i=1}^5 S_i)$ | Unified DB | Float | Stage 1 | Compute on available cast | None | Very High |
| 8 | `lead_actor_genre_affinity` | Talent Power | Average gross of lead actor in target primary genre. | Mean gross in target genre | Unified DB | Float | Stage 1 | Fall back to `lead_actor_avg_gross_last5` | None | High |
| 9 | `lead_actor_is_blockbuster_proven`| Talent Power | 1 if lead actor has headlined film $>100\text{M}$ USD (or ₹300 Cr). | Binary flag | Unified DB | Binary | Stage 1 | 0 | None | High |
| 10 | `lead_actor_days_since_last_film` | Talent Power | Days elapsed since actor's previous theatrical release. | $T_{\text{snapshot}} - T_{\text{last\_release}}$ | Unified DB | Int | Stage 1 | 730 (2 years default) | None | Low |
| 11 | `cast_gender_diversity_index` | Talent Power | Ratio of female to male actors in top 6 billing slots. | $\frac{N_{\text{female}}}{N_{\text{male}}}$ | IMDb Credits | Float | Stage 1 | 0.33 (median) | None | Low |
| 12 | `lead_actor_recent_awards_count` | Talent Power | Major acting awards in preceding 3 years. | Count of awards | IMDb / TMDB | Int | Stage 1 | 0 | None | Low |
| 13 | `lead_actor_market_crossover_score`| Talent Power | Ratio of overseas collections to domestic collections. | $\frac{\text{Gross}_{\text{intl}}}{\text{Gross}_{\text{dom}}}$ | The Numbers / Sacnilk | Float | Stage 1 | 0.15 (standard domestic) | None | Medium |
| 14 | `cast_untested_pairing_flag` | Talent Power | 1 if lead actor and director have never collaborated. | Binary flag | Unified DB | Binary | Stage 1 | 1 | None | Low |
| 15 | `lead_actor_debut_flag` | Talent Power | 1 if `lead_actor_career_film_count` == 0; else 0. | Binary flag | Derived | Binary | Stage 1 | 0 | None | Medium |
| 16 | `director_avg_gross_last3` | Director Power | Mean inflation-adjusted gross of director's last 3 features. | $\frac{1}{k}\sum_{i=1}^k \text{Gross}_{\text{real}}(m_i), k \le 3$ | Unified DB | Float | Stage 1 | Impute market median; `is_director_debut=1` | None | Very High |
| 17 | `director_career_success_rate` | Director Power | Career hit ratio: proportion classified as Hit or above. | $\frac{N_{\text{hits}}}{N_{\text{total}}}$ | Unified DB | Float | Stage 1 | 0.30 (baseline) | None | High |
| 18 | `director_career_film_count` | Director Power | Number of prior directed feature films. | Cumulative count | IMDb / TMDB | Int | Stage 1 | 0 | None | Medium |
| 19 | `director_genre_specialization` | Director Power | Fraction of prior filmography in identical primary genre. | $\frac{N_{\text{genre}}}{N_{\text{total}}}$ | IMDb / TMDB | Float | Stage 1 | 0.0 | None | High |
| 20 | `director_has_all_time_record` | Director Power | 1 if director previously delivered industry-record grosser. | Binary flag | Trade Annals | Binary | Stage 1 | 0 | None | High |
| 21 | `director_budget_experience_tier` | Director Power | Max budget tier previously handled: `micro` to `mega`. | Categorical tier | Unified DB | String | Stage 1 | `micro` | None | High |
| 22 | `director_box_office_volatility` | Director Power | Standard deviation of director's past grosses. | $\sigma(\text{Grosses})$ | Unified DB | Float | Stage 1 | 0.0 | None | Medium |
| 23 | `director_screenwriter_overlap` | Director Power | 1 if director also credited as primary writer/creator. | Binary flag | IMDb Crew | Binary | Stage 1 | 0 | None | Low |
| 24 | `director_days_since_last_release`| Director Power | Inactivity gap in days. | $T_{\text{snapshot}} - T_{\text{last\_release}}$ | Unified DB | Int | Stage 1 | 1095 (3 years) | None | Low |
| 25 | `is_director_debut` | Director Power | 1 if first-time director; else 0. | Binary flag | Derived | Binary | Stage 1 | Derived | None | Medium |
| 26 | `production_budget_usd_real` | Core Attribute | Estimated budget in constant 2024 USD (CPI-adjusted). | $\text{Budget}_{\text{nom}} \times \text{Deflator}$ | The Numbers / Trade | Float | Stage 1 | KNN imputed from genre+talent; set flag | Low | Critical |
| 27 | `budget_to_talent_equity_ratio` | Core Attribute | Ratio of budget to lead actor star power. | $\frac{\text{Budget}}{\text{StarPower}}$ | Derived | Float | Stage 1 | Imputed from median | None | Very High |
| 28 | `budget_tier` | Core Attribute | Five categorical tiers: `micro` to `mega`. | Categorical binning | Derived | String | Stage 1 | Derived | None | High |
| 29 | `is_budget_imputed` | Core Attribute | 1 if budget was estimated via KNN model; else 0. | Binary flag | Derived | Binary | Stage 1 | 0 | None | Medium |
| 30 | `runtime_minutes` | Core Attribute | Duration of the film in minutes. | Positive integer | TMDB / IMDb | Int | Stage 1 | Genre-specific median | None | Medium |
| 31 | `primary_genre` | Core Attribute | Primary canonical genre. | Categorical | TMDB | String | Stage 1 | Mandatory | None | High |
| 32 | `genre_combination_encoded` | Core Attribute | Top 2 genres alphabetically sorted. | e.g. `Action_SciFi` | TMDB | String | Stage 1 | `Drama_Other` | None | High |
| 33 | `is_franchise` | Core Attribute | 1 if part of recognized intellectual property / franchise. | Binary flag | TMDB Collections | Binary | Stage 1 | 0 | None | Very High |
| 34 | `is_sequel` | Core Attribute | 1 if direct narrative sequel to prior release. | Binary flag | TMDB / Trade | Binary | Stage 1 | 0 | None | Very High |
| 35 | `sequel_number` | Core Attribute | Sequence index (1 = original, 2 = sequel, etc.). | Integer index | Derived | Int | Stage 1 | 1 | None | High |
| 36 | `prior_franchise_avg_gross` | Core Attribute | Average gross of previous entries in same franchise. | Historical mean | Unified DB | Float | Stage 1 | 0.0 (if not franchise) | None | Very High |
| 37 | `is_remake` | Core Attribute | 1 if official remake of an earlier film. | Binary flag | Trade Annals | Binary | Stage 1 | 0 | None | Medium |
| 38 | `original_film_success_tier` | Core Attribute | Success tier of original film if remake. | Categorical tier | Unified DB | String | Stage 1 | `None` | None | Medium |
| 39 | `production_company_tier` | Core Attribute | Studio tier: `Tier 1 Major`, `Tier 2 Mid`, `Tier 3 Indie`.| Categorical tier | TMDB Companies | String | Stage 1 | `Tier 3 Indie` | None | High |
| 40 | `is_pan_india_release` | Core Attribute | 1 if released simultaneously in $\ge 3$ Indian languages. | Binary flag | Trade Reports | Binary | Stage 2 | 0 | None | Very High |
| 41 | `release_month` | Calendar Strategy| Calendar month of theatrical release (1 to 12). | Integer | TMDB Release | Int | Stage 1 | Mandatory | None | High |
| 42 | `release_quarter` | Calendar Strategy| Quarter of release (1 to 4). | Integer | Derived | Int | Stage 1 | Derived | None | Medium |
| 43 | `release_season` | Calendar Strategy| Seasonality bucket: `Holiday/Festive`, `Summer`, etc. | Categorical bucket | Derived | String | Stage 1 | Derived | None | High |
| 44 | `is_major_holiday_release` | Calendar Strategy| 1 if within 3 days of major national/international holiday. | Calendar match | Holiday Table | Binary | Stage 1 | 0 | None | Very High |
| 45 | `is_cultural_festival_release` | Calendar Strategy| 1 if release coincides with Diwali, Eid, Christmas, Pongal. | Festival match | Cultural Calendar| Binary | Stage 1 | 0 | None | Very High |
| 46 | `days_to_nearest_holiday` | Calendar Strategy| Absolute integer distance in days to nearest public holiday.| Distance calculation | Calendar Series | Int | Stage 1 | Calculated | None | Medium |
| 47 | `competing_releases_same_week` | Calendar Strategy| Count of other wide releases scheduled on identical week. | Rolling count | Release Schedule | Int | Stage 2 | Recomputed daily; 0 default | Medium | High |
| 48 | `competing_clash_star_power` | Calendar Strategy| Sum of star power of all competing clash releases. | $\sum S_{\text{competitors}}$ | Release Schedule | Float | Stage 2 | 0.0 | Medium | Very High |
| 49 | `scheduled_screen_count_tier` | Calendar Strategy| Estimated screen scale: `Limited`, `Moderate`, `Wide`, `Ultra`.| Categorical tier | Trade / Budget | String | Stage 3 | Imputed from budget tier | Low | High |
| 50 | `has_imax_premium_screens` | Calendar Strategy| 1 if secured IMAX / Dolby Cinema release format. | Binary flag | Distributor Trade| Binary | Stage 3 | 0 | Low | High |
| 51 | `theatrical_window_announced` | Calendar Strategy| Exclusive theatrical window duration in days prior to OTT. | Days integer | Trade Reports | Int | Stage 3 | 45 (industry standard) | None | Medium |
| 52 | `day_of_week_release` | Calendar Strategy| Day of release (5 = Friday, 4 = Thursday preview, etc.). | Integer (1–7) | Release Date | Int | Stage 1 | 5 (Friday) | None | Medium |
| 53 | `trailer_lead_time_days` | Digital Buzz | Days between first teaser drop and theatrical release date.| $T_{\text{release}} - T_{\text{trailer}}$| YouTube API | Int | Stage 2 | 0 (No trailer yet) | Medium | Medium |
| 54 | `youtube_views_first_24h` | Digital Buzz | Log-transformed views on official teaser in first 24 hours. | $\ln(1 + \text{Views}_{24\text{h}})$ | YouTube API | Float | Stage 2 | 0.0 | High | Very High |
| 55 | `youtube_trailer_view_velocity` | Digital Buzz | Average daily views accrued between launch and snapshot. | $\frac{\text{Views}}{\text{Days}}$ | YouTube API | Float | Stage 3 | 0.0 | High | Very High |
| 56 | `youtube_trailer_like_ratio` | Digital Buzz | Engagement ratio: $\frac{\text{Likes}}{\text{Views}} \times 100$. | Percentage | YouTube API | Float | Stage 3 | 4.0% (median) | High | High |
| 57 | `google_trends_relative_score` | Digital Buzz | Normalized Google Trends search interest (0–100). | Trends relative score | Google Trends | Float | Stage 2 | 10.0 (baseline) | High | High |
| 58 | `google_trends_momentum_30d` | Digital Buzz | % change in search interest between 60d–30d and 30d–0d. | Growth slope % | Google Trends | Float | Stage 3 | 0.0 | High | High |
| 59 | `reddit_discussion_volume` | Digital Buzz | Mentions across tracked subreddits in preceding 30 days. | Post/comment count | Reddit API | Int | Stage 3 | 0 | Medium | Medium |
| 60 | `pre_release_sentiment_polarity`| Digital Buzz | Mean MuRIL sentiment polarity score (range $[-1.0, +1.0]$).| Compound score | NLP Pipeline | Float | Stage 3 | 0.0 (neutral) | Medium | High |
| 61 | `sentiment_positive_ratio` | Digital Buzz | Fraction of social mentions classified as strongly positive.| $[0.0, 1.0]$ | NLP Pipeline | Float | Stage 3 | 0.50 (median) | Medium | Medium |
| 62 | `advance_booking_day1_inr_crores`| Digital Buzz | Advance ticket sales revenue tracked 24h prior to debut. | Revenue in ₹ Cr | Trade Trackers | Float | Stage 4 | 0.0 | Critical | Extreme |
| 63 | `genre_market_share_trailing_year`| Macro Market | Box office share of target genre in preceding 12 months. | Trailing percentage | Unified DB | Float | Stage 1 | Computed from rolling DB | None | High |
| 64 | `market_segment` | Macro Market | Primary industry: `Bollywood`, `Tollywood`, `Hollywood`, etc. | Categorical | TMDB / Language | String | Stage 1 | Mandatory | None | Very High |
| 65 | `post_pandemic_recovery_index` | Macro Market | Step indicator: Pre-2020 (0), 2020–2022 (1), 2023+ (2). | Ordinal step | Release Date | Int | Stage 1 | Derived | None | High |
