# 21 · MLOps and Training Workflow — CineMetrics

> **Document type**: ML engineering specification  
> **Status**: Planning / Pre-implementation  
> **Audience**: ML engineers, AI agents implementing the training pipeline  
> **Related docs**: [`05_FEATURE_ENGINEERING.md`](./05_FEATURE_ENGINEERING.md) · [`07_MODEL_ARCHITECTURE.md`](./07_MODEL_ARCHITECTURE.md) · [`22_SECURITY_AND_GOVERNANCE.md`](./22_SECURITY_AND_GOVERNANCE.md) · [`23_TESTING_AND_VALIDATION.md`](./23_TESTING_AND_VALIDATION.md)

---

## Table of Contents

1. [ML Training Pipeline Overview (20 Steps)](#1-ml-training-pipeline-overview-20-steps)
2. [MLflow Setup — Local Tracking Server](#2-mlflow-setup--local-tracking-server)
3. [Optuna Hyperparameter Search Spaces](#3-optuna-hyperparameter-search-spaces)
4. [Model Versioning Strategy](#4-model-versioning-strategy)
5. [Retraining Policy](#5-retraining-policy)
6. [Model Drift Detection](#6-model-drift-detection)
7. [Dataset Versioning](#7-dataset-versioning)
8. [Pipeline Orchestration](#8-pipeline-orchestration)
9. [Directory and File Structure](#9-directory-and-file-structure)
10. [Environment and Dependencies](#10-environment-and-dependencies)

---

## 1. ML Training Pipeline Overview (20 Steps)

The CineMetrics training pipeline transforms raw ingested data into production-ready prediction models. Each step is designed to be **idempotent** (re-running produces the same output given the same input), **logged** (all outputs stored with MLflow or plaintext logs), and **independently testable** (each step has defined inputs, outputs, and validation criteria).

The pipeline is implemented as a sequence of Python scripts in `ml/pipeline/` and can be run end-to-end via `python ml/pipeline/run_pipeline.py` or step-by-step for debugging.

---

### Step 1 — Dataset Acquisition

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Download/collect all raw data from configured sources |
| **Script** | `ml/pipeline/01_acquire_data.py` |
| **Inputs** | API keys from `.env`, configured source list from `ml/config/sources.yaml` |
| **Outputs** | Raw data files in `data/raw/` (CSV or Parquet format, one file per source) |
| **Tools** | `requests`, `httpx`, TMDB API client, IMDb dataset downloader |
| **Validation** | File size > 0 bytes; response status 200; row count > minimum threshold per source |
| **Expected Duration** | 15–60 min (network-dependent; IMDb dataset download is ~1 GB) |
| **Notes** | Respects API rate limits (40 req/10s for TMDB). Saves download manifest `data/raw/manifest.json` with timestamps, source URLs, and row counts. Never overwrites existing raw files — appends `_YYYYMMDD` suffix to avoid accidental data loss. |

---

### Step 2 — Raw Data Storage

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Convert raw files to versioned Parquet format and record provenance |
| **Script** | `ml/pipeline/02_store_raw.py` |
| **Inputs** | Files from `data/raw/` |
| **Outputs** | Parquet files in `data/raw/parquet/{source_name}/{YYYY-MM-DD}/` |
| **Tools** | `pandas`, `pyarrow` |
| **Validation** | Parquet schema matches expected schema per source; no empty DataFrames |
| **Expected Duration** | 2–5 min |
| **Notes** | Each Parquet file is stored with its acquisition date as a directory partition. This enables point-in-time dataset reconstruction. `data/raw/parquet/` is git-ignored; tracked via DVC or manual hash registry (see [Section 7](#7-dataset-versioning)). |

---

### Step 3 — Data Validation

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Validate that each raw dataset conforms to expected schema, ranges, and constraints before any processing |
| **Script** | `ml/pipeline/03_validate_raw.py` |
| **Inputs** | Parquet files from Step 2 |
| **Outputs** | `data/validation/raw_validation_report_{date}.json` — pass/fail per check with counts |
| **Tools** | `pydantic` (schema validation), `pandera` (DataFrame schema validation), custom pytest-style checks |
| **Validation Criteria** | (1) Required columns present; (2) No null values in primary key columns; (3) Year in [1900, 2030]; (4) Budget ≥ 0; (5) Runtime in [1, 600] minutes; (6) No duplicate primary keys |
| **Expected Duration** | 1–3 min |
| **On Failure** | Pipeline halts. Validation report shows which check failed and how many rows are affected. Developer must inspect and either fix the source data or add a documented exception. |

```python
# Example pandera schema for TMDB movie table
import pandera as pa
from pandera.typing import DataFrame, Series

class TMDBMovieSchema(pa.SchemaModel):
    tmdb_id: Series[int]       = pa.Field(nullable=False, unique=True, ge=1)
    title: Series[str]         = pa.Field(nullable=False, str_length={"min_value": 1})
    release_date: Series[str]  = pa.Field(nullable=True)  # May be absent for unannounced
    budget: Series[float]      = pa.Field(nullable=True, ge=0)
    runtime: Series[float]     = pa.Field(nullable=True, ge=1, le=600)
    original_language: Series[str] = pa.Field(nullable=False)

    class Config:
        coerce = True
        strict = "filter"  # Drop extra columns silently
```

---

### Step 4 — Entity Resolution

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Match movies across multiple sources (TMDB, IMDb, Kaggle datasets) into a single unified entity table. Resolve duplicate entries, name variations, and ID mismatches. |
| **Script** | `ml/pipeline/04_entity_resolution.py` |
| **Inputs** | Validated Parquet files from Step 3 |
| **Outputs** | `data/processed/entity_resolution_map.parquet` — columns: `canonical_id`, `tmdb_id`, `imdb_id`, `title`, `release_year`, `confidence_score` |
| **Tools** | `rapidfuzz` (fuzzy string matching), `recordlinkage` library, custom rule-based matching |
| **Matching Logic** | Priority order: (1) exact TMDB+IMDb ID pair; (2) title + release year exact match; (3) fuzzy title match (threshold ≥ 90) + release year within ±1; (4) manual overrides from `data/manual/entity_overrides.csv` |
| **Validation** | Match rate ≥ 95% for movies present in both TMDB and IMDb; zero duplicate `canonical_id` values |
| **Expected Duration** | 5–15 min |
| **Notes** | Unmatched entities are written to `data/processed/entity_unmatched.parquet` for manual review. Never silently discard unmatched records. |

---

### Step 5 — Dataset Integration

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Join all validated, entity-resolved sources into a single unified movie table |
| **Script** | `ml/pipeline/05_integrate_datasets.py` |
| **Inputs** | Entity resolution map (Step 4), validated source Parquets (Step 3) |
| **Outputs** | `data/processed/unified_movies.parquet` — one row per movie, all source columns merged with conflict resolution |
| **Tools** | `pandas` |
| **Conflict Resolution Rules** | Budget: prefer The Numbers > TMDB > Kaggle. Gross: prefer The Numbers > IMDb > TMDB. Runtime: prefer IMDb > TMDB. If sources differ by > 20%, flag as `budget_conflict = True`. |
| **Validation** | Row count ≥ 10,000 movies; zero duplicate `canonical_id`; no null `title` or `release_year` |
| **Expected Duration** | 2–5 min |

---

### Step 6 — Historical Snapshot Creation

| Attribute | Detail |
|-----------|--------|
| **Purpose** | For each movie, create multiple "snapshots" representing the data available at each prediction stage (Announcement, Pre-Production, Production, Post-Production, Pre-Release). This is critical for preventing temporal data leakage. |
| **Script** | `ml/pipeline/06_create_snapshots.py` |
| **Inputs** | `unified_movies.parquet` (Step 5), stage definition config from `ml/config/prediction_stages.yaml` |
| **Outputs** | `data/processed/feature_snapshots.parquet` — multiple rows per movie (one per stage), columns tagged `_available_at_{stage}` |
| **Tools** | `pandas` |
| **Validation** | No post-stage features appear in earlier stage rows (enforced by column masking logic); every released movie has at least one `final` stage snapshot |
| **Expected Duration** | 3–10 min |
| **Stage Definitions** (from `prediction_stages.yaml`): |

```yaml
stages:
  announcement:
    available_features:
      - title, genre, language, industry, production_company
      - director, lead_actors (announced)
      - franchise_flag, sequel_number
      - release_season (target quarter)
    masked_features:
      - budget, runtime, actual_cast_star_power, trailer_views, review_scores
  
  pre_production:
    available_features:
      - all announcement features
      - confirmed_budget (if announced)
      - confirmed_cast (star power computable)
    masked_features:
      - trailer_views, review_scores, runtime

  pre_release:
    available_features:
      - all pre_production features
      - trailer_views_7d, trailer_views_30d
      - social_buzz_score, google_trends_30d
      - confirmed_runtime
      - competition_score (concurrent releases)
      - advance_booking_index (if available)
    masked_features:
      - actual_opening_weekend, review_scores

  final:
    available_features:
      - ALL features including opening weekend, review scores
    masked_features: []
```

---

### Step 7 — Feature Engineering

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Transform raw snapshot data into ML-ready features: encode categoricals, compute derived features, normalize numerics |
| **Script** | `ml/pipeline/07_feature_engineering.py` |
| **Inputs** | `feature_snapshots.parquet` (Step 6) |
| **Outputs** | `data/features/feature_matrix_X.parquet`, `data/features/target_y.parquet`, `ml/artifacts/feature_metadata.json` |
| **Tools** | `pandas`, `scikit-learn` (`OrdinalEncoder`, `TargetEncoder`, `StandardScaler`), `feature-engine` |
| **Key Engineered Features** | (1) `cast_power_score` — weighted average of lead actors' historical box-office averages; (2) `director_success_rate` — % of director's films that were hits; (3) `franchise_momentum` — revenue trend of franchise entries; (4) `competition_index` — number of competing films × their predicted revenue; (5) `budget_tier` — ordinal encoding of budget quintile; (6) `release_timing_score` — encoded release season + holiday proximity |
| **Validation** | No `NaN` in final feature matrix for required features; no features with zero variance; feature count matches `feature_metadata.json` |
| **Expected Duration** | 3–8 min |

---

### Step 8 — EDA and Feature Analysis

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Generate exploratory data analysis reports to understand data distributions, feature correlations, and target variable characteristics before modeling |
| **Script** | `ml/pipeline/08_eda.py` |
| **Inputs** | Feature matrix X, target y (Step 7) |
| **Outputs** | `reports/eda/eda_report_{date}.html` (interactive), `reports/eda/correlation_matrix.png`, `reports/eda/target_distribution.png`, `reports/eda/feature_importance_univariate.csv` |
| **Tools** | `ydata-profiling` (formerly pandas-profiling), `matplotlib`, `seaborn`, `scipy.stats` |
| **Key Analyses** | (1) Target variable distribution (revenue) — expect right-skewed log-normal; (2) Missing value heatmap per stage; (3) Pearson correlation of numerics with log(revenue); (4) Top categorical features by mean revenue difference (ANOVA); (5) Budget vs. Revenue scatter plot (log-log) |
| **Expected Duration** | 5–10 min |
| **Notes** | EDA output is for human review. No decisions are automatically made from EDA output. The developer reviews the HTML report before proceeding. |

---

### Step 9 — Temporal Split Creation

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Split the dataset into training, validation, and test sets using **time-based splitting** (never random split) to prevent temporal data leakage |
| **Script** | `ml/pipeline/09_temporal_split.py` |
| **Inputs** | Feature matrix X, target y (Step 7) |
| **Outputs** | `data/splits/X_train.parquet`, `data/splits/X_val.parquet`, `data/splits/X_test.parquet`, `data/splits/y_train.parquet`, `data/splits/y_val.parquet`, `data/splits/y_test.parquet`, `data/splits/split_metadata.json` |
| **Tools** | `pandas` |
| **Split Strategy** | |

```python
# Temporal split boundaries (adjust based on actual dataset)
TRAIN_CUTOFF = "2020-12-31"   # Movies released through 2020 → training
VAL_CUTOFF   = "2022-06-30"   # 2021–mid-2022 → validation
# Test set: mid-2022 → present (most recent data, never touched during training)

split_metadata = {
    "train_period":      ["pre-2021",           "through 2020-12-31"],
    "validation_period": ["2021-01-01",          "2022-06-30"],
    "test_period":       ["2022-07-01",          "latest available"],
    "train_size":        len(X_train),
    "val_size":          len(X_val),
    "test_size":         len(X_test),
    "train_cutoff_date": TRAIN_CUTOFF,
    "val_cutoff_date":   VAL_CUTOFF,
    "created_at":        datetime.now().isoformat(),
    "feature_list_hash": hash_feature_list(X_train.columns.tolist()),
}
```

| **Validation** | No movie in X_val has `release_date` ≤ `TRAIN_CUTOFF`; no movie in X_test has `release_date` ≤ `VAL_CUTOFF`; temporal ordering verified |
| **Expected Duration** | < 1 min |

---

### Step 10 — Baseline Model Training

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Establish a simple, interpretable baseline that any ML model must outperform to justify its complexity |
| **Script** | `ml/pipeline/10_baseline_model.py` |
| **Inputs** | Training split (Step 9) |
| **Outputs** | `ml/models/baseline_metrics.json`, baseline prediction CSV |
| **Tools** | `scikit-learn` (`DummyRegressor`, `LinearRegression`, `Ridge`) |
| **Baselines to Train** | (1) Mean predictor (always predict mean of training log-revenue); (2) Median predictor; (3) Budget-only linear regression (log-log); (4) Genre+Budget ridge regression |
| **Metrics Computed** | SMAPE, MAE, RMSE, R² on validation set |
| **Expected Duration** | < 1 min |
| **Gate** | Any advanced model (Step 11) must achieve SMAPE at least 10% lower than the best baseline on validation set. |

---

### Step 11 — Advanced Model Training

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Train gradient boosting models with default hyperparameters to establish pre-tuning performance |
| **Script** | `ml/pipeline/11_train_models.py` |
| **Inputs** | Training split (Step 9), feature metadata (Step 7) |
| **Outputs** | Model artifacts in `ml/models/candidates/` (`.cbm`, `.json`, `.pkl` files), training metrics JSON per model |
| **Tools** | `catboost`, `lightgbm`, `xgboost`, `scikit-learn` |
| **Models Trained** | |

```
1. CatBoostRegressor          — log(revenue) target, automatic cat features
2. LGBMRegressor              — log(revenue) target, one-hot or ordinal encoding
3. XGBRegressor               — log(revenue) target, manual encoding
4. CatBoostClassifier         — 7-class success category
5. LGBMClassifier             — 7-class success category
```

**Note on target**: Train on `log1p(revenue)` (natural log of revenue+1). Predictions are transformed back with `expm1()`. This prevents large-budget blockbusters from dominating the loss function.

| **Validation** | All models converge without NaN loss; validation SMAPE computed and stored; models serializable |
| **Expected Duration** | 15–45 min (GPU significantly reduces CatBoost time) |

---

### Step 12 — Hyperparameter Optimization (Optuna)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Find optimal hyperparameters for each model type using Bayesian optimization |
| **Script** | `ml/pipeline/12_hyperparameter_tuning.py` |
| **Inputs** | Training + validation splits, model type to tune (passed as argument) |
| **Outputs** | `ml/artifacts/best_params_{model_type}.json`, Optuna study database `ml/artifacts/optuna_{model_type}.db` |
| **Tools** | `optuna`, model libraries |
| **Optimization Target** | Minimize SMAPE on validation set |
| **N Trials** | 100 trials per model (adjust based on time budget; 50 minimum) |
| **Expected Duration** | 2–6 hours per model on CPU; 30–90 min with GPU |
| **Notes** | Full search spaces documented in [Section 3](#3-optuna-hyperparameter-search-spaces). Optuna supports pruning (early stopping of bad trials) via `MedianPruner` to reduce wasted compute. |

---

### Step 13 — Model Evaluation

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Thoroughly evaluate each tuned model on the held-out test set across all metrics and market segments |
| **Script** | `ml/pipeline/13_evaluate_models.py` |
| **Inputs** | Tuned models (Step 12), test split (Step 9) |
| **Outputs** | `reports/evaluation/model_evaluation_{model}_{date}.json` per model; combined `reports/evaluation/all_metrics.csv` |
| **Tools** | `scikit-learn.metrics`, `scipy`, custom SMAPE/MAPE functions |
| **Metrics Computed** | |

```python
REGRESSION_METRICS = {
    "smape":        symmetric_mean_absolute_percentage_error,
    "mape":         mean_absolute_percentage_error,
    "mae":          mean_absolute_error,            # in original currency
    "rmse":         root_mean_squared_error,         # in original currency
    "r2":           r2_score,
    "log_rmse":     log-space RMSE,                  # scale-invariant
}

CLASSIFICATION_METRICS = {
    "accuracy":     accuracy_score,
    "f1_macro":     f1_score(average='macro'),
    "f1_weighted":  f1_score(average='weighted'),
    "confusion_matrix": confusion_matrix,
    "brier_score":  brier_score_loss,               # for calibration
}

# Segment-level evaluation (break down by):
SEGMENTS = ["bollywood", "hollywood", "south_indian", "low_budget", "high_budget",
            "franchise", "non_franchise", "pre_release_stage", "announcement_stage"]
```

| **Expected Duration** | 10–20 min |

---

### Step 14 — Model Comparison

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Side-by-side comparison of all candidate models to inform the selection decision |
| **Script** | `ml/pipeline/14_compare_models.py` |
| **Inputs** | Evaluation JSONs from Step 13 |
| **Outputs** | `reports/evaluation/model_comparison.csv` (all models × all metrics), `reports/evaluation/model_comparison.html` (formatted table) |
| **Tools** | `pandas`, `jinja2` (for HTML report) |
| **Comparison Table Columns** | model_name, smape_overall, smape_bollywood, smape_hollywood, smape_south_indian, mae_m_usd, r2, f1_macro, training_time_seconds, inference_time_ms, model_size_mb |
| **Expected Duration** | < 1 min |

---

### Step 15 — Model Selection

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Select the best model for each market segment (or one global model) based on comparison results, with documented justification |
| **Script** | `ml/pipeline/15_select_model.py` (or manual decision + script to record it) |
| **Inputs** | `model_comparison.csv` (Step 14) |
| **Outputs** | `ml/models/selected_model.txt` — contains model name, version, selection criteria, and date; `ml/models/selected_model_path.txt` — path to the model artifact |
| **Selection Criteria** | Primary: lowest SMAPE on test set overall. Tiebreaker: lowest SMAPE on largest market (Bollywood or Hollywood). Secondary consideration: inference time (< 500ms per prediction required). |
| **Expected Duration** | 5 min (human review recommended) |

```
# Example selected_model.txt content
Model: CatBoostRegressor
Version: catboost_global_all_stages_20241115_a3f9b2
Test SMAPE (overall): 31.4%
Test SMAPE (Bollywood): 28.9%
Test SMAPE (Hollywood): 33.1%
Test R²: 0.61
Test MAE: $18.2M equivalent
Selection date: 2024-11-15
Selected by: pipeline autoselect (lowest SMAPE)
Justification: CatBoost outperformed LightGBM by 2.1% SMAPE and XGBoost by 4.8% SMAPE,
  likely due to native categorical feature handling (genre, language, production_company).
  Inference time (45ms) is well within the 500ms requirement.
```

---

### Step 16 — SHAP Analysis

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Compute SHAP values for the selected model to enable explainable predictions and feature importance analysis |
| **Script** | `ml/pipeline/16_shap_analysis.py` |
| **Inputs** | Selected model artifact, training + test features |
| **Outputs** | `ml/artifacts/shap_explainer.pkl` (TreeExplainer object), `reports/shap/feature_importance_global.png`, `reports/shap/shap_summary_plot.png`, `ml/artifacts/shap_values_test.npy` |
| **Tools** | `shap` library |
| **Analysis Steps** | |

```python
import shap

# 1. Create TreeExplainer (fast for tree-based models)
explainer = shap.TreeExplainer(model)

# 2. Compute SHAP values on test set
shap_values = explainer.shap_values(X_test)

# 3. Global feature importance
shap.summary_plot(shap_values, X_test, plot_type="bar")

# 4. SHAP summary plot (beeswarm)
shap.summary_plot(shap_values, X_test)

# 5. Save explainer for inference-time use
import pickle
with open("ml/artifacts/shap_explainer.pkl", "wb") as f:
    pickle.dump(explainer, f)

# 6. Per-prediction SHAP: called at inference time for individual explanations
def explain_prediction(movie_features: pd.DataFrame) -> dict:
    shap_vals = explainer.shap_values(movie_features)
    return {
        "base_value": explainer.expected_value,
        "shap_values": dict(zip(movie_features.columns, shap_vals[0])),
    }
```

| **Expected Duration** | 10–30 min (SHAP is compute-intensive on large datasets) |
| **Note** | For inference, only compute SHAP on-demand per movie request. Do not pre-compute SHAP for all movies. |

---

### Step 17 — Uncertainty Calibration

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Generate calibrated prediction intervals (pessimistic, expected, optimistic) using conformal prediction |
| **Script** | `ml/pipeline/17_uncertainty_calibration.py` |
| **Inputs** | Selected model, calibration set (validation data not used in Optuna), predictions on calibration set |
| **Outputs** | `ml/artifacts/conformal_quantiles_{coverage}.pkl` — nonconformity score quantiles for 80%, 90%, 95% coverage levels |
| **Tools** | `MAPIE` library (Model Agnostic Prediction Interval Estimator) or manual conformal prediction |
| **Method** | Split conformal prediction (inductive conformal prediction): |

```python
from mapie.regression import MapieRegressor

# Fit MAPIE wrapper on calibration set
mapie = MapieRegressor(estimator=base_model, method="naive", cv="prefit")
mapie.fit(X_calib, y_calib)

# Predict with intervals
y_pred, y_intervals = mapie.predict(X_test, alpha=[0.1, 0.2])  # 90% and 80% coverage
```

| **Validation** | 90% interval must contain actual revenue ≥ 85% of time on test set |
| **Expected Duration** | 5–15 min |

---

### Step 18 — Model Serialization

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Save all model artifacts in a standard, versioned format ready for deployment |
| **Script** | `ml/pipeline/18_serialize_models.py` |
| **Inputs** | Trained models, SHAP explainer, conformal quantiles, feature metadata |
| **Outputs** | `ml/models/{version}/` directory containing all artifacts |
| **Tools** | CatBoost native `.save_model()`, `pickle`, `json`, `numpy.save` |
| **Artifact Manifest** | |

```
ml/models/{version}/
├── model_regression.cbm          # CatBoost regression model (revenue)
├── model_classification.cbm      # CatBoost classification model (success tier)
├── shap_explainer.pkl            # Pre-fitted TreeExplainer
├── conformal_quantiles.pkl       # Prediction interval quantiles
├── feature_metadata.json         # Feature list, encoders, expected dtypes
├── label_encoder.pkl             # For success tier labels
├── model_card.json               # Version, metrics, training date, dataset hash
└── preprocessing_pipeline.pkl   # sklearn Pipeline for feature transform
```

| **Expected Duration** | 1–2 min |

---

### Step 19 — MLflow Logging

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Log all experiment metadata, metrics, parameters, and artifacts to MLflow for reproducibility and lineage tracking |
| **Script** | `ml/pipeline/19_mlflow_log.py` |
| **Inputs** | Model artifacts (Step 18), evaluation metrics (Step 13), selected hyperparameters (Step 12) |
| **Outputs** | MLflow run recorded in local tracking server (`http://localhost:5000`) |
| **Tools** | `mlflow` |
| **What to Log** | |

```python
import mlflow
import mlflow.catboost

with mlflow.start_run(run_name=f"cinemetrics_{model_version}"):
    # Parameters
    mlflow.log_params(best_hyperparams)
    mlflow.log_param("train_cutoff_date", TRAIN_CUTOFF)
    mlflow.log_param("dataset_version_hash", dataset_hash)
    mlflow.log_param("feature_list_hash", feature_hash)
    mlflow.log_param("n_training_samples", len(X_train))
    mlflow.log_param("n_features", X_train.shape[1])

    # Metrics
    mlflow.log_metric("test_smape_overall", test_smape)
    mlflow.log_metric("test_smape_bollywood", test_smape_bollywood)
    mlflow.log_metric("test_smape_hollywood", test_smape_hollywood)
    mlflow.log_metric("test_mae_usd_m", test_mae)
    mlflow.log_metric("test_r2", test_r2)
    mlflow.log_metric("val_smape", val_smape)
    mlflow.log_metric("classification_f1_macro", f1_macro)

    # Artifacts
    mlflow.log_artifact("ml/models/{version}/model_card.json")
    mlflow.log_artifact("reports/shap/feature_importance_global.png")
    mlflow.log_artifact("reports/evaluation/model_comparison.csv")
    mlflow.catboost.log_model(cb_model, "catboost_model")

    # Tags
    mlflow.set_tag("selected_model", "True")
    mlflow.set_tag("model_type", "catboost")
    mlflow.set_tag("market", "global")
```

| **Expected Duration** | 2–5 min |

---

### Step 20 — Model Deployment

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Make the production model available to the FastAPI backend |
| **Script** | `ml/pipeline/20_deploy_model.py` |
| **Inputs** | Serialized model from Step 18 |
| **Outputs** | `ml/models/production/current/` — symlink or copy of latest production model directory; `ml/models/production/current_version.txt` |
| **Tools** | Python `os`, `shutil`, FastAPI server restart trigger |
| **Deployment Steps** | (1) Copy artifact directory to `ml/models/production/{version}/`; (2) Update `ml/models/production/current_version.txt`; (3) FastAPI startup code reads `current_version.txt` and loads model accordingly; (4) Health check endpoint `/health` verifies model is loaded |
| **Rollback** | Update `current_version.txt` to previous version string; restart backend |
| **Expected Duration** | 1–2 min |

> [!IMPORTANT]
> Never deploy a model with a test SMAPE worse than the currently deployed model without explicit human approval. The deployment script should include a gate that compares metrics and aborts if the new model performs worse.

---

## 2. MLflow Setup — Local Tracking Server

### Installation

```bash
pip install mlflow
# Or include in requirements.txt:
# mlflow>=2.9.0
```

### Starting the Tracking Server

```bash
# From project root
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri sqlite:///ml/mlflow/mlflow.db \
  --default-artifact-root ./ml/mlflow/artifacts

# Access UI at: http://localhost:5000
```

The `--backend-store-uri` stores experiment metadata in a local SQLite database. The `--default-artifact-root` stores model files and plots. Both directories are gitignored.

### Experiment Naming Convention

```python
# Format: cinemetrics_revenue_v{version}
# Examples:
experiment_names = [
    "cinemetrics_revenue_v1",          # First training run
    "cinemetrics_revenue_v2_catboost", # Specific model experiment
    "cinemetrics_classification_v1",   # Success tier classifier
    "cinemetrics_hyperparam_search",   # Optuna sweep runs
]

# In code:
mlflow.set_experiment(f"cinemetrics_revenue_v{VERSION}")
```

### Environment Variable for FastAPI

```bash
# In .env
MLFLOW_TRACKING_URI=http://localhost:5000
```

### MLflow Project Structure

```
ml/
└── mlflow/
    ├── mlflow.db          # SQLite backend (gitignored)
    └── artifacts/         # Model files, plots (gitignored)
        ├── {experiment_id}/
        │   └── {run_id}/
        │       ├── artifacts/
        │       └── metrics/
```

---

## 3. Optuna Hyperparameter Search Spaces

All search spaces are defined in `ml/config/hyperparameter_spaces.yaml` and loaded by `12_hyperparameter_tuning.py`.

### CatBoostRegressor Search Space

```python
def catboost_objective(trial: optuna.Trial, X_train, y_train, X_val, y_val, cat_features):
    params = {
        "iterations":        trial.suggest_int("iterations", 500, 3000),
        "depth":             trial.suggest_int("depth", 4, 10),
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "l2_leaf_reg":       trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
        "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 1.0),
        "random_strength":   trial.suggest_float("random_strength", 0.0, 10.0),
        "border_count":      trial.suggest_int("border_count", 32, 255),
        "cat_features":      cat_features,  # fixed, not tuned
        "loss_function":     "RMSE",
        "eval_metric":       "RMSE",
        "verbose":           0,
        "early_stopping_rounds": 50,
        "task_type":         "GPU" if GPU_AVAILABLE else "CPU",
    }

    model = CatBoostRegressor(**params)
    model.fit(X_train, y_train, eval_set=(X_val, y_val))

    preds = model.predict(X_val)
    smape = symmetric_mape(y_val, preds)

    # Optuna pruning (stops bad trials early)
    trial.report(smape, step=0)
    if trial.should_prune():
        raise optuna.TrialPruned()

    return smape
```

### LightGBM Search Space

```python
def lgbm_objective(trial: optuna.Trial, X_train, y_train, X_val, y_val):
    params = {
        "n_estimators":       trial.suggest_int("n_estimators", 500, 3000),
        "num_leaves":         trial.suggest_int("num_leaves", 31, 255),
        "learning_rate":      trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "feature_fraction":   trial.suggest_float("feature_fraction", 0.6, 1.0),
        "bagging_fraction":   trial.suggest_float("bagging_fraction", 0.6, 1.0),
        "bagging_freq":       trial.suggest_int("bagging_freq", 1, 7),
        "min_data_in_leaf":   trial.suggest_int("min_data_in_leaf", 10, 100),
        "lambda_l1":          trial.suggest_float("lambda_l1", 0.0, 10.0),
        "lambda_l2":          trial.suggest_float("lambda_l2", 0.0, 10.0),
        "max_depth":          trial.suggest_int("max_depth", -1, 15),
        "objective":          "regression",
        "metric":             "rmse",
        "verbosity":          -1,
    }

    callbacks = [lgb.early_stopping(50), lgb.log_evaluation(-1)]
    model = lgb.train(
        params,
        lgb.Dataset(X_train, label=y_train),
        valid_sets=[lgb.Dataset(X_val, label=y_val)],
        callbacks=callbacks,
    )

    preds = model.predict(X_val)
    return symmetric_mape(y_val, preds)
```

### XGBoost Search Space

```python
def xgb_objective(trial: optuna.Trial, X_train, y_train, X_val, y_val):
    params = {
        "n_estimators":       trial.suggest_int("n_estimators", 500, 3000),
        "max_depth":          trial.suggest_int("max_depth", 3, 10),
        "learning_rate":      trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample":          trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree":   trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "colsample_bylevel":  trial.suggest_float("colsample_bylevel", 0.6, 1.0),
        "reg_alpha":          trial.suggest_float("reg_alpha", 0.0, 5.0),
        "reg_lambda":         trial.suggest_float("reg_lambda", 0.0, 5.0),
        "min_child_weight":   trial.suggest_int("min_child_weight", 1, 20),
        "gamma":              trial.suggest_float("gamma", 0.0, 5.0),
        "tree_method":        "gpu_hist" if GPU_AVAILABLE else "hist",
        "eval_metric":        "rmse",
        "early_stopping_rounds": 50,
        "verbosity":          0,
    }

    model = XGBRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    preds = model.predict(X_val)
    return symmetric_mape(y_val, preds)
```

### Optuna Study Configuration

```python
study = optuna.create_study(
    study_name=f"cinemetrics_{model_type}_v{VERSION}",
    direction="minimize",         # minimize SMAPE
    storage=f"sqlite:///ml/artifacts/optuna_{model_type}.db",
    load_if_exists=True,          # Resume interrupted study
    pruner=optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=5),
    sampler=optuna.samplers.TPESampler(seed=42),
)

study.optimize(objective, n_trials=100, timeout=3600)  # 100 trials or 1h, whichever first

# Log best params
print(f"Best SMAPE: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")
```

---

## 4. Model Versioning Strategy

### Version String Format

```
{model_type}_{market}_{stage_coverage}_{date}_{hash}

Examples:
  catboost_global_all_stages_20241115_a3f9b2
  lgbm_bollywood_all_stages_20241115_c72f1a
  catboost_global_prerelease_20241201_d8e3b7
  xgboost_hollywood_all_stages_20241115_f19a44
```

**Components**:
- `model_type`: `catboost`, `lgbm`, `xgboost`
- `market`: `global` (all markets), `bollywood`, `hollywood`, `south_indian`
- `stage_coverage`: `all_stages`, `prerelease_only`, `announcement_only`
- `date`: `YYYYMMDD` of training run
- `hash`: first 6 characters of SHA256 of `{dataset_version_hash}+{feature_list_hash}+{hyperparams_hash}`

### Storage Layout

```
ml/
└── models/
    ├── candidates/                        # All trained candidate models
    │   ├── catboost_global_all_stages_20241115_a3f9b2/
    │   │   ├── model_regression.cbm
    │   │   ├── model_card.json
    │   │   └── ...
    │   └── lgbm_bollywood_all_stages_20241115_c72f1a/
    │       └── ...
    ├── production/                        # Active production models
    │   ├── current_version.txt           # "catboost_global_all_stages_20241115_a3f9b2"
    │   └── catboost_global_all_stages_20241115_a3f9b2/  # Symlink or copy
    └── retired/                           # Previously deployed models (kept for rollback)
        └── catboost_global_all_stages_20240901_b2c5d8/
```

### Model Card Format (`model_card.json`)

```json
{
  "version": "catboost_global_all_stages_20241115_a3f9b2",
  "model_type": "CatBoostRegressor",
  "market": "global",
  "stage_coverage": "all_stages",
  "training_date": "2024-11-15T14:32:00Z",
  "dataset_version_hash": "7f3a9c2d1e4b8f0a",
  "feature_list_hash": "2b9e4f1a7c3d6e8b",
  "hyperparams_hash": "c5a2b8f3d1e7a9c0",
  "n_training_samples": 14823,
  "n_features": 47,
  "train_cutoff_date": "2020-12-31",
  "metrics": {
    "test_smape_overall": 31.4,
    "test_smape_bollywood": 28.9,
    "test_smape_hollywood": 33.1,
    "test_mae_usd_m": 18.2,
    "test_r2": 0.61,
    "val_smape": 29.8,
    "classification_f1_macro": 0.63
  },
  "mlflow_run_id": "7f4e9a2c1b3d8e5f",
  "selected_for_production": true,
  "deployed_at": "2024-11-15T16:00:00Z",
  "retired_at": null
}
```

### Rollback Procedure

```bash
# Step 1: Identify the previous version
cat ml/models/production/current_version.txt
# Shows: catboost_global_all_stages_20241115_a3f9b2

# Step 2: Check retired models
ls ml/models/retired/

# Step 3: Update current version pointer
echo "catboost_global_all_stages_20240901_b2c5d8" > ml/models/production/current_version.txt

# Step 4: Restart backend
# (the backend reads current_version.txt on startup)
# If using uvicorn:
pkill uvicorn && uvicorn backend.main:app --reload

# Step 5: Verify health check
curl http://localhost:8000/health
# Expected: {"status": "ok", "model_version": "catboost_global_all_stages_20240901_b2c5d8"}
```

---

## 5. Retraining Policy

### Scheduled Retraining

| Trigger | Condition | Action |
|---------|-----------|--------|
| **Monthly check** | First Monday of each month | Run `ml/scripts/drift_check.py` on last 20 released movies |
| **Quarterly retrain** | Every 3 months if data has grown | Full pipeline retrain if ≥ 200 new labeled movies available |

### Event-Triggered Retraining

| Trigger | Condition | Action |
|---------|-----------|--------|
| **Performance degradation** | Rolling 3-month SMAPE on recently released movies > 1.5× baseline SMAPE | Trigger full retrain; alert developer |
| **New labeled data** | ≥ 50 new movies with final box-office data added since last training | Optional retrain (developer decides) |
| **Major market shift** | External: pandemic, streaming disruption, significant box-office structural change | Manual retrain with new data and potentially updated features |

### What Does NOT Trigger Retraining

- Metadata updates (poster changes, description edits)
- Popularity score fluctuations on TMDB
- Discovery of new upcoming movies (ingestion only)
- Minor prediction errors on individual movies (expected statistical variation)
- Changes to the UI or backend that don't affect model inputs

### Human Review Gate

> [!IMPORTANT]
> **No automatic deployment to production.** Every retraining run produces a candidate model. A developer (or team member) must review the model card, compare metrics to the current production model, and explicitly run `python ml/pipeline/20_deploy_model.py --approve` to deploy. Automatic retraining and deployment without human review is prohibited.

```python
# deploy_model.py gate
def deployment_gate(new_metrics: dict, current_metrics: dict) -> bool:
    """Returns True if new model is safe to deploy."""
    if new_metrics["test_smape_overall"] > current_metrics["test_smape_overall"] * 1.05:
        print("❌ GATE FAILED: New model SMAPE is >5% worse than current production.")
        return False
    if new_metrics["test_r2"] < 0.25:
        print("❌ GATE FAILED: R² below minimum acceptable threshold (0.25).")
        return False
    print("✅ GATE PASSED: New model meets deployment criteria.")
    return True
```

---

## 6. Model Drift Detection

### Types of Drift to Monitor

| Drift Type | Description | Detection Method |
|------------|-------------|-----------------|
| **Concept drift** | The relationship between features and revenue changes (e.g., pandemic changes box-office dynamics) | Performance degradation on recent data |
| **Data drift** | Input feature distributions shift (e.g., typical production budgets inflate over years) | Statistical tests (KS test, PSI) on feature distributions |
| **Performance drift** | Model accuracy degrades on recently released movies | Rolling SMAPE on last N movies |
| **Label distribution drift** | Distribution of success categories shifts (more blockbusters or fewer) | Chi-square test on success category distribution |

### Drift Detection Implementation

```python
# ml/scripts/drift_check.py
import pandas as pd
from scipy.stats import ks_2samp
import numpy as np

def compute_rolling_smape(predictions_df: pd.DataFrame, n_recent: int = 20) -> float:
    """
    Compute SMAPE on the N most recently released movies
    where actual box office is now known.
    
    Args:
        predictions_df: DataFrame with columns: movie_id, predicted_revenue, 
                        actual_revenue, release_date, model_version
        n_recent: Number of recent movies to evaluate
    """
    recent = predictions_df.sort_values("release_date").tail(n_recent)
    actual = recent["actual_revenue"].values
    predicted = recent["predicted_revenue"].values
    smape = 100 * np.mean(2 * np.abs(predicted - actual) / (np.abs(actual) + np.abs(predicted)))
    return smape

def detect_feature_drift(train_features: pd.DataFrame,
                          recent_features: pd.DataFrame,
                          threshold_p: float = 0.05) -> dict:
    """
    KS test for distribution shift in numeric features.
    Returns dict of {feature_name: p_value} for features with significant drift.
    """
    drifted = {}
    for col in train_features.select_dtypes(include=[np.number]).columns:
        stat, p_value = ks_2samp(train_features[col].dropna(), recent_features[col].dropna())
        if p_value < threshold_p:
            drifted[col] = p_value
    return drifted

# Alerting threshold
BASELINE_SMAPE = 31.4  # from production model card
DRIFT_THRESHOLD = BASELINE_SMAPE * 1.5  # 47.1% would trigger alert

rolling_smape = compute_rolling_smape(predictions_df, n_recent=20)
if rolling_smape > DRIFT_THRESHOLD:
    send_alert(f"⚠️ Model drift detected! Rolling SMAPE: {rolling_smape:.1f}% (threshold: {DRIFT_THRESHOLD:.1f}%)")
```

### Drift Monitoring Tools

- **Primary (simple)**: Custom rolling SMAPE script run monthly — no extra dependencies
- **Advanced (optional)**: [Evidently AI](https://www.evidentlyai.com/) — open-source ML monitoring library

```bash
pip install evidently

# Generate drift report
python ml/scripts/generate_evidently_report.py \
  --reference-data data/splits/X_train.parquet \
  --current-data data/live/recent_predictions.parquet \
  --output reports/drift/drift_report_{date}.html
```

The Evidently report produces an interactive HTML file showing feature drift, target drift, and data quality metrics.

---

## 7. Dataset Versioning

### Strategy: Hash-Based Manual Versioning

Since this is a student project without DVC infrastructure, we use a lightweight hash-based approach. For larger-scale deployments, DVC is the recommended upgrade path.

```python
# ml/utils/dataset_versioning.py
import hashlib
import json
from pathlib import Path
import pandas as pd

def compute_dataframe_hash(df: pd.DataFrame) -> str:
    """Compute a stable hash of a DataFrame's content."""
    return hashlib.sha256(
        pd.util.hash_pandas_object(df, index=True).values.tobytes()
    ).hexdigest()[:16]

def compute_feature_list_hash(feature_names: list[str]) -> str:
    """Hash the ordered list of feature names."""
    return hashlib.sha256(
        json.dumps(sorted(feature_names)).encode()
    ).hexdigest()[:16]

def create_version_manifest(
    datasets: dict[str, pd.DataFrame],
    feature_names: list[str],
    train_cutoff_date: str,
) -> dict:
    """Create a full version manifest for a training run."""
    manifest = {
        "created_at": pd.Timestamp.now().isoformat(),
        "train_cutoff_date": train_cutoff_date,
        "feature_list_hash": compute_feature_list_hash(feature_names),
        "n_features": len(feature_names),
        "datasets": {},
    }
    for name, df in datasets.items():
        manifest["datasets"][name] = {
            "hash": compute_dataframe_hash(df),
            "n_rows": len(df),
            "n_cols": len(df.columns),
        }
    
    # Combined version hash
    combined = "_".join(v["hash"] for v in manifest["datasets"].values())
    manifest["dataset_version_hash"] = hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    return manifest
```

### Version Manifest Storage

Every training run writes its version manifest to:
```
ml/artifacts/version_manifests/
└── {dataset_version_hash}_{date}.json
```

This manifest is stored in git (it contains only hashes and metadata, not the actual data). To reproduce any past model, the developer:
1. Looks up the `dataset_version_hash` in the model card
2. Finds the corresponding manifest JSON
3. Re-downloads or restores the raw data files with matching hashes
4. Re-runs the pipeline with the same `train_cutoff_date`

### DVC (Optional Upgrade)

For teams wanting full reproducibility with large data files:

```bash
pip install dvc

# Initialize DVC in repo
dvc init

# Track large data files
dvc add data/raw/
dvc add data/processed/

# Push to remote (e.g., Google Drive — free)
dvc remote add -d gdrive gdrive://your-gdrive-folder-id
dvc push

# Pull data on another machine
dvc pull
```

DVC stores `.dvc` pointer files in git (small, text files) while the actual data lives in the configured remote storage.

---

## 8. Pipeline Orchestration

### End-to-End Execution

```bash
# Run full pipeline
python ml/pipeline/run_pipeline.py

# Run from a specific step (e.g., restart from feature engineering)
python ml/pipeline/run_pipeline.py --from-step 7

# Run only specific steps
python ml/pipeline/run_pipeline.py --steps 11,12,13,14,15

# Dry run (validate config, check inputs exist, don't execute)
python ml/pipeline/run_pipeline.py --dry-run
```

### `run_pipeline.py` Structure

```python
# ml/pipeline/run_pipeline.py
import subprocess
import sys
import logging
from pathlib import Path

STEPS = {
    1:  ("01_acquire_data.py",        "Dataset Acquisition"),
    2:  ("02_store_raw.py",           "Raw Data Storage"),
    3:  ("03_validate_raw.py",        "Data Validation"),
    4:  ("04_entity_resolution.py",   "Entity Resolution"),
    5:  ("05_integrate_datasets.py",  "Dataset Integration"),
    6:  ("06_create_snapshots.py",    "Historical Snapshot Creation"),
    7:  ("07_feature_engineering.py", "Feature Engineering"),
    8:  ("08_eda.py",                 "EDA and Feature Analysis"),
    9:  ("09_temporal_split.py",      "Temporal Split Creation"),
    10: ("10_baseline_model.py",      "Baseline Model Training"),
    11: ("11_train_models.py",        "Advanced Model Training"),
    12: ("12_hyperparameter_tuning.py", "Hyperparameter Optimization"),
    13: ("13_evaluate_models.py",     "Model Evaluation"),
    14: ("14_compare_models.py",      "Model Comparison"),
    15: ("15_select_model.py",        "Model Selection"),
    16: ("16_shap_analysis.py",       "SHAP Analysis"),
    17: ("17_uncertainty_calibration.py", "Uncertainty Calibration"),
    18: ("18_serialize_models.py",    "Model Serialization"),
    19: ("19_mlflow_log.py",          "MLflow Logging"),
    20: ("20_deploy_model.py",        "Model Deployment"),
}

def run_step(step_num: int, script_name: str, description: str):
    logger.info(f"▶ Step {step_num:02d}/{len(STEPS)}: {description}")
    result = subprocess.run(
        [sys.executable, f"ml/pipeline/{script_name}"],
        capture_output=False,  # Let output stream to console
    )
    if result.returncode != 0:
        logger.error(f"❌ Step {step_num} FAILED: {description}")
        sys.exit(1)
    logger.info(f"✅ Step {step_num:02d} COMPLETE: {description}")
```

---

## 9. Directory and File Structure

```
ml/
├── pipeline/                   # Training pipeline scripts (Steps 1–20)
│   ├── 01_acquire_data.py
│   ├── 02_store_raw.py
│   ├── ...
│   ├── 20_deploy_model.py
│   └── run_pipeline.py         # Orchestrator
├── scripts/                    # Utility and monitoring scripts
│   ├── drift_check.py
│   ├── generate_evidently_report.py
│   └── backfill_predictions.py
├── config/                     # Configuration files (tracked in git)
│   ├── sources.yaml
│   ├── prediction_stages.yaml
│   ├── hyperparameter_spaces.yaml
│   └── feature_definitions.yaml
├── models/                     # Model artifacts (gitignored)
│   ├── candidates/
│   ├── production/
│   └── retired/
├── artifacts/                  # Training artifacts (gitignored except manifests)
│   ├── version_manifests/      # ← tracked in git
│   ├── shap_explainer.pkl
│   ├── conformal_quantiles.pkl
│   ├── feature_metadata.json
│   └── optuna_*.db
├── mlflow/                     # MLflow storage (gitignored)
│   ├── mlflow.db
│   └── artifacts/
└── utils/                      # Shared utility functions
    ├── dataset_versioning.py
    ├── metrics.py              # Custom SMAPE, MAPE implementations
    ├── feature_utils.py
    └── logging_config.py
```

---

## 10. Environment and Dependencies

### Python Dependencies (`requirements-ml.txt`)

```
# Core ML
catboost>=1.2.0
lightgbm>=4.1.0
xgboost>=2.0.0
scikit-learn>=1.3.0
optuna>=3.4.0
shap>=0.43.0
mapie>=0.7.0

# Data processing
pandas>=2.1.0
numpy>=1.26.0
pyarrow>=14.0.0
pandera>=0.17.0
rapidfuzz>=3.5.0
recordlinkage>=0.15

# MLflow
mlflow>=2.9.0

# Validation and profiling
ydata-profiling>=4.6.0
evidently>=0.4.0

# Utilities
pydantic>=2.4.0
pyyaml>=6.0.1
python-dotenv>=1.0.0
structlog>=23.2.0
tqdm>=4.66.0
```

### Hardware Recommendations

| Configuration | Training Time (Step 11–12) | Suitable For |
|---------------|---------------------------|--------------|
| CPU only (4 cores, 8 GB RAM) | 3–8 hours | Development, testing |
| CPU (8 cores, 16 GB RAM) | 1.5–4 hours | Standard student laptop |
| GPU (RTX 3060 or better) | 30–90 min | Recommended for full Optuna sweep |
| Google Colab (free GPU) | 1–3 hours | Free cloud option |

> [!TIP]
> For student development, use `n_trials=20` for Optuna and `iterations=500` max for initial CatBoost runs to get results in under 1 hour on a standard laptop. Increase once the pipeline is verified end-to-end.

---

*This MLOps document defines the complete training workflow for CineMetrics. Every step must be implemented as an independent, logged, and validatable Python script before the full pipeline is wired together.*
