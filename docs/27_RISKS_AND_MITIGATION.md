# CineMetrics — Master Risk Register & Mitigation Strategy

**Document ID:** 27  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [Project Vision](01_PROJECT_VISION.md) | [Security & Governance](22_SECURITY_AND_GOVERNANCE.md) | [Final Technical Decisions](28_FINAL_TECHNICAL_DECISIONS.md)

---

## Table of Contents

1. [Risk Governance Framework & Severity Scoring Matrix](#1-risk-governance-framework--severity-scoring-matrix)
2. [Comprehensive Master Risk Register](#2-comprehensive-master-risk-register)
   - 2.1 [Data Sourcing & Engineering Risks (RSK-DATA)](#21-data-sourcing--engineering-risks-rsk-data)
   - 2.2 [Machine Learning & Algorithmic Risks (RSK-ML)](#22-machine-learning--algorithmic-risks-rsk-ml)
   - 2.3 [Technical Architecture & System Risks (RSK-TECH)](#23-technical-architecture--system-risks-rsk-tech)
   - 2.4 [Financial & Resource Constraint Risks (RSK-FIN)](#24-financial--resource-constraint-risks-rsk-fin)
   - 2.5 [Legal, Ethical & Compliance Risks (RSK-LEG)](#25-legal-ethical--compliance-risks-rsk-leg)
   - 2.6 [Timeline & Execution Risks (RSK-TIME)](#26-timeline--execution-risks-rsk-time)
   - 2.7 [Portfolio Value & Academic Positioning Risks (RSK-PORT)](#27-portfolio-value--academic-positioning-risks-rsk-port)
3. [Continuous Risk Monitoring & Review Cadence](#3-continuous-risk-monitoring--review-cadence)

---

## 1. Risk Governance Framework & Severity Scoring Matrix

CineMetrics evaluates risk using a standard qualitative $3 \times 3$ severity matrix:

$$\text{Risk Score} = \text{Likelihood} \times \text{Impact}$$

- **Likelihood**: Low (1), Medium (2), High (3)
- **Impact**: Low (1), Medium (2), High (3)
- **Classification**:
  - Score **1 – 2**: Low Risk (Monitor routinely)
  - Score **3 – 4**: Medium Risk (Mitigation plan required)
  - Score **6 – 9**: High / Critical Risk (Active architectural mitigation & contingency gate required)

```
       IMPACT ──►     LOW (1)        MEDIUM (2)       HIGH (3)
LIKELIHOOD:
HIGH (3)           [Medium - 3]     [High - 6]      [CRITICAL - 9]
MEDIUM (2)         [Low - 2]        [Medium - 4]    [High - 6]
LOW (1)            [Low - 1]        [Low - 2]       [Medium - 3]
```

---

## 2. Comprehensive Master Risk Register

### 2.1 Data Sourcing & Engineering Risks (RSK-DATA)

| Risk ID | Description | L | I | Score | Proactive Mitigation Strategy | Contingency Plan | Status |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **RSK-DATA-01** | **Indian Box-Office Discrepancies**: Indian collections are not formally audited; Sacnilk, Bollywood Hungama, and producers report conflicting numbers ($\pm 20\%$). | H | H | **9 (Crit)** | Establish strict source arbitration hierarchy; store all raw reports in audit array; compute consensus range. | Display reliability rating badge (`reported` vs. `verified`) and wider conformal prediction bands for disputed films. | Mitigated |
| **RSK-DATA-02** | **Production Budget Sparsity**: TMDB and IMDb frequently report 0 or null for production budgets, especially in regional Indian cinema. | H | H | **9 (Crit)** | Implement KNN budget tier imputation based on primary genre, star power, and production company tier; add `is_budget_imputed` flag. | If imputation confidence is low, fall back to qualitative budget category (`Mid-Tier`, `Big-Budget`) rather than numerical guess. | Mitigated |
| **RSK-DATA-03** | **Historical Snapshot Unavailability**: Pre-release popularity and trailer stats are difficult to retroactively reconstruct for older catalog films (2000–2018). | H | M | **6 (High)** | Train baseline models exclusively on time-invariant structural features (cast, director, budget, franchise, date); harvest live snapshots going forward. | Clearly differentiate Stage 1 historical model performance from live Stage 3/4 inference capabilities. | Mitigated |
| **RSK-DATA-04** | **Third-Party API Rate Limits**: Automated discovery triggers TMDB (40 req/10s) or YouTube (10k units/day) quota exhaustion. | M | M | **4 (Med)** | Implement token bucket client throttling, exponential backoff retries, and strict daily polling quotas. | Pause non-critical buzz polling; prioritize upcoming releases within the 30-day window. | Mitigated |
| **RSK-DATA-05** | **Currency Conversion & Inflation Distortions**: Comparing 2005 INR gross directly against 2024 USD introduces severe economic distortion. | M | H | **6 (High)** | Convert nominal values to real 2024 USD using release-date historical FX rates and monthly US/Indian CPI index deflation series. | Preserve original local nominal currency in database alongside standardized real metrics for auditability. | Mitigated |

---

### 2.2 Machine Learning & Algorithmic Risks (RSK-ML)

| Risk ID | Description | L | I | Score | Proactive Mitigation Strategy | Contingency Plan | Status |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **RSK-ML-01** | **Temporal Lookahead Data Leakage**: Future post-release signals (IMDb ratings, vote counts, opening grosses) accidentally contaminate pre-release feature sets. | M | H | **6 (High)** | Enforce automated leakage tests (`tests/test_leakage.py`) checking feature names and timestamps before every model training run. | Immediate invalidation of model artifacts if leakage is detected; reconstruct training matrix via point-in-time SQL. | Mitigated |
| **RSK-ML-02** | **Extreme Class Imbalance in Success Tiers**: True Blockbusters comprise $<8\%$ of releases, leading to poor classifier recall. | H | M | **6 (High)** | Apply balanced class weighting in CatBoost Classifier; evaluate via Macro $F_1$ and Quadratic Weighted Kappa ($\kappa_w$) rather than raw accuracy. | Apply SMOTE oversampling on minority blockbuster training cohorts if validation recall drops below $0.60$. | Mitigated |
| **RSK-ML-03** | **Regional Sub-Cohort Bias**: Model excels on Hollywood and Bollywood but collapses on Mollywood or Sandalwood due to smaller training sample size. | M | H | **6 (High)** | Enforce mandatory market-segmented validation gates; tune market-specific loss weights; evaluate SMAPE per regional cohort. | Introduce hierarchical market adjustment offsets or dedicated regional GBDT sub-models if global error exceeds $45\%$. | Mitigated |
| **RSK-ML-04** | **Concept & Post-Pandemic Drift**: Box-office behavior shifted dramatically post-2020 (shorter theatrical windows, streaming substitution). | H | M | **6 (High)** | Add `post_pandemic_recovery_index` step feature; use expanding-window walk-forward cross-validation covering 2020–2024. | Weight recent training instances (2021–2024) higher using sample decay weighting. | Mitigated |
| **RSK-ML-05** | **Overconfident Uncertainty Bounds**: Standard confidence intervals fail to capture real black-swan box-office disasters or viral sensations. | M | H | **6 (High)** | Implement MAPIE Conformal Prediction intervals providing formal distribution-free coverage guarantees ($\ge 80\%$). | Expand interval bands for films with Prediction Readiness Score $<60$. | Mitigated |

---

### 2.3 Technical Architecture & System Risks (RSK-TECH)

| Risk ID | Description | L | I | Score | Proactive Mitigation Strategy | Contingency Plan | Status |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **RSK-TECH-01** | **Microservice Complexity Trap**: Over-engineering into distributed microservices causes development gridlock for a solo student developer. | H | H | **9 (Crit)** | Enforce a strict Pragmatic Modular Monolith architecture within a single Python process tree and clean package boundaries. | Resist adding message brokers (Kafka/RabbitMQ) or Kubernetes; rely on APScheduler and in-process memory. | Mitigated |
| **RSK-TECH-02** | **In-Memory ML Inference Latency**: SHAP calculations or transformer sentiment models block the FastAPI async event loop. | M | M | **4 (Med)** | Pre-compute SHAP background values; use quantized MuRIL (INT8) in background workers; execute inference inside threadpool workers. | Pre-aggregate predictions and explanations nightly; serve cached JSON directly from PostgreSQL during HTTP reads. | Mitigated |
| **RSK-TECH-03** | **PostgreSQL Connection Exhaustion**: High concurrent traffic exhausts managed database connection pools. | M | M | **4 (Med)** | Use SQLAlchemy async connection pooling; enforce connection timeouts; configure Supabase Transaction Pooler (port 6543). | Implement in-memory LRU caching on public catalog endpoints to reduce database hits by 70%. | Mitigated |

---

### 2.4 Financial & Resource Constraint Risks (RSK-FIN)

| Risk ID | Description | L | I | Score | Proactive Mitigation Strategy | Contingency Plan | Status |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **RSK-FIN-01** | **Infrastructure Cost Overruns**: Cloud hosting, managed databases, or commercial APIs exceed student developer budget ($0). | M | H | **6 (High)** | Design the architecture around 100% free developer tiers: Vercel (Frontend), Fly.io/Render (Backend), Supabase (Postgres), Local Docker. | Platform runs 100% locally on laptop via Docker Compose without requiring any active cloud hosting. | Mitigated |
| **RSK-FIN-02** | **Paid LLM API Dependencies**: Attempting to generate predictions via OpenAI/Claude API incurs unsustainable token billing. | H | H | **9 (Crit)** | **Core Architectural Rule**: External LLMs are strictly forbidden from generating revenue predictions. We train our own local GBDT models. | Model runs locally for $0.00 marginal cost per prediction. | Mitigated |

---

### 2.5 Legal, Ethical & Compliance Risks (RSK-LEG)

| Risk ID | Description | L | I | Score | Proactive Mitigation Strategy | Contingency Plan | Status |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **RSK-LEG-01** | **API Terms of Service Infringement**: Violating TMDB, IMDb, or YouTube commercial reuse restrictions. | L | H | **3 (Med)** | Design platform strictly as a non-commercial academic portfolio demonstration; display mandatory attribution notices and logos. | If requested by upstream provider, immediately restrict public API access to authenticated evaluator logins. | Mitigated |
| **RSK-LEG-02** | **Aggressive Web Scraping Blacklisting**: IP addresses banned for hammering trade portals. | M | M | **4 (Med)** | Obey `robots.txt`; implement polite request throttling ($\ge 3\text{s}$ delays); rely primarily on official APIs and bulk dumps. | Fall back to manual editorial curation for contested regional data points. | Mitigated |
| **RSK-LEG-03** | **Misinterpreted Financial Advice**: Users treat box-office forecasts as guaranteed investment guidance. | L | M | **2 (Low)** | Prominently display mandatory legal prediction disclaimers across all API responses and UI prediction cards. | State explicitly: *"CineMetrics estimates are statistical research models, not financial advice."* | Mitigated |

---

### 2.6 Timeline & Execution Risks (RSK-TIME)

| Risk ID | Description | L | I | Score | Proactive Mitigation Strategy | Contingency Plan | Status |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **RSK-TIME-01** | **Underestimating Data Engineering Complexity**: Entity resolution and deduplication consume weeks of unplanned debugging. | H | M | **6 (High)** | Allocate 2.5 dedicated weeks in Phase 3; use RapidFuzz and Pandera; maintain a curated 200-film ground truth gold set. | Limit initial catalogue to top 5,000 films with clean TMDB/IMDb IDs before expanding to obscure titles. | Mitigated |
| **RSK-TIME-02** | **Frontend UI Perfectionism Scope Creep**: Spending months tweaking 3D visualizers rather than completing core ML models. | M | M | **4 (Med)** | Prioritize clean, high-contrast Tailwind typography and standard Recharts; defer complex Three.js canvas visualizers. | Build Movie Explorer first; ensure core analytical features work before polishing animations. | Mitigated |

---

### 2.7 Portfolio Value & Academic Positioning Risks (RSK-PORT)

| Risk ID | Description | L | I | Score | Proactive Mitigation Strategy | Contingency Plan | Status |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **RSK-PORT-01** | **Dismissal as a Generic "Toy" Project**: Reviewers mistake CineMetrics for a basic Kaggle movie tutorial. | M | H | **6 (High)** | Emphasize temporal leakage prevention, SHAP explainability, conformal prediction, and autonomous daily discovery in documentation and README. | Showcase the live Upcoming Releases radar (Mode 2), which proves real-world autonomous operational capability. | Mitigated |
| **RSK-PORT-02** | **Dishonest Accuracy Claims**: Claiming $95\%$ prediction accuracy damages professional credibility. | L | H | **3 (Med)** | Honestly report realistic holdout metrics ($\text{SMAPE} \approx 36\%–40\%$) and document the statistical reality of box-office volatility. | Highlight why honest uncertainty intervals are far more scientifically defensible than fake high $R^2$ scores. | Mitigated |

---

## 3. Continuous Risk Monitoring & Review Cadence

The CineMetrics Risk Register is a living governance document:
- **Phase Boundary Reviews**: At the conclusion of each implementation phase, the active developer audits the risk register to verify that mitigations remain effective.
- **Trigger-Based Escalation**: If holdout test metrics violate acceptance gates (e.g. Holdout SMAPE $>40.0\%$), development immediately halts until the underlying data leakage or modeling failure is identified and remediated.
