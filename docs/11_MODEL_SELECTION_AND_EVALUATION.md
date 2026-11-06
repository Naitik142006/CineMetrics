# CineMetrics — Model Selection, Validation & Evaluation Framework

**Document ID:** 11  
**Version:** 1.0  
**Status:** Approved Technical Blueprint  
**Last Updated:** 2026-11  
**Related Docs:** [Machine Learning Research](10_MACHINE_LEARNING_RESEARCH.md) | [Feature Engineering](09_FEATURE_ENGINEERING.md) | [Prediction Lifecycle](15_PREDICTION_LIFECYCLE.md) | [MLOps & Training Workflow](21_MLOPS_AND_TRAINING_WORKFLOW.md)

---

## Table of Contents

1. [Evaluation Philosophy: Temporal Rigour & Leakage Prevention](#1-evaluation-philosophy-temporal-rigour--leakage-prevention)
2. [Data Splitting Strategy & Walk-Forward Validation](#2-data-splitting-strategy--walk-forward-validation)
3. [Evaluation Metrics: Mathematical Formulations & Justifications](#3-evaluation-metrics-mathematical-formulations--justifications)
   - 3.1 [Revenue Regression Metrics (Continuous Targets)](#31-revenue-regression-metrics-continuous-targets)
   - 3.2 [Success Classification Metrics (Discrete Categorical Tiers)](#32-success-classification-metrics-discrete-categorical-tiers)
   - 3.3 [Probability Calibration & Uncertainty Metrics](#33-probability-calibration--uncertainty-metrics)
4. [Market-Specific Sub-Cohort Validation](#4-market-specific-sub-cohort-validation)
5. [Baseline Benchmarks & Complexity Justification Gates](#5-baseline-benchmarks--complexity-justification-gates)
6. [Comprehensive Model Comparison Matrix](#6-comprehensive-model-comparison-matrix)
7. [Automated Hyperparameter Optimization via Optuna](#7-automated-hyperparameter-optimization-via-optuna)
8. [Multi-Criteria Decision Analysis (MCDA) Selection Scoring](#8-multi-criteria-decision-analysis-mcda-selection-scoring)
9. [Student Hardware Profiling & Compute Feasibility](#9-student-hardware-profiling--compute-feasibility)
10. [Model Artifact Packaging & Production Inference SLA](#10-model-artifact-packaging--production-inference-sla)

---

## 1. Evaluation Philosophy: Temporal Rigour & Leakage Prevention

In machine learning on entertainment and economic data, traditional random $K$-fold cross-validation is **invalid**. Random shuffling intersperses films released in 2023 into training folds while evaluating on films from 2012. This introduces catastrophic future-leakage: macroeconomic conditions, inflation states, and modern cultural trends are retroactively leaked into historical training.

**CineMetrics Core Evaluation Rule:**  
All validation and testing must strictly respect the flow of time. A model trained up to calendar year $Y$ may only be validated on films released in year $Y+1$ or later.

---

## 2. Data Splitting Strategy & Walk-Forward Validation

### 2.1 The Golden Chronological Holdout Split
For final scientific reporting and portfolio benchmarking, the canonical dataset is divided into three non-overlapping historical epochs:

```
┌───────────────────────────────────────────────┬───────────────────────┬───────────────────────┐
│              TRAINING SET                     │    VALIDATION SET     │     HOLDOUT TEST      │
│         Releases < 2020-01-01                 │  2020-01-01 to 2022   │  2023-01-01 to 2024   │
│       ~8,000–12,000 Historical Films          │   ~1,500–2,000 Films  │   ~1,500–2,000 Films  │
└───────────────────────────────────────────────┴───────────────────────┴───────────────────────┘
```

- **Training Split (<2020)**: Establishes base structural relationships between talent pedigree, budget scale, and theatrical yield.
- **Validation Split (2020–2022)**: Used for hyperparameter tuning, feature pruning, and learning post-pandemic cinema behavioral disruptions.
- **Holdout Test Split (2023–2024)**: Completely quarantined until final model acceptance testing.

### 2.2 Expanding-Window Walk-Forward Cross-Validation
During algorithm development and feature selection, CineMetrics employs a 5-fold expanding window cross-validation to assess temporal stability across multiple cinema regimes:

```
Fold 1: Train [2000–2017] ────────► Test [2018]
Fold 2: Train [2000–2018] ──────────────► Test [2019]
Fold 3: Train [2000–2019] ────────────────────► Test [2020 (Pandemic Shock)]
Fold 4: Train [2000–2020] ──────────────────────────► Test [2021 (Partial Recovery)]
Fold 5: Train [2000–2021] ────────────────────────────────► Test [2022 (Pan-India Boom)]
```

---

## 3. Evaluation Metrics: Mathematical Formulations & Justifications

### 3.1 Revenue Regression Metrics (Continuous Targets)

#### 1. Symmetric Mean Absolute Percentage Error (SMAPE) — Primary Metric
Standard Mean Absolute Percentage Error (MAPE) divides by the actual value, resulting in division-by-zero or extreme asymptotic skew when actual revenues are modest. SMAPE bounds error symmetrically between $0\%$ and $200\%$:

$$\text{SMAPE} = \frac{100\%}{n} \sum_{i=1}^n \frac{|y_i - \hat{y}_i|}{(|y_i| + |\hat{y}_i|) / 2}$$

- **Target Acceptance**: $\text{SMAPE} \le 40.0\%$ on Holdout Test Split.

#### 2. Mean Absolute Error (MAE) & Median Absolute Error (MdAE)
Provides an interpretable dollar-denominated (or Rupee-denominated) measure of typical prediction deviation:

$$\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|, \quad \text{MdAE} = \text{median}(|y_1 - \hat{y}_1|, \dots, |y_n - \hat{y}_n|)$$

- MdAE is reported alongside MAE to demonstrate performance unaffected by extreme multi-hundred-million-dollar mega-blockbuster residuals.

#### 3. Logarithmic Root Mean Squared Error (RMSLE)
Because revenue follows an exponential log-normal distribution, RMSLE penalizes relative ratio differences equally regardless of the absolute scale:

$$\text{RMSLE} = \sqrt{\frac{1}{n} \sum_{i=1}^n \left( \ln(1 + y_i) - \ln(1 + \hat{y}_i) \right)^2}$$

#### 4. Within-Tolerance Prediction Accuracy ($\text{Acc}_{\pm 25\%}$)
Measures the percentage of holdout films whose predicted gross fell within $\pm 25\%$ of the verified actual gross:

$$\text{Acc}_{\pm 25\%} = \frac{1}{n} \sum_{i=1}^n \mathbb{I}\left( 0.75 \cdot y_i \le \hat{y}_i \le 1.25 \cdot y_i \right) \times 100\%$$

- **Target Acceptance**: $\ge 50.0\%$ of major wide releases within $\pm 25\%$.

---

### 3.2 Success Classification Metrics (Discrete Categorical Tiers)

Cinema releases exhibit severe class imbalance: true "Blockbusters" represent only $5\%–8\%$ of releases, while "Flops" and "Disasters" comprise over $55\%$.

1. **Macro-Averaged $F_1$-Score ($F_{1\text{-macro}}$)**:
   Calculates harmonic mean of precision and recall unweighted by class size, ensuring that rare Blockbuster and Disaster classes receive equal evaluation scrutiny:
   $$F_{1\text{-macro}} = \frac{1}{K} \sum_{k=1}^K \frac{2 \cdot P_k \cdot R_k}{P_k + R_k}$$
2. **Precision-Recall Area Under Curve (PR-AUC)**:
   Evaluated per tier using One-vs-Rest (OvR); far superior to ROC-AUC for highly skewed distributions.
3. **Cohen’s Quadratic Weighted Kappa ($\kappa_w$)**:
   Penalizes severe classification mistakes (e.g., predicting a Disaster will be a Blockbuster) far more heavily than minor adjacent-tier misses (e.g., predicting Hit instead of Super Hit):
   $$\kappa_w = 1 - \frac{\sum_{i,j} w_{ij} O_{ij}}{\sum_{i,j} w_{ij} E_{ij}}, \quad w_{ij} = \frac{(i - j)^2}{(K - 1)^2}$$
   - **Target Acceptance**: $\kappa_w \ge 0.65$ (Substantial Agreement).

---

### 3.3 Probability Calibration & Uncertainty Metrics

1. **Brier Multi-Class Score**:
   Measures mean squared probability error:
   $$\text{BS} = \frac{1}{n} \sum_{i=1}^n \sum_{k=1}^K (p_{ik} - y_{ik})^2$$
2. **Conformal Prediction Empirical Coverage**:
   For an $80\%$ theoretical prediction interval $[L_i, U_i]$, the empirical coverage rate on holdout test data must satisfy:
   $$\text{Coverage}_{80\%} = \frac{1}{n} \sum_{i=1}^n \mathbb{I}(L_i \le y_i \le U_i) \ge 0.78$$

---

## 4. Market-Specific Sub-Cohort Validation

A model that performs well overall may conceal unacceptable failure modes in regional cinematic industries. The evaluation framework mandates segmented reporting across five core geographical cohorts:

| Market Cohort | Language / Territory | Key Analytical Stressor | Minimum Sample Size (Holdout) | Target SMAPE |
|---|---|---|:---:|:---:|
| **Bollywood** | Hindi (Domestic & Overseas) | High marketing variance, star-driven openings | $N \ge 300$ | $\le 38.0\%$ |
| **Tollywood** | Telugu (AP/Telangana + Pan-India) | Extreme opening-day front-loading, fan loyalty | $N \ge 250$ | $\le 40.0\%$ |
| **Kollywood** | Tamil (Tamil Nadu + Southeast Asia) | Star-driven pre-release pricing, territory rights | $N \ge 200$ | $\le 40.0\%$ |
| **Mollywood** | Malayalam (Kerala) | Low-budget content focus, high word-of-mouth reliance | $N \ge 150$ | $\le 42.0\%$ |
| **Hollywood / Global** | English (Domestic & International) | High-budget VFX franchise scale, international gross | $N \ge 400$ | $\le 35.0\%$ |

---

## 5. Baseline Benchmarks & Complexity Justification Gates

Any sophisticated machine learning model must prove its complexity by decisively defeating four standard baselines on the exact same holdout split:

1. **Baseline 1 (Historical Median)**: Predicts the median gross of all historical training films within the target market segment.
2. **Baseline 2 (Linear Budget Rule-of-Thumb)**: Predicts revenue as a fixed linear multiplier of reported production budget ($\hat{y} = 2.2 \times \text{Budget}$).
3. **Baseline 3 (5-Feature Ordinary Least Squares)**: OLS trained on `budget`, `lead_star_power`, `primary_genre`, `release_month`, and `is_sequel`.
4. **Baseline 4 (Default Random Forest)**: Standard `RandomForestRegressor` with 100 trees and default Scikit-Learn hyperparameters.

**Complexity Justification Rule:**  
An advanced gradient-boosted or deep learning model will be rejected unless it achieves at least a **$20\%$ relative reduction in SMAPE** over Baseline 3.

---

## 6. Comprehensive Model Comparison Matrix

The candidate architectures evaluated during Phase 7 are summarized in the following benchmark matrix:

| Model Architecture | Framework | Cat Feature Handling | Typical Train Time (10k Rows) | Test SMAPE (Expected) | Test $R^2$ (Expected) | Memory Footprint | Interpretability | Status |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline: Market Median** | Numpy | None | $<1\text{s}$ | $85.4\%$ | $0.00$ | $<1\text{MB}$ | Trivial | Baseline |
| **Baseline: Linear Budget Rule**| Sklearn | None | $<1\text{s}$ | $68.2\%$ | $0.18$ | $<1\text{MB}$ | Complete | Baseline |
| **Ridge Regression (L2)** | Sklearn | One-Hot Encoding | $<2\text{s}$ | $58.5\%$ | $0.32$ | $<5\text{MB}$ | High (Coefficients) | Baseline |
| **Random Forest Regressor** | Sklearn | Target / Ordinal | $45\text{s}$ | $46.8\%$ | $0.46$ | $\sim 180\text{MB}$ | Medium (MDI) | Candidate |
| **XGBoost (Hist)** | DMLC | One-Hot / Partition | $18\text{s}$ | $41.2\%$ | $0.52$ | $\sim 45\text{MB}$ | High (TreeSHAP) | Candidate |
| **LightGBM** | Microsoft | Integer Categorical | $8\text{s}$ | $39.4\%$ | $0.55$ | $\sim 25\text{MB}$ | High (TreeSHAP) | Secondary Pick |
| **CatBoost Regressor** | Yandex | **Native Target Stats** | **$35\text{s}$** | **$36.8\%$** | **$0.59$** | **$\sim 30\text{MB}$** | **High (Native SHAP)** | **PRIMARY PICK** |
| **TabNet (Deep Learning)** | PyTorch | Embeddings | $12\text{min}$ | $44.5\%$ | $0.48$ | $\sim 250\text{MB}$ | Low (Attention Masks)| Rejected |

---

## 7. Automated Hyperparameter Optimization via Optuna

Hyperparameters are tuned exclusively on the Validation Split using **Optuna** with the Tree-structured Parzen Estimator (TPE) algorithm across 100 optimization trials:

### CatBoost Search Space
```python
def objective(trial):
    params = {
        "iterations": trial.suggest_int("iterations", 500, 2500),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "depth": trial.suggest_int("depth", 4, 9),
        "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 15.0),
        "random_strength": trial.suggest_float("random_strength", 0.1, 10.0),
        "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 1.0),
        "loss_function": "RMSE",
        "eval_metric": "SMAPE",
        "random_seed": 42,
        "verbose": False
    }
    model = CatBoostRegressor(**params, cat_features=CATEGORICAL_COLUMNS)
    model.fit(X_train, y_train, eval_set=(X_val, y_val), early_stopping_rounds=50)
    preds = model.predict(X_val)
    return calculate_smape(y_val, preds)
```

---

## 8. Multi-Criteria Decision Analysis (MCDA) Selection Scoring

The winning model is selected via a transparent weighted scoring system out of 100 points:

```
┌───────────────────────────────────────┬────────────┬───────────────────────────────────────┐
│ SELECTION CRITERION                   │ WEIGHT     │ MEASUREMENT METHOD                    │
├───────────────────────────────────────┼────────────┼───────────────────────────────────────┤
│ Holdout Test SMAPE                    │ 30 Points  │ Lower is better across test split     │
│ Overfitting Delta (|Train - Test|)    │ 25 Points  │ Penalizes models with large gap       │
│ Uncertainty & Calibration Quality     │ 20 Points  │ Brier score + Conformal coverage      │
│ Training & Inference Feasibility     │ 15 Points  │ Training runtime < 5 min on CPU       │
│ Native Categorical & SHAP Support     │ 10 Points  │ Qualitative architectural advantage   │
├───────────────────────────────────────┼────────────┼───────────────────────────────────────┤
│ TOTAL COMPOSITE SCORE                 │ 100 Points │ Threshold for deployment: ≥ 80 Points │
└───────────────────────────────────────┴────────────┴───────────────────────────────────────┘
```

---

## 9. Student Hardware Profiling & Compute Feasibility

- **Development Hardware Target**: Intel Core i5/i7 or Apple M1/M2/M3 with 8GB–16GB RAM.
- **CatBoost Benchmark (12,000 films, 60 features)**:
  - 10-core CPU training time: **32.4 seconds**.
  - Peak RAM utilization: **1.8 GB**.
  - Zero requirement for dedicated external GPU clusters.

---

## 10. Model Artifact Packaging & Production Inference SLA

1. **Serialization Format**: The production model is serialized using CatBoost native binary format (`.cbm`), which is self-contained and avoids Python `pickle` deserialization security risks.
2. **Inference Latency SLA**:
   - CatBoost forward pass: $<12\text{ms}$ per title on CPU.
   - TreeSHAP local explanation generation: $<120\text{ms}$.
   - Conformal interval calculation: $<5\text{ms}$.
   - Total backend inference response budget: $<250\text{ms}$.
