# CineMetrics — Master Open Decisions & Architectural Trade-Off Log

**Document ID:** PLN-08  
**Version:** 1.0  
**Status:** Operational Tracking Matrix  
**Last Updated:** 2026-11  
**Related Docs:** [Final Technical Decisions](../docs/28_FINAL_TECHNICAL_DECISIONS.md) | [Requirements Specification](../docs/02_REQUIREMENTS_SPECIFICATION.md)

---

## 1. Governance & Decision Lifecycle

Every non-trivial technical fork in CineMetrics is logged, contextualized, and resolved through this document. Decisions transition across four formal states: `Proposed` $\rightarrow$ `Under Review` $\rightarrow$ `Decided` $\rightarrow$ `Deferred`.

---

## 2. Master Open Decisions Register (25+ Architectural Choices)

| Decision ID | Area | Technical Decision Context | Options Considered | Recommended / Selected Choice | Architectural Rationale | Status | Target Phase |
|---|---|---|---|---|---|:---:|:---:|
| **DEC-01** | Data Sourcing | Sourcing unstandardized Indian theatrical collection numbers. | A) Manual data entry<br>B) Aggressive scraping<br>C) Curated Kaggle sets + Sacnilk reference | **Option C: Curated Kaggle + Trade Reference** | Avoids scraping IP bans; preserves provenance while capturing Indian nett figures. | **Decided** | Phase 2 |
| **DEC-02** | ML Modeling | Model segmentation: Single global model vs. separate regional models. | A) 5 separate regional models<br>B) Unified global model with market categoricals | **Option B: Unified Global Model** | Prevents overfitting on smaller regional industries (Mollywood/Sandalwood); enables transfer learning. | **Decided** | Phase 7 |
| **DEC-03** | Data Sourcing | Sacnilk data integration method. | A) Reverse-engineer unofficial endpoints<br>B) Curated reference baseline | **Option B: Curated Reference Baseline** | Protects project from brittle web scraping breakages and legal ToS disputes. | **Decided** | Phase 2 |
| **DEC-04** | Data Sourcing | Inclusion of commercial Ormax Cinematix anticipation data. | A) Purchase commercial license<br>B) Exclude Ormax, rely on YouTube/Google Trends | **Option B: Exclude Ormax** | Commercial licensing ($$$) violates student $0 budget constraint. | **Decided** | Phase 2 |
| **DEC-05** | NLP Buzz | Reddit API utilization following post-2023 pricing changes. | A) Pay commercial Reddit tiers<br>B) Use free OAuth tier with rate-limited sampling | **Option B: Free OAuth Rate-Limited Sampling** | Free tier permits 100 req/min; sufficient for sampling r/bollywood and r/tollywood discussions. | **Decided** | Phase 9 |
| **DEC-06** | Database | SQLite vs. PostgreSQL 15 for local development. | A) Start with SQLite, migrate later<br>B) Use PostgreSQL 15 via Docker from Day 1 | **Option B: PostgreSQL from Day 1** | Avoids painful future migration; enables JSONB and pg_trgm fuzzy matching immediately. | **Decided** | Phase 3 |
| **DEC-07** | Feature Eng | Inclusion of post-theatrical OTT streaming deal valuations. | A) Include as pre-release feature<br>B) Exclude from pre-release feature vectors | **Option B: Exclude from Pre-Release** | OTT deals are often finalized post-theatrical; creates lookahead contamination risk. | **Decided** | Phase 5 |
| **DEC-08** | Economics | Anchor baseline calendar year for real-term inflation adjustment. | A) Year 2000 USD<br>B) Constant 2024 USD | **Option B: Constant 2024 USD** | Provides intuitive modern valuation for current film enthusiasts and evaluators. | **Decided** | Phase 3 |
| **DEC-09** | Financials | Mathematical definitions for Indian cinema success tiers. | A) Arbitrary gross thresholds<br>B) Ratio of India Nett Collection to Production Budget | **Option B: Nett Collection / Budget Ratio** | Standard Indian trade definition: Disaster (<50%), Flop (50-75%), Hit (125-175%), Blockbuster (>250%). | **Decided** | Phase 8 |
| **DEC-10** | ML Lifecycle | Prediction lifecycle stage architecture. | A) 5 disjoint trained models<br>B) Single model with feature-availability indicators | **Option B: Single Model with Indicators** | Simplifies MLOps and artifact deployment; CatBoost natively handles missing buzz inputs. | **Decided** | Phase 7 |
| **DEC-11** | NLP Modeling | Selection of primary multilingual sentiment model. | A) mBERT<br>B) XLM-RoBERTa<br>C) Google MuRIL | **Option C: Google MuRIL** | MuRIL was pre-trained specifically on transliterated Roman script and code-mixed Indic languages (Hinglish). | **Decided** | Phase 9 |
| **DEC-12** | Features | Sourcing advance ticket booking numbers. | A) Live scraping BookMyShow<br>B) Trade portal reported day-1 advance numbers | **Option B: Trade Reported Advance Numbers** | Live scraping violates ticketing ToS; trade reports provide validated day-0 benchmarks. | **Decided** | Phase 12 |
| **DEC-13** | Features | Theatrical screen count data availability for catalog films. | A) Require exact screen counts<br>B) Categorical screen tiers (Limited, Wide, Ultra) | **Option B: Categorical Screen Tiers** | Exact historical screen counts are missing for ~40% of older titles; tiers provide stable signal. | **Decided** | Phase 5 |
| **DEC-14** | Frontend | Utilization of Three.js / WebGL 3D visualizers. | A) Heavy 3D canvas landing globe<br>B) Clean 2D SVG charts via Recharts | **Option B: Clean 2D SVG Charts (Recharts)** | 3D canvas introduces heavy GPU overhead on mobile and distracts from analytical data density. | **Decided** | Phase 14 |
| **DEC-15** | Infrastructure| Inclusion of Redis caching layer in MVP. | A) Deploy Redis container immediately<br>B) In-process Python LRU cache; defer Redis | **Option B: Defer Redis to Post-MVP** | Avoids extra container RAM overhead; Python in-memory cache handles MVP concurrency easily. | **Decided** | Phase 13 |
| **DEC-16** | MLOps | Experiment tracking: MLflow vs. Weights & Biases (W&B). | A) Weights & Biases cloud<br>B) Local MLflow tracking server | **Option B: Local MLflow Tracking Server** | 100% open-source, runs locally via SQLite for $0.00 with zero cloud lock-in. | **Decided** | Phase 7 |
| **DEC-17** | MLOps | Dataset versioning: DVC vs. Hash-based Parquet archiving. | A) Full DVC Git-LFS setup<br>B) Semantic hash-based Parquet directory naming | **Option B: Hash-Based Parquet Archiving** | Avoids DVC remote storage setup complexity while ensuring complete audit reproducibility. | **Decided** | Phase 3 |
| **DEC-18** | Compute | Hardware training environment: Local CPU vs. Google Colab. | A) Force everything onto local laptop<br>B) Local CPU for GBDT; Colab T4 GPU for NLP | **Option B: Hybrid (CPU GBDT + Colab NLP)** | CatBoost trains in $<1\text{min}$ on laptop CPU; Colab provides free GPU for MuRIL quantization. | **Decided** | Phase 7 / 9 |
| **DEC-19** | Security | User authentication for initial MVP deployment. | A) Require user login for all features<br>B) Open public read-only; JWT for admin only | **Option B: Public Read-Only + Admin JWT** | Maximizes portfolio accessibility; evaluators can immediately explore without registration friction. | **Decided** | Phase 13 |
| **DEC-20** | Platform | Mobile native app (React Native) vs. Responsive Web. | A) Build iOS/Android apps<br>B) Responsive mobile-first React SPA | **Option B: Responsive Web SPA** | Native apps require expensive developer accounts ($99/year Apple); web SPA covers all devices for $0. | **Decided** | Phase 14 |
| **DEC-21** | Scientific | Target accuracy threshold for model acceptance. | A) Demand unrealistic 90% $R^2$<br>B) Statistically defensible Holdout SMAPE $\le 40\%$ | **Option B: Holdout SMAPE $\le 40.0\%$** | Reflects empirical box-office literature reality; preserves scientific honesty. | **Decided** | Phase 7 |
| **DEC-22** | Features | Sourcing cinematic franchise and sequel lineage data. | A) Manual tagging<br>B) TMDB Collections API + title sequel regex | **Option B: TMDB Collections + Regex** | Programmatically captures 98% of established cinematic franchises. | **Decided** | Phase 5 |
| **DEC-23** | Features | Sourcing promotional marketing spend (P&A budget). | A) Attempt scraping marketing budgets<br>B) Exclude from model; estimate via heuristic | **Option B: Exclude & Heuristic Estimate** | Marketing budgets are strictly confidential studio secrets; almost never publicly disclosed. | **Decided** | Phase 5 |
| **DEC-24** | Localization | Frontend UI language: English-only vs. Multilingual UI. | A) Build multi-language UI (Hindi/Telugu)<br>B) English UI with native-script movie titles | **Option B: English UI + Regional Titles** | English is the universal tech/industry lingua franca; movie titles render in native scripts. | **Decided** | Phase 14 |
| **DEC-25** | Cloud Hosting | Public cloud hosting provider selection. | A) AWS / GCP free tier (spins down/expires)<br>B) Vercel (Front) + Fly.io (Back) + Supabase (DB) | **Option B: Vercel + Fly.io + Supabase** | Permanent, unexpiring free developer tiers with modern Git-driven deployment. | **Decided** | Phase 16 |
