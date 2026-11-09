# CineMetrics — Autonomous Movie Discovery & Radar Report

**Execution Timestamp:** `2026-11-09T06:32:56.886350+00:00`  
**Cycle Duration:** `30.51s`  
**Total Upcoming Titles in Live Radar:** `35` releases  

---

## 1. Discovery Cycle Execution Metrics

| Metric Name | Value | Description |
|---|:---:|---|
| **Raw Candidates Harvested** | `292` | Across TMDB upcoming (IN, US, GB), Discover 365, and Indian regional queries |
| **Unique TMDB Entities** | `230` | Deduplicated entity count |
| **New Titles Discovered** | `230` | Newly announced theatrical films not previously tracked |
| **Date Shifts Detected** | `0` | Existing tracked films whose release dates moved |
| **Enriched in Cycle** | `35` | Full credits, directors, cast, and YouTube trailer keys fetched |

---

## 2. Active Radar Portfolio by Industry

| Industry Territory | Active Tracked Films | Percentage Share |
|---|:---:|:---:|
| **Tollywood** | `8` | `22.9%` |
| **Bollywood** | `7` | `20.0%` |
| **Mollywood** | `6` | `17.1%` |
| **Kollywood** | `6` | `17.1%` |
| **Hollywood** | `3` | `8.6%` |
| **Sandalwood** | `3` | `8.6%` |
| **Marathi Cinema** | `1` | `2.9%` |
| **Global** | `1` | `2.9%` |

---

## 3. Prediction Lifecycle Stage Distribution

| Lifecycle Stage | Count | Trigger Condition |
|---|:---:|---|
| **Stage 1 (Pre-Trailer Announcement)** | `24` | Official YouTube trailer linked; buzz tracking active |
| **Stage 2 (Trailer Released)** | `10` | Official YouTube trailer linked; buzz tracking active |
| **Stage 0 (Early Discovery)** | `1` | Pre-trailer announcement; structural features only |

---

## 4. Top Anticipated Upcoming Releases (Chronological Live Radar)

| Movie Title | Industry | Release Date | Director | Lead Actor | Lifecycle Stage | YouTube Trailer Key |
|---|---|:---:|---|---|:---:|:---:|
| **Gondhal** | Marathi Cinema | `2025-11-14` | Santosh Davakhar | Kishore Kadam | `Stage 1 (Pre-Trailer Announcement)` | *Pending drop* |
| **Godzilla Minus Zero** | Global | `2026-11-03` | Takashi Yamazaki | Ryunosuke Kamiki | `Stage 2 (Trailer Released)` | [`pWJjYoqVSjQ`](https://youtu.be/pWJjYoqVSjQ) |
| **Ghost Soldier** | Hollywood | `2026-11-04` | William Eubank | Jim Caviezel | `Stage 2 (Trailer Released)` | [`UKaWzMf9Ybc`](https://youtu.be/UKaWzMf9Ybc) |
| **Donga Naa Koduku** | Tollywood | `2026-11-12` | Sreenu Kambala | Mouli | `Stage 1 (Pre-Trailer Announcement)` | *Pending drop* |
| **Bouma** | Mollywood | `2026-11-12` | Rejin S Babu | Dileesh Pothan | `Stage 1 (Pre-Trailer Announcement)` | *Pending drop* |
| **Bhogi** | Tollywood | `2026-11-12` | Sampath Nandi | Sharwanand | `Stage 1 (Pre-Trailer Announcement)` | *Pending drop* |
| **Black Gold** | Kollywood | `2026-11-13` | Dheeran Arunkumar | Vetri | `Stage 1 (Pre-Trailer Announcement)` | *Pending drop* |
| **Lambodhara 2.0** | Sandalwood | `2026-11-13` | Suni | Anil Shetty | `Stage 1 (Pre-Trailer Announcement)` | *Pending drop* |
| **Maya lady** | Tollywood | `2026-11-13` | Unknown | Rakesh Varre | `Stage 0 (Early Discovery)` | *Pending drop* |
| **Itllu Arjuna** | Tollywood | `2026-11-13` | Mahesh Uppala | Aniesh | `Stage 1 (Pre-Trailer Announcement)` | *Pending drop* |
| **John Doe** | Kollywood | `2026-11-13` | Madhumita | Arjun Das | `Stage 1 (Pre-Trailer Announcement)` | *Pending drop* |
| **Melcow Pondicherry** | Mollywood | `2026-11-13` | Nikhil Mohan | Arjun Ashokan | `Stage 1 (Pre-Trailer Announcement)` | *Pending drop* |

---

## 5. Architectural Conclusions & Downstream Trigger

1. **Zero Duplicate Inserts:** Deduplication on unique `tmdb_id` guarantees idempotent discovery execution.
2. **DoH Bypass Automation:** Google DNS-over-HTTPS natively integrated into discovery client, preventing ISP connection drops.
3. **Continuous Radar Feed:** Persisted `upcoming_discovery_catalog.parquet` continuously powers Mode 2 (Upcoming Releases Intelligence) and triggers Phase 12 prediction lifecycle updates.
