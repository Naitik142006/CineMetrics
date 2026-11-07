"""
CineMetrics — Production CatBoost Revenue Forecasting Engine
Trains gradient-boosted decision trees with Ordered Target Statistics, Optuna tuning, and Conformal Uncertainty.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from catboost import CatBoostRegressor, Pool
import joblib
import numpy as np
import optuna
import pandas as pd

from ml.dataset_engineering.config import BASE_DIR, SNAPSHOTS_DATA_DIR
from ml.training.metrics import evaluate_predictions
from ml.training.uncertainty import ConformalCalibrator

# Suppress Optuna verbose logs
optuna.logging.set_verbosity(optuna.logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TrainCatBoost")

PRODUCTION_MODELS_DIR = BASE_DIR / "ml" / "models" / "production"
PRODUCTION_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Feature definitions for CatBoost
NUM_COLS = [
    "log_budget",
    "runtime_minutes_clean",
    "genre_count",
    "is_sequel_or_franchise",
    "is_summer_season",
    "is_holiday_season",
    "is_weekend_release",
    "release_month",
    "release_quarter",
    "director_prior_movies",
    "director_prior_avg_real_gross",
    "director_prior_avg_roi",
    "director_prior_hit_rate",
    "lead_actor_prior_movies",
    "lead_actor_prior_avg_real_gross",
    "lead_actor_prior_avg_roi",
    "lead_actor_prior_hit_rate",
    "studio_prior_movies",
]

CAT_COLS = [
    "budget_tier",
    "primary_genre",
    "industry",
    "language_clean",
    "director",
    "lead_actor",
]

ALL_MODEL_COLS = NUM_COLS + CAT_COLS


def prepare_catboost_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepares feature matrix for CatBoost: ensures categoricals are strings with no NaNs."""
    df_clean = df[ALL_MODEL_COLS].copy()
    for col in CAT_COLS:
        df_clean[col] = df_clean[col].fillna("Unknown").astype(str)
    for col in NUM_COLS:
        df_clean[col] = df_clean[col].fillna(0.0).astype(float)
    return df_clean


def optimize_hyperparameters(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
    n_trials: int = 20,
) -> Dict:
    """Uses Optuna Bayesian optimization to find optimal CatBoost hyperparameters."""
    logger.info(f"Starting Optuna hyperparameter optimization ({n_trials} trials)...")

    train_pool = Pool(X_train, y_train, cat_features=CAT_COLS)
    val_pool = Pool(X_val, y_val, cat_features=CAT_COLS)

    def objective(trial):
        params = {
            "iterations": 500,
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
            "depth": trial.suggest_int("depth", 4, 8),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 15.0),
            "random_strength": trial.suggest_float("random_strength", 0.0, 2.0),
            "loss_function": "RMSE",
            "eval_metric": "RMSE",
            "random_seed": 42,
            "verbose": False,
        }
        model = CatBoostRegressor(**params)
        model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=30, verbose=False)
        val_preds = model.predict(X_val)
        return float(np.sqrt(np.mean((y_val - val_preds) ** 2)))

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials)

    best_params = study.best_params
    logger.info(f"Optuna Best Trial (RMSE={study.best_value:.4f}): {best_params}")
    return best_params


def train_production_catboost() -> Dict:
    """
    Trains, calibrates, evaluates, and exports the production CatBoost revenue model.
    """
    train_path = SNAPSHOTS_DATA_DIR / "train_v1.parquet"
    val_path = SNAPSHOTS_DATA_DIR / "val_v1.parquet"
    test_path = SNAPSHOTS_DATA_DIR / "test_v1.parquet"

    logger.info("Loading Gold snapshots for CatBoost training...")
    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    test_df = pd.read_parquet(test_path)

    X_train = prepare_catboost_data(train_df)
    y_train = train_df["target_revenue_log10"].values
    y_train_real = train_df["target_revenue_raw"].values

    X_val = prepare_catboost_data(val_df)
    y_val = val_df["target_revenue_log10"].values
    y_val_real = val_df["target_revenue_raw"].values

    X_test = prepare_catboost_data(test_df)
    y_test = test_df["target_revenue_log10"].values
    y_test_real = test_df["target_revenue_raw"].values

    # 1. Hyperparameter Optimization
    best_params = optimize_hyperparameters(X_train, y_train, X_val, y_val, n_trials=20)

    # 2. Train Production Model with Early Stopping on Validation Set
    logger.info("Training production CatBoost Regressor with optimal parameters...")
    train_pool = Pool(X_train, y_train, cat_features=CAT_COLS)
    val_pool = Pool(X_val, y_val, cat_features=CAT_COLS)

    prod_params = {
        "iterations": 1000,
        "learning_rate": best_params.get("learning_rate", 0.05),
        "depth": best_params.get("depth", 6),
        "l2_leaf_reg": best_params.get("l2_leaf_reg", 5.0),
        "random_strength": best_params.get("random_strength", 1.0),
        "loss_function": "RMSE",
        "eval_metric": "RMSE",
        "random_seed": 42,
        "verbose": 100,
    }

    model = CatBoostRegressor(**prod_params)
    model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=50, verbose=100)

    # 3. Validation and Test Predictions
    pred_val_log = model.predict(X_val)
    pred_test_log = model.predict(X_test)

    val_metrics = evaluate_predictions(y_val, pred_val_log, y_val_real)
    test_metrics = evaluate_predictions(y_test, pred_test_log, y_test_real)

    logger.info(f"CatBoost Test Results: RMSE={test_metrics['rmse_log']:.4f} | R2={test_metrics['r2_log']:.4f} | SMAPE={test_metrics['smape_pct']:.2f}%")

    # 4. Calibrate Conformal Prediction Intervals
    logger.info("Calibrating Conformal Prediction uncertainty intervals...")
    calibrator = ConformalCalibrator(alpha_levels=[0.20, 0.05])
    calibrator.calibrate(y_val, pred_val_log)
    coverage_results = calibrator.evaluate_coverage(y_test, pred_test_log)
    logger.info(f"Conformal Empirical Test Coverage: {coverage_results}")

    # 5. Extract Feature Importance
    importances = model.get_feature_importance(train_pool)
    feat_imp = sorted(zip(ALL_MODEL_COLS, importances), key=lambda x: x[1], reverse=True)
    top_features = [{"feature": f, "importance": round(float(imp), 2)} for f, imp in feat_imp[:10]]

    # 6. Save Model Artifacts
    model_cbm_path = PRODUCTION_MODELS_DIR / "catboost_revenue_v1.cbm"
    calibrator_path = PRODUCTION_MODELS_DIR / "conformal_calibrator_v1.joblib"
    metadata_path = PRODUCTION_MODELS_DIR / "catboost_metadata_v1.json"

    model.save_model(str(model_cbm_path))
    joblib.dump(calibrator, calibrator_path)

    meta = {
        "model_name": "CatBoostRegressor (Production)",
        "version": "v1.0",
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "optimal_hyperparameters": best_params,
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
        "conformal_coverage": coverage_results,
        "top_features": top_features,
        "categorical_features": CAT_COLS,
        "numerical_features": NUM_COLS,
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"Saved production artifacts to {PRODUCTION_MODELS_DIR}.")
    return meta


if __name__ == "__main__":
    train_production_catboost()

