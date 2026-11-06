# CineMetrics — Comprehensive Data Source Comparison Report

**Document ID:** PLN-02  
**Version:** 1.0  
**Status:** Operational Tracking Matrix  
**Last Updated:** 2026-11  
**Related Docs:** [Dataset Research](../docs/04_DATASET_RESEARCH.md) | [Data Engineering Pipeline](../docs/07_DATA_ENGINEERING_PIPELINE.md)

---

## 1. Multi-Source Attribute Comparison Matrix

| Source Authority | Primary Data Type | Geographic Coverage | Core Strengths & Key Features | Programmatic Access Method | Licensing & Usage Restrictions | Cost | Primary Limitations | Architectural Priority |
|---|---|---|---|---|---|:---:|---|:---:|
| **The Movie Database (TMDB)** | Rich Metadata & Discovery | Global (Strong US, European & Indian) | Upcoming movie discovery endpoints, external IDs mapping, poster CDN, popularity index, keywords, trailers. | Official REST API v3 / v4 (Token Auth) | Free non-commercial with mandatory attribution notice. | **$0.00** | Budget and revenue fields often 0 for mid-tier releases. | **Primary (Discovery & Metadata)** |
| **IMDb Non-Commercial Datasets** | Credits & Filmography | Global Comprehensive | Ground-truth talent IDs (`nconst`), complete filmography graphs, director/writer attributions, titles. | Direct HTTP Gzip downloads (`datasets.imdbws.com`) | Free non-commercial personal / research use only. | **$0.00** | Explicitly excludes financial data (zero box office or budgets). | **Primary (Talent & Credit Graph)** |
| **The Numbers (Nash Information)** | Box Office & Budgets | Primarily Hollywood & Global Major | Gold-standard production budget database, domestic & international grosses, opening weekends. | Downloadable tables / curated CSV reference sets | Public reference data; commercial redistribution restricted. | **$0.00 (Public sets)** | US-centric; limited coverage of regional South Indian cinema. | **Primary (Budget Baseline)** |
| **Box Office Mojo (IMDb/Amazon)** | Detailed Daily Box Office | Hollywood & Major International | Daily box office collections, weekend theater drops, distributor records. | Reference browsing; no public API; commercial via IMDbPro. | Scraping strictly restricted by Amazon ToS. | Commercial ($$$) | No public API; strictly reference-only to avoid ToS breach. | **Supplementary (Reference Only)** |
| **Sacnilk** | Indian Theatrical Collections | Bollywood, Tollywood, Kollywood, Mollywood | Day-wise collections, Gross vs. Nett breakdown, distributor share, advance bookings. | Reference web tracking; community consensus. | Factual reporting of commercial public figures (Fair use). | **$0.00** | Unofficial data; numbers occasionally contested by producers. | **Primary (Indian Box Office)** |
| **Bollywood Hungama** | Hindi Film Trade | Bollywood (Hindi Cinema) | Historical Bollywood box office rankings, producer announcements, territory breakdowns. | Web trade charts. | Factual commercial reference. | **$0.00** | Hindi belt focus only; limited South Indian regional data. | **Secondary (Bollywood Validation)** |
| **YouTube Data API v3** | Digital Video Engagement | Global & Indian Regional | Trailer view velocity, like counts, published timestamp, teaser momentum. | Official Google Cloud REST API (`youtube/v3`) | Free tier quota (10,000 units/day). | **$0.00** | Dislike counts hidden by YouTube; quota limits bulk polling. | **Primary (Trailer Buzz)** |
| **Google Trends (Pytrends)** | Public Search Interest | Global & State-Level India | Relative search interest momentum (0–100) over 30d/90d pre-release windows. | Unofficial Python client (`pytrends`) | Rate-limited non-commercial research use. | **$0.00** | Relative index rather than absolute volume; strict request throttling needed. | **Secondary (Search Momentum)** |
| **Reddit API** | Audience Discussion & Sentiment | English & Code-Mixed Communities | Pre-release reactions in r/movies, r/boxoffice, r/bollywood, r/tollywood. | Official Reddit OAuth API | Free tier with rate limits (post-2023 policy). | **$0.00** | Strict post-2023 rate limits restrict large bulk scraping. | **Supplementary (Sentiment)** |
| **Ormax Media (Cinematix)** | Audience Anticipation & Tracking | Indian Cinema Exclusive | Proprietary audience anticipation scores, day-1 conversion forecasts. | Commercial subscription reports. | Proprietary commercial service. | Commercial ($$$) | Extremely expensive; completely unfeasible for student budget. | **Optional (Excluded from MVP)** |

---

## 2. Recommended Minimum Viable Data Stack (Zero-Cost Blueprint)

To maintain student feasibility and legal compliance, CineMetrics constructs its data fabric from this four-pillar combination:
1. **Metadata & Live Discovery**: TMDB REST API (Free with attribution)
2. **Talent & Credit Graph**: IMDb Non-Commercial Gzip TSV Dumps (Free personal use)
3. **Hollywood Financials & Budgets**: The Numbers Public Reference Datasets + Kaggle Curated Sets (Free / Public Domain)
4. **Indian Cinema Financials**: Sacnilk / Indian Trade Consensus Reference Tables + Curated Kaggle Bollywood Sets (Factual reporting)
5. **Digital Buzz & Sentiment**: YouTube Data API (Free tier) + Google Trends (Pytrends) + Google MuRIL (Open-source HuggingFace)

**Total Monthly Data Cost: $0.00** (100% compliant with student development constraints).
