"""
CineMetrics — Production LightGBM Revenue Forecasting Engine
Trains fast histogram gradient boosted decision trees for multi-model ensemble validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List
import lightgbm as lgb
import numpy as np
import pandas as pd

from ml.dataset_engineering.config import BASE_DIR, SNAPSHOTS_DATA_DIR
from ml.training.metrics import evaluate_predictions

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TrainLightGBM")

PRODUCTION_MODELS_DIR = BASE_DIR / "ml" / "models" / "production"
PRODUCTION_MODELS_DIR.mkdir(parents=True, exist_ok=True)

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


def prepare_lgb_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepares feature matrix for LightGBM with explicit category dtypes."""
    df_clean = df[ALL_MODEL_COLS].copy()
    for col in CAT_COLS:
        df_clean[col] = df_clean[col].fillna("Unknown").astype("category")
    for col in NUM_COLS:
        df_clean[col] = df_clean[col].fillna(0.0).astype(float)
    return df_clean


def train_production_lightgbm() -> Dict:
    """Trains, evaluates, and exports the production LightGBM revenue model."""
    train_path = SNAPSHOTS_DATA_DIR / "train_v1.parquet"
    val_path = SNAPSHOTS_DATA_DIR / "val_v1.parquet"
    test_path = SNAPSHOTS_DATA_DIR / "test_v1.parquet"

    logger.info("Loading Gold snapshots for LightGBM training...")
    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    test_df = pd.read_parquet(test_path)

    X_train = prepare_lgb_data(train_df)
    y_train = train_df["target_revenue_log10"].values

    X_val = prepare_lgb_data(val_df)
    y_val = val_df["target_revenue_log10"].values
    y_val_real = val_df["target_revenue_raw"].values

    X_test = prepare_lgb_data(test_df)
    y_test = test_df["target_revenue_log10"].values
    y_test_real = test_df["target_revenue_raw"].values

    logger.info("Training LightGBM Regressor with early stopping...")
    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=CAT_COLS)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data, categorical_feature=CAT_COLS)

    params = {
        "objective": "regression",
        "metric": "rmse",
        "boosting_type": "gbdt",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": 6,
        "min_child_samples": 20,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 1.0,
        "reg_lambda": 5.0,
        "random_state": 42,
        "verbose": -1,
    }

    callbacks = [lgb.early_stopping(stopping_rounds=50, verbose=False)]
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[val_data],
        callbacks=callbacks,
    )

    pred_val_log = model.predict(X_val)
    pred_test_log = model.predict(X_test)

    val_metrics = evaluate_predictions(y_val, pred_val_log, y_val_real)
    test_metrics = evaluate_predictions(y_test, pred_test_log, y_test_real)

    logger.info(f"LightGBM Test Results: RMSE={test_metrics['rmse_log']:.4f} | R2={test_metrics['r2_log']:.4f} | SMAPE={test_metrics['smape_pct']:.2f}%")

    # Save model artifact
    model_txt_path = PRODUCTION_MODELS_DIR / "lightgbm_revenue_v1.txt"
    metadata_path = PRODUCTION_MODELS_DIR / "lightgbm_metadata_v1.json"
    model.save_model(str(model_txt_path))

    meta = {
        "model_name": "LightGBMRegressor (Production)",
        "version": "v1.0",
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"Saved LightGBM model to {model_txt_path}.")
    return meta


if __name__ == "__main__":
    train_production_lightgbm()

