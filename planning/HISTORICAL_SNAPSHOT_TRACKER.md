# CineMetrics — Historical Feature Snapshot & Temporal Reconstruction Tracker

**Document ID:** PLN-05  
**Version:** 1.0  
**Status:** Operational Tracking Matrix  
**Last Updated:** 2026-11  
**Related Docs:** [Historical Snapshot Strategy](../docs/08_HISTORICAL_SNAPSHOT_STRATEGY.md) | [Prediction Lifecycle](../docs/15_PREDICTION_LIFECYCLE.md)

---

## 1. Feature Temporal Reconstructibility Audit

This audit classifies whether each feature category can be reliably reconstructed for past historical films (2000–2023) or must be harvested live going forward (2024+):

| Feature Domain | Specific Features | Historical Reconstructibility (Past Films) | Reconstruction Method / Provenance | Going-Forward Live Harvest (Upcoming Films) | Temporal Leakage Risk | Policy Enforcement |
|---|---|:---:|---|:---:|:---:|---|
| **Core Metadata** | `title`, `genres`, `runtime`, `language`, `production_companies` | **100% Reconstructible** | Inherent to physical creative work; immutable post-production. | Direct from TMDB/IMDb discovery payloads. | **None** | Approved for all historical training splits. |
| **Talent Lineup** | `lead_actor_id`, `director_id`, `supporting_cast_ids` | **100% Reconstructible** | Publicly contracted and announced during pre-production. | Direct from TMDB credits endpoints. | **None** | Approved for all historical training splits. |
| **Point-in-Time Talent History**| `lead_actor_avg_gross_last5`, `director_avg_gross_last3` | **100% Reconstructible** | Reconstructed via SQL window functions filtering strictly $T_{\text{release}} < T_{\text{target\_movie}}$. | Computed on-the-fly from historical database. | **High (if future unmasked)** | Strict date filtering verified via automated unit tests. |
| **Production Budgets** | `production_budget_usd_real`, `budget_tier` | **85% Reconstructible** | Trade filings, The Numbers archive, studio reports; KNN imputed where missing. | Early studio trade reporting & press announcements. | **Low** | Approved; missing records explicitly flagged with `is_budget_imputed=1`. |
| **Calendar & Scheduling** | `release_month`, `is_holiday_release`, `festival_release` | **100% Reconstructible** | Verified historical release dates matched to calendar holiday tables. | Scheduled upcoming release calendar. | **None** | Approved for all historical training splits. |
| **Competitive Clash** | `competing_releases_same_week`, `competing_clash_star_power`| **90% Reconstructible** | Reconstructed from historical database of films sharing release weekends. | Active scheduled upcoming release calendar. | **Medium** | Approved for Stage 2/3 models. |
| **Trailer Upload Dates** | `trailer_lead_time_days` | **80% Reconstructible** | YouTube Data API `snippet.publishedAt` timestamp of official teaser. | Live tracking of newly uploaded trailers. | **Medium** | Reconstructible only if official video remains online. |
| **Trailer View Velocity** | `youtube_views_first_24h`, `view_velocity` | **0% Historically Reconstructible** | YouTube does NOT provide retrospective 24h view snapshots for older videos. | Harvested daily via automated background jobs. | **Fatal (if current views used)** | **BANNED from historical training splits.** Used solely for live models. |
| **Google Search Trends** | `google_trends_relative_score`, `momentum_30d` | **Partial (~40%)** | Pytrends historical weekly index (sparse for older regional Indian titles). | Harvested live daily for tracked upcoming films. | **High** | Restricted to live Stage 2/3 inference; excluded from pre-2018 training. |
| **Social Sentiment** | `pre_release_sentiment_polarity`, `positive_ratio` | **0% Historically Reconstructible** | Pre-release Reddit/Twitter commentary from 2012 is unindexed or deleted. | Harvested live weekly for tracked upcoming films. | **Fatal (if post-reviews used)** | **BANNED from historical training splits.** Used solely for live models. |
| **Advance Ticket Sales** | `advance_booking_day1_inr_crores` | **Partial (~20%)** | Trade articles for major post-2019 blockbusters; unrecorded for older films. | Monitored 24h prior to debut via trade reports. | **Critical** | Restricted strictly to Stage 4 (Release Eve). |
| **Third-Party Ratings** | `imdb_final_rating`, `imdb_vote_count`, `tmdb_popularity` | **PERMANENTLY BANNED** | Current numbers reflect years of post-theatrical accumulation. | Untracked for pre-release inference. | **FATAL LEAKAGE** | **PERMANENTLY EXCLUDED FROM PRE-RELEASE FEATURE MATRICES.** |

---

## 2. Benchmark Indian Cinema Financial Verification Ledger

A curated sample of major Indian releases across industries tracked for gold-standard validation:

| Movie Title | Market Segment | Release Date | Reported Budget (INR Cr) | Verified Gross (INR Cr) | SACNILK Nett (INR Cr) | Trade Consensus Source | Financial Status |
|---|---|:---:|:---:|:---:|:---:|---|:---:|
| **Baahubali 2: The Conclusion** | Tollywood / Pan-India | 2017-04-28 | ₹250 Cr | ₹1,788 Cr | ₹1,030 Cr | Sacnilk / Trade Consensus | Verified Ground Truth |
| **Dangal** | Bollywood | 2016-12-23 | ₹70 Cr | ₹2,024 Cr | ₹387 Cr | Bollywood Hungama / China Filings | Verified Ground Truth |
| **RRR** | Tollywood / Pan-India | 2022-03-25 | ₹550 Cr | ₹1,230 Cr | ₹782 Cr | Sacnilk / DVV Entertainment | Verified Ground Truth |
| **K.G.F: Chapter 2** | Sandalwood / Pan-India| 2022-04-14 | ₹100 Cr | ₹1,215 Cr | ₹859 Cr | Sacnilk / Hombale Films | Verified Ground Truth |
| **Jawan** | Bollywood / Pan-India | 2023-09-07 | ₹300 Cr | ₹1,148 Cr | ₹640 Cr | Sacnilk / Red Chillies Ent | Verified Ground Truth |
| **Pathaan** | Bollywood | 2023-01-25 | ₹240 Cr | ₹1,050 Cr | ₹543 Cr | YRF Studio Filings / Sacnilk | Verified Ground Truth |
| **Kalki 2898 AD** | Tollywood / Pan-India | 2024-06-27 | ₹600 Cr | ₹1,042 Cr | ₹646 Cr | Sacnilk / Vyjayanthi Movies | Verified Ground Truth |
| **Leo** | Kollywood | 2023-10-19 | ₹250 Cr | ₹605 Cr | ₹342 Cr | Seven Screen Studio / Sacnilk | Verified Ground Truth |
| **Manjummel Boys** | Mollywood | 2024-02-22 | ₹20 Cr | ₹242 Cr | ₹138 Cr | Kerala Film Producers Assoc / Sacnilk | Verified Ground Truth |
| **Kantara** | Sandalwood | 2022-09-30 | ₹16 Cr | ₹407 Cr | ₹310 Cr | Hombale Films / Sacnilk | Verified Ground Truth |
| **Pushpa: The Rise** | Tollywood / Pan-India | 2021-12-17 | ₹170 Cr | ₹350 Cr | ₹268 Cr | Mythri Movie Makers / Sacnilk | Verified Ground Truth |
| **Vikram** | Kollywood | 2022-06-03 | ₹120 Cr | ₹414 Cr | ₹247 Cr | Raaj Kamal Films / Sacnilk | Verified Ground Truth |

---

## 3. Live Snapshot Accumulation Progress (2024+ Operation)

*This register updates dynamically as scheduled background jobs populate `feature_snapshots`.*

| Snapshot Date | Total Movies Tracked | Stage 1 Snapshots | Stage 2 Snapshots | Stage 3 Snapshots | Stage 4 Snapshots | Storage Size (JSONB) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| *Pending Phase 11* | - | - | - | - | - | - |
