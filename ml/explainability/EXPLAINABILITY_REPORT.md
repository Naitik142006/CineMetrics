# CineMetrics — Explainability, Conformal Uncertainty & Risk Engine Report

**Execution Phase:** Phase 10 (Explainability & Financial Risk Engine)  
**Baseline Expected Value:** `7.3533` log10 (~`$22,560,484.89` USD)  
**Additivity Axiom Pass Rate:** `100.0%` (Max Residual Error: `3.55e-15`)  
**TreeSHAP CPU Latency:** Mean: `16.34ms` | P95: `21.68ms` (Target $<100$ms Achieved)  

---

## 1. Executive Prediction & Downside Risk Audit

| Movie Title | Industry | Budget | Pessimistic (80% Low) | Expected Forecast (USD / INR) | Optimistic (80% High) | Break-Even Prob | 2.5x Profit Prob | Risk Assessment |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Wind River** | Hollywood | `$14.10M` | `$493,375` | **`$3.39M`** / `₹28.48 Cr` | `$23.29M` | `17.2%` | `6.0%` | 🔴 HIGH RISK |
| **Star Wars: Episode VIII - The Last Jedi** | Hollywood | `$406.37M` | `$33.30M` | **`$228.82M`** / `₹1922.11 Cr` | `$1572.25M` | `35.1%` | `16.1%` | 🟠 ELEVATED |
| **Crawl** | Hollywood | `$16.59M` | `$5.28M` | **`$36.31M`** / `₹304.99 Cr` | `$249.47M` | `69.9%` | `46.5%` | 🟡 MODERATE |
| **Avengers: Endgame** | Hollywood | `$437.45M` | `$44.67M` | **`$306.90M`** / `₹2577.98 Cr` | `$2108.74M` | `40.7%` | `19.9%` | 🟠 ELEVATED |
| **Avengers: Infinity War** | Hollywood | `$401.67M` | `$57.59M` | **`$395.73M`** / `₹3324.14 Cr` | `$2719.08M` | `49.6%` | `26.8%` | 🟠 ELEVATED |
| **The Lion King** | Hollywood | `$319.48M` | `$92.61M` | **`$636.36M`** / `₹5345.39 Cr` | `$4372.43M` | `67.7%` | `44.0%` | 🟡 MODERATE |

---

## 2. Local TreeSHAP Feature Drivers & Dollar Impact Breakdown

### 🎬 Wind River (Hollywood)

> **Executive Narrative:** *"The box-office forecast of $3.4M for 'Wind River' reflects cautious theatrical expectations, weighed down predominantly by Primary Genre Appeal (-$2.6M), Director Career Hit Rate (-$2.4M). Key supporting factors mitigating downside risk include Theatrical Runtime (+$613,709), Lead Actor Filmography Volume (+$223,025), Summer Blockbuster Seasonality (+$79,510)."*

| Attribution Category | Feature Identifier | Feature Value | SHAP log10 | Estimated Dollar Impact | Direction |
|---|---|---|:---:|:---:|:---:|
| 🟢 **Key Driver** | `Theatrical Runtime` | `107.0` | `+0.0294` | **`+$613,709`** | Positive |
| 🟢 **Key Driver** | `Lead Actor Filmography Volume` | `3.0` | `+0.0107` | **`+$223,025`** | Positive |
| 🔴 **Drag Factor** | `Primary Genre Appeal` | `Crime` | `-0.1266` | **`-$2.65M`** | Negative |
| 🔴 **Drag Factor** | `Director Career Hit Rate` | `0.39836289222373805` | `-0.1132` | **`-$2.37M`** | Negative |


### 🎬 Star Wars: Episode VIII - The Last Jedi (Hollywood)

> **Executive Narrative:** *"The box-office forecast of $228.8M for 'Star Wars: Episode VIII - The Last Jedi' represents an above-average projection, driven primarily by strong positive contributions from Production Budget Scale (+$77.2M), Capital Expenditure Tier (+$38.9M), Studio Scale & Track Record (+$26.4M). This upside is partially moderated by drag from Director Career Hit Rate (-$8.8M), Lead Actor Star Power (-$7.5M)."*

| Attribution Category | Feature Identifier | Feature Value | SHAP log10 | Estimated Dollar Impact | Direction |
|---|---|---|:---:|:---:|:---:|
| 🟢 **Key Driver** | `Production Budget Scale` | `8.60892213167357` | `+0.5993` | **`+$77.16M`** | Positive |
| 🟢 **Key Driver** | `Capital Expenditure Tier` | `Tentpole` | `+0.3022` | **`+$38.90M`** | Positive |
| 🔴 **Drag Factor** | `Director Career Hit Rate` | `0.43052930056710775` | `-0.0684` | **`-$8.81M`** | Negative |
| 🔴 **Drag Factor** | `Lead Actor Star Power` | `Daisy Ridley` | `-0.0585` | **`-$7.53M`** | Negative |


### 🎬 Crawl (Hollywood)

> **Executive Narrative:** *"The box-office forecast of $36.3M for 'Crawl' represents an above-average projection, driven primarily by strong positive contributions from Studio Scale & Track Record (+$4.9M), Director Brand Equity (+$1.3M), Lead Actor Career Hit Rate (+$664,030). This upside is partially moderated by drag from Lead Actor Star Power (-$1.5M), Theatrical Runtime (-$1.3M)."*

| Attribution Category | Feature Identifier | Feature Value | SHAP log10 | Estimated Dollar Impact | Direction |
|---|---|---|:---:|:---:|:---:|
| 🟢 **Key Driver** | `Studio Scale & Track Record` | `73.0` | `+0.3092` | **`+$4.93M`** | Positive |
| 🟢 **Key Driver** | `Director Brand Equity` | `Alexandre Aja` | `+0.0802` | **`+$1.28M`** | Positive |
| 🔴 **Drag Factor** | `Lead Actor Star Power` | `Kaya Scodelario` | `-0.0921` | **`-$1.47M`** | Negative |
| 🔴 **Drag Factor** | `Theatrical Runtime` | `87.0` | `-0.0816` | **`-$1.30M`** | Negative |


### 🎬 Avengers: Endgame (Hollywood)

> **Executive Narrative:** *"The box-office forecast of $306.9M for 'Avengers: Endgame' represents an above-average projection, driven primarily by strong positive contributions from Production Budget Scale (+$108.9M), Capital Expenditure Tier (+$51.5M), Franchise & Sequel IP Recognition (+$19.7M). This upside is partially moderated by drag from Director Career Hit Rate (-$13.8M), Genre Blend Breadth (-$9.3M)."*

| Attribution Category | Feature Identifier | Feature Value | SHAP log10 | Estimated Dollar Impact | Direction |
|---|---|---|:---:|:---:|:---:|
| 🟢 **Key Driver** | `Production Budget Scale` | `8.640925450647766` | `+0.6340` | **`+$108.89M`** | Positive |
| 🟢 **Key Driver** | `Capital Expenditure Tier` | `Tentpole` | `+0.2997` | **`+$51.47M`** | Positive |
| 🔴 **Drag Factor** | `Director Career Hit Rate` | `0.4618760285244103` | `-0.0805` | **`-$13.82M`** | Negative |
| 🔴 **Drag Factor** | `Genre Blend Breadth` | `1.0` | `-0.0539` | **`-$9.26M`** | Negative |


### 🎬 Avengers: Infinity War (Hollywood)

> **Executive Narrative:** *"The box-office forecast of $395.7M for 'Avengers: Infinity War' represents an above-average projection, driven primarily by strong positive contributions from Production Budget Scale (+$135.2M), Capital Expenditure Tier (+$70.0M), Franchise & Sequel IP Recognition (+$25.0M). This upside is partially moderated by drag from Director Career Hit Rate (-$16.9M), Lead Actor Career Hit Rate (-$10.5M)."*

| Attribution Category | Feature Identifier | Feature Value | SHAP log10 | Estimated Dollar Impact | Direction |
|---|---|---|:---:|:---:|:---:|
| 🟢 **Key Driver** | `Production Budget Scale` | `8.603864500392081` | `+0.6183` | **`+$135.15M`** | Positive |
| 🟢 **Key Driver** | `Capital Expenditure Tier` | `Tentpole` | `+0.3202` | **`+$69.98M`** | Positive |
| 🔴 **Drag Factor** | `Director Career Hit Rate` | `0.0` | `-0.0774` | **`-$16.91M`** | Negative |
| 🔴 **Drag Factor** | `Lead Actor Career Hit Rate` | `0.0` | `-0.0479` | **`-$10.47M`** | Negative |


### 🎬 The Lion King (Hollywood)

> **Executive Narrative:** *"The box-office forecast of $636.4M for 'The Lion King' represents an above-average projection, driven primarily by strong positive contributions from Production Budget Scale (+$235.4M), Capital Expenditure Tier (+$108.9M), Primary Genre Appeal (+$59.8M). This upside is partially moderated by drag from Lead Actor Star Power (-$22.1M), Genre Blend Breadth (-$7.3M)."*

| Attribution Category | Feature Identifier | Feature Value | SHAP log10 | Estimated Dollar Impact | Direction |
|---|---|---|:---:|:---:|:---:|
| 🟢 **Key Driver** | `Production Budget Scale` | `8.504448800644333` | `+0.6416` | **`+$235.36M`** | Positive |
| 🟢 **Key Driver** | `Capital Expenditure Tier` | `Tentpole` | `+0.2968` | **`+$108.86M`** | Positive |
| 🔴 **Drag Factor** | `Lead Actor Star Power` | `Donald Glover` | `-0.0603` | **`-$22.12M`** | Negative |
| 🔴 **Drag Factor** | `Genre Blend Breadth` | `1.0` | `-0.0200` | **`-$7.32M`** | Negative |


---

## 3. Global Feature Attribution Importance (Mean |SHAP|)

| Rank | Feature Identifier | Display Name | Mean Absolute SHAP (log10) | Relative Impact Share |
|:---:|---|---|:---:|:---:|
| 1 | `log_budget` | **log_budget** | `0.2899` | `30.2%` |
| 2 | `studio_prior_movies` | **studio_prior_movies** | `0.1084` | `11.3%` |
| 3 | `director` | **director** | `0.1013` | `10.6%` |
| 4 | `primary_genre` | **primary_genre** | `0.0922` | `9.6%` |
| 5 | `director_prior_hit_rate` | **director_prior_hit_rate** | `0.0878` | `9.2%` |
| 6 | `budget_tier` | **budget_tier** | `0.0679` | `7.1%` |
| 7 | `runtime_minutes_clean` | **runtime_minutes_clean** | `0.0637` | `6.6%` |
| 8 | `lead_actor` | **lead_actor** | `0.0596` | `6.2%` |
| 9 | `genre_count` | **genre_count** | `0.0451` | `4.7%` |
| 10 | `lead_actor_prior_hit_rate` | **lead_actor_prior_hit_rate** | `0.0435` | `4.5%` |

---

## 4. Architectural & Production Readiness Sign-Off

1. **Exact Local Accuracy (Efficiency Axiom):** 100% of tested instances satisfied $f(x) = \phi_0 + \sum \phi_i$ to machine precision ($<10^{-14}$ residual difference).
2. **Sub-100ms Inference Constraint:** Local explanations generate in $\approx 16\text{ms}$ mean latency on CPU, enabling instant rendering of waterfall diagrams on the React frontend.
3. **Operational Conformal Uncertainty:** Packaged 80% and 95% finite-sample prediction intervals provide defensible pessimistic/optimistic operational scenarios.
4. **FastAPI Serving Ready:** `ExplainerService` initialized in `backend/app/ml/explainer_service.py` as an in-memory singleton for immediate API route mounting.
