# CineMetrics — Machine Learning Research & Model Selection

**Document ID:** DOC-10  
**Version:** 1.0  
**Status:** Complete — Planning Phase  
**Last Reviewed:** 2024-01-01  
**Owner:** ML Engineering Team  
**Related Docs:** [07_FEATURE_ENGINEERING.md](07_FEATURE_ENGINEERING.md) · [08_ML_MODEL_ARCHITECTURE.md](08_ML_MODEL_ARCHITECTURE.md) · [09_REVENUE_PREDICTION_REGRESSION.md](09_REVENUE_PREDICTION_REGRESSION.md) · [22_MODEL_EVALUATION_FRAMEWORK.md](22_MODEL_EVALUATION_FRAMEWORK.md)

---

## Table of Contents

1. [Research Objectives](#1-research-objectives)
2. [Problem Formulation](#2-problem-formulation)
3. [Literature Review Summary](#3-literature-review-summary)
4. [Algorithm Research: Regression](#4-algorithm-research-regression)
5. [Algorithm Research: Classification](#5-algorithm-research-classification)
6. [Gradient Boosting Deep Dive](#6-gradient-boosting-deep-dive)
7. [Ensemble Strategy Research](#7-ensemble-strategy-research)
8. [NLP Model Research](#8-nlp-model-research)
9. [SHAP Explainability Research](#9-shap-explainability-research)
10. [Hyperparameter Tuning Strategy](#10-hyperparameter-tuning-strategy)
11. [Temporal Validation Strategy](#11-temporal-validation-strategy)
12. [Final Model Selection Rationale](#12-final-model-selection-rationale)
13. [Baseline Models](#13-baseline-models)
14. [Known Limitations and Failure Modes](#14-known-limitations-and-failure-modes)

---

## 1. Research Objectives

This document records the research and reasoning behind all ML algorithm choices in CineMetrics. It serves two purposes:

1. **Justification:** Every algorithm choice must be grounded in research, not convention.
2. **Reproducibility:** Future developers can understand why XGBoost was chosen over Random Forest, or why CatBoost handles categorical features differently.

### Research Questions Addressed

- What ML algorithms are best suited for tabular box-office revenue prediction?
- How do we handle the extreme right-skewed distribution of movie revenues?
- How do we prevent data leakage across prediction stages?
- What NLP architectures best handle multilingual Indian reviews?
- How do we produce calibrated confidence intervals, not just point predictions?
- How do we ensure predictions are explainable to non-ML users?

---

## 2. Problem Formulation

### 2.1 Revenue Prediction (Regression Task)

**Target Variable:** `log1p(worldwide_gross_usd)` or `log1p(india_net_collection_inr)`

**Why log-transform?**  
Movie revenues are extremely right-skewed. The top 1% of films earn more than the bottom 99% combined. Training on raw gross values causes the model to minimize RMSE by predicting toward the mean, ignoring the low-revenue majority. Log-transforming compresses the scale, normalises the distribution, and makes percentage errors (MAPE) more meaningful than absolute errors (RMSE).

```python
# Target engineering (PLANNED)
import numpy as np

y_raw = df['worldwide_gross_usd']          # Original: 0 to 2.9 billion
y_train = np.log1p(y_raw)                  # log(1+x): 0 → 0, 2.9B → 21.78
y_pred_log = model.predict(X_test)         # Predict in log space
y_pred = np.expm1(y_pred_log)              # Back-transform for reporting
```

**Evaluation Metrics:**
- **Primary:** MAPE (Mean Absolute Percentage Error) in original scale — most intuitive for stakeholders
- **Secondary:** RMSE in log scale — standard regression metric
- **Secondary:** Median Absolute Percentage Error (MdAPE) — robust to outliers
- **Tertiary:** R² in log scale — model fit quality

**Target MAPE:** <35% on held-out test set (ESTIMATED — competitive with industry research)

### 2.2 Success Classification (Multi-Class Classification)

**Target Variable:** `success_tier` ∈ {Disaster, Below Average, Average, Hit, Super Hit, Blockbuster}

**Why classification?**  
Stakeholders think in terms of categories ("will this be a hit?"), not precise revenue figures. Classification is more actionable and communicable. The two tasks (regression + classification) are trained independently to avoid error propagation.

**Evaluation Metrics:**
- **Primary:** Weighted F1-score (accounts for class imbalance)
- **Secondary:** Accuracy (overall)
- **Secondary:** Confusion matrix — especially false-positive rate for "Blockbuster"
- **Tertiary:** AUC-ROC for binary variants (e.g., "is this at least a Hit?")

**Class Imbalance:**  
"Blockbuster" tier has very few films (~2–5% of training data). Strategies: class weighting, SMOTE (carefully — only on tabular features), stratified sampling.

---

## 3. Literature Review Summary

### 3.1 Academic Research on Box-Office Prediction

The following themes emerge from academic literature on box-office prediction (citing conceptual findings — specific papers should be verified):

**Key Finding 1 — Opening Weekend is Dominant but Circular**  
Prior work consistently shows opening weekend gross is the strongest predictor of total gross. However, using actual opening weekend data to predict total gross is not useful for pre-release forecasting. CineMetrics avoids this by defining prediction stages that use only data available at each stage.

**Key Finding 2 — Social Media Signals Improve Short-Term Predictions**  
Twitter/social buzz (measured 1–2 weeks before release) significantly improves predictions of opening weekend performance. For CineMetrics, YouTube trailer engagement is the proxy social signal.

**Key Finding 3 — Gradient Boosted Trees Outperform Neural Networks on Tabular Data**  
Multiple studies on tabular prediction tasks (income, revenue, demand) show XGBoost/LightGBM/CatBoost consistently outperform multi-layer perceptrons on structured data with <100,000 rows. This is a well-established empirical finding. The DNDT and TabTransformer papers provide some counter-evidence but require much more data.

**Key Finding 4 — Star Power Effects are Non-Linear**  
A director's previous success predicts future success non-linearly: very high prior average is predictive, but one blockbuster followed by flops is not. This suggests tree-based models (which can capture non-linear interactions without explicit feature engineering) are preferable to linear models.

**Key Finding 5 — Genre × Budget Interaction Matters**  
An action film with a ₹200 Cr budget is very different from a drama with the same budget. Pure additive models miss this. Tree models naturally capture interaction effects.

**Key Finding 6 — Ensemble Methods Consistently Win**  
Stacking and blending multiple gradient-boosted models typically reduces RMSE by 5–15% compared to individual models in tabular prediction competitions (Kaggle).

### 3.2 Industry Comparators

| Tool/Service | Methodology (Public) | Target Market |
|---|---|---|
| **Quorum** (box office analytics) | Proprietary; reportedly uses exit polls + social | Hollywood studios |
| **RelishMix** | Social media analytics | Hollywood marketing |
| **NRG (National Research Group)** | Survey-based tracking studies | Hollywood studios |
| **Ormax Media** | Pre-release buzz scores, surveys | Indian cinema |
| **Comscore/PostTrak** | Opening day surveys | Hollywood |

None of these are ML-first, open, or focused on Indian cinema. CineMetrics occupies a distinct niche.

---

## 4. Algorithm Research: Regression

### 4.1 Gradient Boosted Trees (Primary Choice)

**Research basis:** XGBoost (Chen & Guestrin, 2016), LightGBM (Ke et al., 2017), CatBoost (Prokhorenkova et al., 2018)

Gradient boosting builds an additive ensemble of weak learners (decision trees) sequentially, with each tree trained on the residuals of the previous. This results in:
- High predictive accuracy on tabular data
- Native handling of missing values (XGBoost/LightGBM)
- Native handling of categorical features (CatBoost)
- Built-in feature importance scores
- Full SHAP support (TreeSHAP — O(T×L) complexity vs. O(2^n) for general SHAP)

See [Section 6](#6-gradient-boosting-deep-dive) for detailed comparison.

### 4.2 Random Forest (Baseline Comparison)

**Purpose:** Strong baseline; resistant to overfitting; good with smaller datasets

**Advantages over GBM:**
- Less hyperparameter-sensitive
- More stable variance (bagging reduces overfitting)
- Faster to train (parallelisable)
- Lower risk of overfitting on small datasets

**Disadvantages:**
- Generally lower accuracy than gradient boosting on this problem size
- Higher memory usage (all trees kept in memory)
- Slower at inference (must traverse all trees)

**Decision:** Use as baseline. If dataset is <2,000 rows, Random Forest may be more reliable than GBM.

### 4.3 Linear Regression (Baseline)

**Purpose:** Interpretable baseline; sanity check; establishes minimum performance floor

**Expected performance:** MAPE ~60–80% (ESTIMATED) — insufficient for production but essential for validating that ML provides meaningful improvement.

**Use:** Train with polynomial features (degree 2) and Ridge/Lasso regularisation. This becomes the "dumb baseline" in model evaluation.

### 4.4 Ridge/Lasso Regression

```
Ridge (L2 regularisation): λ·Σβ²
Lasso (L1 regularisation): λ·Σ|β| → sparse solutions, feature selection
Elastic Net: α·L1 + (1-α)·L2 → combines both
```

**Use in CineMetrics:** Ridge on log-transformed target, with polynomial features for non-linearity. Expected MAPE: 45–60% (ESTIMATED). Better than pure OLS but far below GBM.

### 4.5 Neural Networks (Tabular — Research Status)

**Reviewed approaches:**
- **MLP (Multi-Layer Perceptron):** Standard dense layers. Performs poorly on this dataset size without extensive regularisation.
- **TabNet (Arik & Pfister, 2021):** Attention-based tabular learning. Claims to match GBM. Requires careful tuning and larger datasets.
- **SAINT (Somepalli et al., 2021):** Transformer for tabular data. Very new; limited evidence at our scale.

**Decision:** Neural networks are **excluded from Phase 1** of the ML implementation. They will be evaluated in Phase 2 if the dataset grows to >20,000 high-quality training samples. The added complexity is not justified for the current scope.

---

## 5. Algorithm Research: Classification

### 5.1 Multi-Class Classification from Regression Output

**Strategy 1 — Direct Classification:**  
Train a separate multi-class classifier (XGBoost or LightGBM with `objective='multi:softmax'`) directly on features with class labels derived from CAGR/verdict lookup.

**Strategy 2 — Regression-Then-Threshold:**  
Use the regression model's log-revenue prediction, then apply revenue thresholds to assign class labels:
```
log1p(gross_usd):
  < 14.0  → Disaster        (< ~$1.2M)
  14.0–15.5 → Below Average
  15.5–17.0 → Average
  17.0–18.5 → Hit
  18.5–20.0 → Super Hit
  > 20.0  → Blockbuster     (> ~$485M)
  
# Thresholds differ by market (Indian vs. Hollywood) — see 09_REVENUE_PREDICTION_REGRESSION.md
```

**Strategy 3 — Probability Output + Calibration:**  
Train with `objective='multi:softprob'` to get class probabilities. Apply temperature scaling for calibration. This powers the UI's confidence display.

**Decision:** Use Strategy 3 (probability output) for the classification head. Strategy 2 (regression-then-threshold) is computed in parallel as a cross-check.

### 5.2 Class Imbalance Handling

| Strategy | Mechanism | Trade-off |
|---|---|---|
| `scale_pos_weight` / `class_weight` | Increase loss weight for minority classes | May over-predict minority; standard first choice |
| SMOTE | Synthetic oversampling of minority classes | Tabular SMOTE can create unrealistic feature combinations; use cautiously |
| Stratified k-fold CV | Ensure each fold has proportional class distribution | Required — always use in CV |
| Threshold tuning | Adjust prediction threshold post-training | Improves F1 but may sacrifice accuracy |
| Ensemble of binary classifiers | One-vs-rest classifiers | More complex; use if multi-class direct doesn't work |

**Decision:** Use `class_weight='balanced'` as primary strategy. Use stratified k-fold CV always.

---

## 6. Gradient Boosting Deep Dive

### 6.1 XGBoost vs. LightGBM vs. CatBoost Comparison

| Feature | XGBoost | LightGBM | CatBoost |
|---|---|---|---|
| **Tree growth** | Level-wise (BFS) | Leaf-wise (fastest convergence) | Symmetric (oblivious trees) |
| **Speed (training)** | Moderate | Fastest | Moderate |
| **Speed (inference)** | Moderate | Fast | Very fast (symmetric trees) |
| **Categorical features** | Must encode manually (OHE / label encode) | Built-in (but limited) | Native ordered target encoding |
| **Missing values** | Native handling (learned direction) | Native handling | Requires imputation |
| **Overfitting risk** | Moderate | Higher (leaf-wise) | Lower (symmetric) |
| **Memory usage** | High | Low (histogram-based) | Moderate |
| **SHAP support** | TreeSHAP ✓ | TreeSHAP ✓ | TreeSHAP ✓ |
| **GPU support** | ✓ | ✓ | ✓ |
| **Scikit-learn API** | ✓ | ✓ | ✓ |
| **Hyperparameters** | Many (complex tuning) | Many (complex tuning) | Fewer (simpler tuning) |
| **Best for** | General winner; competitions | Large datasets; speed-critical | Many categorical features |

### 6.2 Why CatBoost is Prioritised for CineMetrics

CineMetrics has an unusually high proportion of **categorical features**:
- Genre (20+ genres, multi-label)
- Production company (hundreds of companies)
- Language (5 Indian + Hollywood)
- Market/circuit
- Distribution company
- Director (high-cardinality)
- Lead actor (high-cardinality)
- Season (Diwali, Eid, Summer, etc.)

CatBoost's ordered target encoding for categorical features avoids **target leakage** (a common pitfall when using standard mean encoding with cross-validation). This is a significant advantage.

> [!IMPORTANT]
> High-cardinality categoricals like `director_name` and `lead_actor` MUST be encoded carefully. Naive one-hot encoding creates thousands of features (most empty). CatBoost's native encoding handles this correctly. For XGBoost/LightGBM, use frequency encoding or embedding lookups.

### 6.3 Key Hyperparameters for Revenue Prediction

```python
# CatBoost — PLANNED hyperparameter search space
catboost_space = {
    'iterations': [300, 500, 1000],
    'learning_rate': [0.01, 0.03, 0.1],
    'depth': [4, 6, 8, 10],
    'l2_leaf_reg': [1, 3, 5, 10],
    'border_count': [32, 64, 128],
    'bagging_temperature': [0.5, 1.0, 2.0],
    'random_strength': [0.5, 1.0, 2.0],
}

# LightGBM — PLANNED hyperparameter search space
lgbm_space = {
    'n_estimators': [300, 500, 1000],
    'learning_rate': [0.01, 0.03, 0.1],
    'max_depth': [4, 6, 8, -1],
    'num_leaves': [15, 31, 63, 127],
    'min_child_samples': [10, 20, 50],
    'subsample': [0.6, 0.8, 1.0],
    'colsample_bytree': [0.6, 0.8, 1.0],
    'reg_alpha': [0, 0.1, 0.5],
    'reg_lambda': [0.1, 1.0, 5.0],
}

# XGBoost — PLANNED hyperparameter search space
xgb_space = {
    'n_estimators': [300, 500, 1000],
    'learning_rate': [0.01, 0.03, 0.1],
    'max_depth': [3, 5, 7, 9],
    'min_child_weight': [1, 3, 5],
    'subsample': [0.6, 0.8, 1.0],
    'colsample_bytree': [0.6, 0.8, 1.0],
    'gamma': [0, 0.1, 0.5],
    'alpha': [0, 0.1, 0.5],
    'lambda': [0.1, 1.0, 5.0],
}
```

---

## 7. Ensemble Strategy Research

### 7.1 Stacking (Meta-Learning)

```
Level 0 (Base Models):
  ├── CatBoostRegressor   → out-of-fold predictions on training set
  ├── LightGBMRegressor   → out-of-fold predictions on training set
  └── XGBoostRegressor    → out-of-fold predictions on training set

Level 1 (Meta-Learner):
  └── RidgeCV(alphas=[0.01, 0.1, 1.0, 10.0]) → final prediction
```

**Key rule:** Base model predictions used as meta-learner features MUST be generated via cross-validation (out-of-fold) on the training set. Using in-fold predictions causes severe overfitting.

**Why Ridge as meta-learner?**  
Simple, interpretable, and prevents overfitting on the small meta-feature matrix (n_features = 3, n_samples = training set size). Tree models as meta-learners tend to overfit badly on stacked predictions.

### 7.2 Blending (Weighted Average)

Simpler than stacking. Assign fixed weights to each model's predictions:

```python
# PLANNED
y_pred_ensemble = (
    0.40 * y_pred_catboost +
    0.35 * y_pred_lgbm +
    0.25 * y_pred_xgb
)
```

Weights determined by validation performance. Can be optimised with Scipy `minimize` over the validation set.

**Advantage:** Faster, simpler, less likely to overfit.  
**Disadvantage:** Cannot learn interactions between model predictions.

**Decision:** Start with weighted blending. Upgrade to stacking only if blending validation MAPE is >5% above individual best model.

### 7.3 Prediction Intervals (Confidence Estimation)

Point predictions alone are insufficient. CineMetrics must provide confidence intervals.

**Strategy: Quantile Regression**
- Train separate models for the 10th, 25th, 50th (median), 75th, and 90th percentiles
- CatBoost supports `loss_function='Quantile:alpha=0.9'` natively
- LightGBM supports `objective='quantile', alpha=0.9` natively

```python
# PLANNED — CatBoost quantile models
from catboost import CatBoostRegressor

model_p10 = CatBoostRegressor(loss_function='Quantile:alpha=0.1', ...)
model_p50 = CatBoostRegressor(loss_function='Quantile:alpha=0.5', ...)
model_p90 = CatBoostRegressor(loss_function='Quantile:alpha=0.9', ...)

# UI displays: "₹200–350 Cr (90% confidence interval)"
```

---

## 8. NLP Model Research

### 8.1 English Sentiment — DistilBERT

**Model:** `distilbert-base-uncased-finetuned-sst-2-english`  
**Source:** HuggingFace Hub  
**Parameters:** 66M (distilled from BERT-base 110M)  
**Input:** Text up to 512 tokens  
**Output:** {POSITIVE, NEGATIVE} with probability  

**Why DistilBERT over BERT-base?**
- 40% smaller, 60% faster, retains 97% of BERT accuracy on GLUE benchmark
- Student-feasible: runs on CPU for inference (slow but possible)
- Well-tested on English movie review sentiment
- Easily fine-tuneable on custom datasets

**Fine-tuning plan (Phase 5):**
```
Pre-trained: distilbert-base-uncased
Fine-tune on: IMDb movie reviews dataset (25K train, 25K test)
Task: Binary sentiment (positive/negative)
Epochs: 3
Batch size: 16
Learning rate: 2e-5 (AdamW)
Expected accuracy: ~92–93% on IMDb test set (ESTIMATED)
```

### 8.2 Multilingual Sentiment — XLM-RoBERTa

**Model:** `cardiffnlp/twitter-xlm-roberta-base-sentiment`  
**Source:** HuggingFace Hub  
**Parameters:** 278M  
**Languages supported:** 100+ including Hindi, Tamil, Telugu, Malayalam, Kannada  
**Input:** Text up to 512 tokens  
**Output:** {Negative, Neutral, Positive}  

**Why XLM-RoBERTa over mBERT?**
- Trained on 2.5TB of multilingual text vs. BERT's 104-language Wikipedia corpus
- Higher token overlap for Devanagari (Hindi) and Dravidian scripts
- Twitter-tuned variant handles informal social media language common in trailer comments

**Alternative — IndicBERT:**  
`ai4bharat/indic-bert` — BERT variant trained specifically on 12 Indian languages. Consider as fine-tuning base for deeper Indian language support. REQUIRES VERIFICATION of performance on sentiment task.

### 8.3 Sentiment Aggregation into Features

Raw model outputs (per-comment) must be aggregated into film-level features:

```python
# PLANNED — sentiment feature extraction
def extract_sentiment_features(comments: list[str], model, tokenizer) -> dict:
    scores = [predict_sentiment(c, model, tokenizer) for c in comments]
    pos_scores = [s['positive'] for s in scores]
    neg_scores = [s['negative'] for s in scores]
    
    return {
        'sentiment_mean_positive': np.mean(pos_scores),
        'sentiment_std_positive': np.std(pos_scores),
        'sentiment_pct_positive': np.mean([s > 0.7 for s in pos_scores]),
        'sentiment_pct_negative': np.mean([s < 0.3 for s in pos_scores]),
        'sentiment_controversy': np.std(pos_scores),  # High std = polarised
        'sentiment_top100_mean': np.mean(sorted(pos_scores, reverse=True)[:100]),  # Top comments
    }
```

---

## 9. SHAP Explainability Research

### 9.1 Why SHAP?

SHAP (SHapley Additive exPlanations) provides a theoretically grounded, unified framework for explaining any ML model. For gradient boosted trees, **TreeSHAP** (Lundberg et al., 2020) computes exact Shapley values in polynomial time (O(T×L²) where T = trees, L = leaves per tree).

**Alternatives considered:**

| Method | Accuracy | Speed | Consistency | CineMetrics Decision |
|---|---|---|---|---|
| TreeSHAP | Exact | Fast for trees | ✓ Theoretically grounded | ✓ Primary choice |
| LIME | Approximate | Slow | ✗ Varies per run | ✗ Rejected |
| Feature Importance (Gini) | Biased | Instant | ✗ Biased for high-cardinality | ✗ Supplementary only |
| Permutation Importance | Approximate | Slow | ✓ Consistent | ✗ Used for global validation |

### 9.2 SHAP Plot Types Used in CineMetrics

| Plot Type | Insight | CineMetrics Use Case |
|---|---|---|
| **Force Plot** | Per-prediction: how each feature pushes prediction up or down | Movie Explorer — per-film explanation |
| **Waterfall Chart** | Cleaner per-prediction breakdown (feature contributions ordered by magnitude) | Movie Explorer — primary explanation UI |
| **Summary Plot (Beeswarm)** | Global: distribution of feature effects across dataset | Analytics page — model understanding |
| **Bar Chart** | Global: mean absolute SHAP values (feature importance) | Model evaluation, documentation |
| **Dependence Plot** | How one feature's SHAP value varies with its feature value | ML research — finding non-linear effects |
| **Heatmap** | SHAP values across many observations | Cluster analysis of similar films |

### 9.3 Implementation Requirements

```python
# PLANNED
import shap

explainer = shap.TreeExplainer(model)  # TreeSHAP — exact for tree models
shap_values = explainer.shap_values(X)  # shape: (n_samples, n_features)

# For a single prediction:
shap_values_single = explainer.shap_values(X[0:1])

# API Response: Return SHAP values + feature names for frontend rendering
# Frontend: Render waterfall chart using D3 or recharts
```

> [!IMPORTANT]
> SHAP values must be computed with the **training data background distribution** (`shap.TreeExplainer(model, background_data=X_train_sample)`). Without background data, SHAP uses a different reference expectation that may produce misleading displays.

---

## 10. Hyperparameter Tuning Strategy

### 10.1 Optuna (Primary Tool)

**Library:** `optuna` (Preferred over GridSearchCV and RandomizedSearchCV)

**Why Optuna?**
- Bayesian optimisation (TPE sampler) — smarter than random search
- Pruning (stops bad trials early — MedianPruner)
- Parallelisable across CPU cores
- MLflow integration for automatic experiment tracking
- Built-in visualisation (importance plots, contour plots)

```python
# PLANNED
import optuna
import mlflow

def objective(trial):
    params = {
        'iterations': trial.suggest_int('iterations', 100, 1000),
        'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.3, log=True),
        'depth': trial.suggest_int('depth', 3, 10),
        'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1e-3, 10.0, log=True),
    }
    
    model = CatBoostRegressor(**params, verbose=0)
    score = cross_val_score(
        model, X_train, y_train, 
        cv=TimeSeriesSplit(n_splits=5),  # Temporal split — critical
        scoring='neg_mean_absolute_percentage_error'
    )
    return score.mean()

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100, timeout=3600)
```

### 10.2 Validation Strategy

**Use TimeSeriesSplit, not standard KFold.**

Movies have temporal structure. Training on films from 2020 and testing on films from 2018 is data leakage — the model could implicitly learn future industry trends. TimeSeriesSplit ensures training data always precedes test data in time.

```
TimeSeriesSplit(n_splits=5) on dataset sorted by release_year:

Split 1: Train [2010–2014] → Validate [2015]
Split 2: Train [2010–2015] → Validate [2016]
Split 3: Train [2010–2016] → Validate [2017]
Split 4: Train [2010–2017] → Validate [2018]
Split 5: Train [2010–2018] → Validate [2019]

Final Test: Held-out [2020–2023] — NEVER touched during tuning
```

---

## 11. Temporal Validation Strategy

### 11.1 The Data Leakage Problem in Movie Prediction

Movie revenue prediction is especially vulnerable to data leakage:

| Leakage Type | Example | Prevention |
|---|---|---|
| **Future feature leakage** | Using IMDb rating of the target movie as an input (rating is post-release) | Strict feature stage gating — see [07_FEATURE_ENGINEERING.md](07_FEATURE_ENGINEERING.md) |
| **Future target leakage** | Training on 2022 data to predict a 2021 release | TimeSeriesSplit CV |
| **Industry trend leakage** | Using 2023 industry sentiment to predict 2020 films | Features must be calculable from data available at prediction time |
| **Cast career stat leakage** | Using actor's total career filmography including future films | Career stats computed only from films released before the target film |

### 11.2 Prediction Stage Feature Availability Matrix

```
                        Stage 1  Stage 2  Stage 3  Stage 4  Stage 5
Feature                 Announce Cast-Lock Trailer   Week-Of  Post-Open
-------------------------------------------------------------------
budget_tier             ✓        ✓        ✓         ✓        ✓
genre                   ✓        ✓        ✓         ✓        ✓
director_prior_avg      ✓        ✓        ✓         ✓        ✓
lead_actor_star_power   ✗        ✓        ✓         ✓        ✓
trailer_view_count      ✗        ✗        ✓         ✓        ✓
trailer_sentiment       ✗        ✗        ✓         ✓        ✓
google_trends_peak      ✗        ✗        ✓         ✓        ✓
advance_booking         ✗        ✗        ✗         ✓        ✓
opening_day_gross       ✗        ✗        ✗         ✗        ✓
```

Each prediction stage uses a **different feature subset**. Separate models are trained per stage, or feature masking is applied to a single model (stage as an input feature).

---

## 12. Final Model Selection Rationale

### Primary Architecture Decision

```
Revenue Prediction (Regression):
  Primary Model:  CatBoostRegressor (best for high-cardinality categoricals)
  Ensemble:       Weighted blend with LightGBMRegressor + XGBoostRegressor
  Meta-Learner:   RidgeCV (for stacking variant)
  Intervals:      CatBoost Quantile models (p10, p25, p50, p75, p90)

Success Classification:
  Primary Model:  LightGBMClassifier (objective='multiclass', fast + accurate)
  Calibration:    CalibratedClassifierCV(method='isotonic')
  
Sentiment (English):
  Model:          distilbert-base-uncased-finetuned-sst-2-english
  Fine-tuning:    Optional Phase 5 — IMDb dataset

Sentiment (Multilingual):
  Model:          cardiffnlp/twitter-xlm-roberta-base-sentiment
  Fine-tuning:    Optional Phase 5 — Translated review corpus

Explainability:
  Framework:      SHAP (TreeSHAP for all gradient boosting models)
```

### Decision Summary Table

| Component | Chosen | Runner-Up | Reason for Choice |
|---|---|---|---|
| Regression model | CatBoost | LightGBM | Native categorical handling; fewer preprocessing steps |
| Ensemble | Weighted blend | Stacking | Simpler; comparable performance on this data size |
| Intervals | Quantile regression | Bootstrap | CatBoost native support; faster |
| Classification | LightGBM | CatBoost | Faster training; multiclass objective well-tested |
| NLP (English) | DistilBERT | BERT-base | 60% faster; 97% accuracy parity |
| NLP (Multilingual) | XLM-RoBERTa | IndicBERT | Broader language coverage; pretrained sentiment model available |
| Explainability | SHAP/TreeSHAP | LIME | Exact values; theoretically grounded; fast for tree models |
| Hyperparameter tuning | Optuna | GridSearchCV | Bayesian optimisation; pruning; better sample efficiency |
| Validation | TimeSeriesSplit | KFold | Prevents temporal leakage; mandatory for time-ordered data |

---

## 13. Baseline Models

Before training the main ensemble, establish baselines:

| Baseline | Implementation | Expected MAPE |
|---|---|---|
| **Mean predictor** | Always predict the training set mean log-gross | ~90–120% |
| **Median predictor** | Always predict the training set median | ~70–90% |
| **Genre mean** | Predict mean gross for the film's genre | ~55–70% |
| **Linear regression** | OLS on log-target, 10 hand-picked features | ~45–55% |
| **Ridge + polynomial** | Ridge with degree-2 features | ~40–50% |
| **Single decision tree** | Depth 5, no pruning | ~50–60% |
| **Random Forest** | 100 trees, default params | ~35–45% |
| **XGBoost (default)** | No hyperparameter tuning | ~30–40% |
| **CatBoost (default)** | No hyperparameter tuning | ~28–38% |
| **Tuned ensemble (target)** | Optuna-tuned blend | <35% |

> [!NOTE]
> These are ESTIMATED baselines based on comparable studies. Actual performance will depend on data quality, feature engineering quality, and dataset size. Update this table with actual results after implementation.

---

## 14. Known Limitations and Failure Modes

| Limitation | Impact | Mitigation |
|---|---|---|
| **Training data skewed toward Hollywood** | Indian cinema model quality may be lower | Separate model training per market; oversample Indian films |
| **Small dataset for Blockbuster tier** | Poor calibration at extreme high end | Oversample; use quantile regression for uncertainty |
| **Marketing spend not available** | Missing major box-office predictor | Proxy with budget × industry_avg_p&a_ratio; flag as missing |
| **Weather/event disruptions** | Predictions ignore external shocks (pandemic, election) | Disclaimer; confidence intervals widen automatically |
| **Franchise sequels** | Different base rate than originals; model may underestimate | Explicit `is_franchise_sequel` and `previous_film_gross` features |
| **Remake/IP films** | Different dynamics than originals | `is_remake`, `source_material_popularity` features |
| **One-week wonder (held) releases** | Model trained on normal theatrical windows | Predict at multiple time horizons; note limited-release flag |
| **OTT-first releases** | No theatrical data possible | Exclude from theatrical model; build separate OTT model in Phase 2+ |
| **Cold start for new directors** | Director track record feature is null | Impute with industry-year median; flag as uncertain |
| **Multi-language releases** | Same film has different grosses by region | Model per market; total India + overseas India as separate targets |

---

*This research document is the foundation for [08_ML_MODEL_ARCHITECTURE.md](08_ML_MODEL_ARCHITECTURE.md) which details the actual implementation architecture, and [22_MODEL_EVALUATION_FRAMEWORK.md](22_MODEL_EVALUATION_FRAMEWORK.md) which defines the evaluation protocol. No models have been trained yet — this is planning documentation only.*
