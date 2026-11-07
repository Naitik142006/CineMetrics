# CineMetrics — Trailer Intelligence & Multilingual NLP Sentiment Report

**Execution Phase:** Phase 9 (Multilingual NLP & Trailer Buzz Engine)  
**Cohort Size:** 8 Multi-Industry Benchmark Releases (Hollywood, Bollywood, Tollywood)  
**Data Source:** YouTube Data API v3 (`videos.list` & `commentThreads.list`)  

---

## 1. Quantitative Engagement & Scale Leaderboard

| Movie Title | Industry | Trailer Views | Log10 Views | Likes | Like/View % | Comments | Daily View Velocity |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Animal** | Bollywood | `83,399,475` | `7.92` | `1,372,921` | `1.65%` | `31,602` | `73,415 views/day` |
| **Jawan** | Bollywood | `78,621,876` | `7.90` | `1,716,045` | `2.18%` | `124,950` | `67,545 views/day` |
| **Oppenheimer** | Hollywood | `75,760,279` | `7.88` | `839,157` | `1.11%` | `33,482` | `59,234 views/day` |
| **Kalki 2898 AD** | Tollywood | `61,474,474` | `7.79` | `952,822` | `1.55%` | `52,021` | `69,857 views/day` |
| **Fighter** | Bollywood | `55,565,552` | `7.74` | `656,030` | `1.18%` | `56,194` | `54,105 views/day` |
| **Salaar: Part 1 - Ceasefire** | Tollywood | `54,698,680` | `7.74` | `1,463,735` | `2.68%` | `70,442` | `51,025 views/day` |
| **Deadpool & Wolverine** | Hollywood | `40,299,696` | `7.61` | `586,234` | `1.45%` | `23,860` | `43,380 views/day` |
| **Dune: Part Two** | Hollywood | `31,286,500` | `7.50` | `437,169` | `1.40%` | `19,313` | `24,366 views/day` |

---

## 2. Multilingual Sentiment & Audience Reception Breakdown

| Movie Title | Positive % | Negative % | Neutral % | Net Polarity (P - N) | Controversy Score | Dominant Lang |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Jawan** | `76.0%` | `4.0%` | `20.0%` | `+0.720` | `0.122` | `en` |
| **Fighter** | `68.0%` | `6.0%` | `26.0%` | `+0.620` | `0.163` | `en` |
| **Deadpool & Wolverine** | `70.0%` | `14.0%` | `16.0%` | `+0.560` | `0.392` | `en` |
| **Kalki 2898 AD** | `56.0%` | `6.0%` | `38.0%` | `+0.500` | `0.134` | `en` |
| **Animal** | `64.0%` | `14.0%` | `22.0%` | `+0.500` | `0.358` | `en` |
| **Salaar: Part 1 - Ceasefire** | `46.0%` | `4.0%` | `50.0%` | `+0.420` | `0.074` | `en` |
| **Oppenheimer** | `62.0%` | `22.0%` | `16.0%` | `+0.400` | `0.546` | `en` |
| **Dune: Part Two** | `60.0%` | `26.0%` | `14.0%` | `+0.340` | `0.624` | `en` |

---

## 3. Cinema Domain Keywords & Audience Sentiment Signals

| Movie Title | Top Positive Keywords Detected | Top Negative Keywords Detected |
|---|---|---|
| **Kalki 2898 AD** | `goosebumps, masterpiece` | `None detected` |
| **Jawan** | `blockbuster, goosebumps, mind blowing, mass` | `None detected` |
| **Oppenheimer** | `blockbuster, goosebumps, masterpiece, banger, chills` | `avoid` |
| **Dune: Part Two** | `goosebumps, masterpiece, chills, hype, phenomenal` | `waste` |
| **Fighter** | `blockbuster, goosebumps, peak cinema, fire, goat` | `None detected` |
| **Animal** | `blockbuster, goosebumps, mind blowing, mass, next level` | `None detected` |
| **Salaar: Part 1 - Ceasefire** | `goosebumps` | `None detected` |
| **Deadpool & Wolverine** | `chills, fire` | `disappointed` |

---

## 4. Master Digital Buzz & Anticipation Index (0–100)

| Rank | Movie Title | Industry | Volume Reach (50%) | Sentiment Polarity (35%) | Passion (15%) | Composite Buzz Score |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 1 | **Jawan** | Bollywood | `7.9` | `+0.72` | `2.18%` | `79.7 / 100` (⚡ **HIGH BUZZ**) |
| 2 | **Salaar: Part 1 - Ceasefire** | Tollywood | `7.7` | `+0.42` | `2.68%` | `74.8 / 100` (⚡ **HIGH BUZZ**) |
| 3 | **Animal** | Bollywood | `7.9` | `+0.50` | `1.65%` | `74.1 / 100` (⚡ **HIGH BUZZ**) |
| 4 | **Fighter** | Bollywood | `7.7` | `+0.62` | `1.18%` | `72.7 / 100` (⚡ **HIGH BUZZ**) |
| 5 | **Kalki 2898 AD** | Tollywood | `7.8` | `+0.50` | `1.55%` | `72.5 / 100` (⚡ **HIGH BUZZ**) |
| 6 | **Oppenheimer** | Hollywood | `7.9` | `+0.40` | `1.11%` | `70.0 / 100` (⚡ **HIGH BUZZ**) |
| 7 | **Deadpool & Wolverine** | Hollywood | `7.6` | `+0.56` | `1.45%` | `68.8 / 100` (⚡ **HIGH BUZZ**) |
| 8 | **Dune: Part Two** | Hollywood | `7.5` | `+0.34` | `1.40%` | `63.6 / 100` (MODERATE) |

---

## 5. Architectural Conclusions & Downstream ML Integration

1. **Dual Signal Synergy:** Scale metrics (views/velocity) prevent niche positive films from over-indexing, while multilingual sentiment flags high-risk reception (e.g. polarizing trailers with high controversy scores).
2. **Regional Dialect Support:** Domain-adapted cinema lexicon successfully decoded Hinglish terms (*'paisa vasool'*, *'banger'*, *'goosebumps'*, *'mass'*) and Devanagari commentary.
3. **Materialization:** Feature matrix persisted to `data/processed/trailer_buzz_features.parquet` for immediate ingestion by the Stage 2/3 prediction pipeline and FastAPI services.
