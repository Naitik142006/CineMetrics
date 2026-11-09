"""
CineMetrics — Production Multi-Model Stacking Ensemble Engine
Combines CatBoost, LightGBM, and XGBoost with a Convex Meta-Optimization
and Conformal Uncertainty Calibration to achieve state-of-the-art predictive accuracy.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
import lightgbm as lgb
import xgboost as xgb
import scipy.optimize as opt

from ml.dataset_engineering.config import BASE_DIR, SNAPSHOTS_DATA_DIR
from ml.training.metrics import evaluate_predictions
from ml.training.uncertainty import ConformalCalibrator
from ml.training.train_catboost import (
    NUM_COLS,
    CAT_COLS,
    ALL_MODEL_COLS,
    prepare_catboost_data,
    PRODUCTION_MODELS_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TrainStackedEnsemble")


def prepare_lgb_and_xgb_data(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, pd.CategoricalDtype]]:
    """
    Prepares feature matrices for LightGBM and XGBoost with unified category encodings
    so that unseen validation/test categories are mapped to 'Unknown' safely.
    """
    tr_clean = train_df[ALL_MODEL_COLS].copy()
    va_clean = val_df[ALL_MODEL_COLS].copy()
    te_clean = test_df[ALL_MODEL_COLS].copy()

    for col in NUM_COLS:
        tr_clean[col] = tr_clean[col].fillna(0.0).astype(float)
        va_clean[col] = va_clean[col].fillna(0.0).astype(float)
        te_clean[col] = te_clean[col].fillna(0.0).astype(float)

    cat_types = {}
    for col in CAT_COLS:
        tr_clean[col] = tr_clean[col].fillna("Unknown").astype(str)
        va_clean[col] = va_clean[col].fillna("Unknown").astype(str)
        te_clean[col] = te_clean[col].fillna("Unknown").astype(str)

        train_vocab = set(tr_clean[col].unique()) | {"Unknown"}
        sorted_vocab = sorted(list(train_vocab))
        cat_type = pd.CategoricalDtype(categories=sorted_vocab, ordered=False)
        cat_types[col] = cat_type

        tr_clean[col] = tr_clean[col].astype(cat_type)
        va_clean[col] = va_clean[col].apply(lambda x: x if x in train_vocab else "Unknown").astype(cat_type)
        te_clean[col] = te_clean[col].apply(lambda x: x if x in train_vocab else "Unknown").astype(cat_type)

    return tr_clean, va_clean, te_clean, cat_types


def train_production_xgboost(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
) -> xgb.XGBRegressor:
    """Trains a production XGBoost Regressor with native categorical support."""
    logger.info("Training production XGBoost Regressor with enable_categorical=True...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=700,
        learning_rate=0.038,
        max_depth=6,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=1.5,
        reg_lambda=3.0,
        enable_categorical=True,
        random_state=42,
        early_stopping_rounds=40,
        tree_method="hist",
    )
    xgb_model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    return xgb_model


def train_production_lightgbm(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
) -> lgb.Booster:
    """Trains an optimized production LightGBM Regressor with early stopping."""
    logger.info("Training production LightGBM Regressor with histogram binning...")
    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=CAT_COLS)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data, categorical_feature=CAT_COLS)

    params = {
        "objective": "regression",
        "metric": "rmse",
        "boosting_type": "gbdt",
        "learning_rate": 0.045,
        "num_leaves": 35,
        "max_depth": 7,
        "min_child_samples": 25,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "reg_alpha": 1.2,
        "reg_lambda": 4.0,
        "random_state": 42,
        "verbose": -1,
    }

    callbacks = [lgb.early_stopping(stopping_rounds=40, verbose=False)]
    lgb_model = lgb.train(
        params,
        train_data,
        num_boost_round=800,
        valid_sets=[val_data],
        callbacks=callbacks,
    )
    return lgb_model


def fit_convex_meta_weights(val_preds_matrix: np.ndarray, y_val: np.ndarray) -> np.ndarray:
    """
    Finds convex combination weights w >= 0, sum(w) = 1.0 minimizing validation RMSE.
    val_preds_matrix: shape (N, 3) [pred_cat, pred_lgb, pred_xgb]
    """
    def objective(w):
        pred = np.dot(val_preds_matrix, w)
        return float(np.mean((y_val - pred) ** 2))

    init_w = np.array([0.334, 0.333, 0.333])
    bounds = [(0.0, 1.0)] * 3
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}

    res = opt.minimize(objective, init_w, bounds=bounds, constraints=constraints)
    weights = res.x / np.sum(res.x)

    logger.info(
        f"Optimal Convex Meta-Weights: CatBoost={weights[0]:.3f}, "
        f"LightGBM={weights[1]:.3f}, XGBoost={weights[2]:.3f}"
    )
    return weights


def main():
    logger.info("=================================================================")
    logger.info(" CineMetrics — Training Production 3-Way Stacking Ensemble")
    logger.info("=================================================================")

    # 1. Load Snapshots
    train_path = SNAPSHOTS_DATA_DIR / "train_v1.parquet"
    val_path = SNAPSHOTS_DATA_DIR / "val_v1.parquet"
    test_path = SNAPSHOTS_DATA_DIR / "test_v1.parquet"

    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    test_df = pd.read_parquet(test_path)

    logger.info(f"Loaded Gold datasets: Train={len(train_df):,} | Val={len(val_df):,} | Test={len(test_df):,}")

    y_train = train_df["target_revenue_log10"].values
    y_val = val_df["target_revenue_log10"].values
    y_val_real = val_df["target_revenue_raw"].values
    y_test = test_df["target_revenue_log10"].values
    y_test_real = test_df["target_revenue_raw"].values

    # 2. Prepare Data Representations
    X_train_cat = prepare_catboost_data(train_df)
    X_val_cat = prepare_catboost_data(val_df)
    X_test_cat = prepare_catboost_data(test_df)

    X_train_lgb, X_val_lgb, X_test_lgb, cat_types = prepare_lgb_and_xgb_data(train_df, val_df, test_df)

    # 3. Load Production CatBoost
    cat_model_path = PRODUCTION_MODELS_DIR / "catboost_revenue_v1.cbm"
    logger.info(f"Loading production CatBoost model from {cat_model_path}...")
    cat_model = CatBoostRegressor()
    cat_model.load_model(str(cat_model_path))

    pred_val_cat = cat_model.predict(X_val_cat)
    pred_test_cat = cat_model.predict(X_test_cat)

    cat_test_eval = evaluate_predictions(y_test, pred_test_cat, y_test_real)
    logger.info(
        f"Model 1 (CatBoost) Test:  RMSE={cat_test_eval['rmse_log']:.4f} | "
        f"R²={cat_test_eval['r2_log']:.4f} | SMAPE={cat_test_eval['smape_pct']:.2f}%"
    )

    # 4. Train LightGBM
    lgb_model = train_production_lightgbm(X_train_lgb, y_train, X_val_lgb, y_val)
    pred_val_lgb = lgb_model.predict(X_val_lgb)
    pred_test_lgb = lgb_model.predict(X_test_lgb)

    lgb_test_eval = evaluate_predictions(y_test, pred_test_lgb, y_test_real)
    logger.info(
        f"Model 2 (LightGBM) Test:  RMSE={lgb_test_eval['rmse_log']:.4f} | "
        f"R²={lgb_test_eval['r2_log']:.4f} | SMAPE={lgb_test_eval['smape_pct']:.2f}%"
    )

    # 5. Train XGBoost
    xgb_model = train_production_xgboost(X_train_lgb, y_train, X_val_lgb, y_val)
    pred_val_xgb = xgb_model.predict(X_val_lgb)
    pred_test_xgb = xgb_model.predict(X_test_lgb)

    xgb_test_eval = evaluate_predictions(y_test, pred_test_xgb, y_test_real)
    logger.info(
        f"Model 3 (XGBoost) Test:   RMSE={xgb_test_eval['rmse_log']:.4f} | "
        f"R²={xgb_test_eval['r2_log']:.4f} | SMAPE={xgb_test_eval['smape_pct']:.2f}%"
    )

    # 6. Fit Convex Meta-Weights on Validation Predictions
    val_preds_mat = np.column_stack([pred_val_cat, pred_val_lgb, pred_val_xgb])
    test_preds_mat = np.column_stack([pred_test_cat, pred_test_lgb, pred_test_xgb])

    weights = fit_convex_meta_weights(val_preds_mat, y_val)

    # Compute Stacked Predictions
    pred_val_stacked = np.dot(val_preds_mat, weights)
    pred_test_stacked = np.dot(test_preds_mat, weights)

    stacked_val_eval = evaluate_predictions(y_val, pred_val_stacked, y_val_real)
    stacked_test_eval = evaluate_predictions(y_test, pred_test_stacked, y_test_real)

    logger.info("=================================================================")
    logger.info(" PRODUCTION TEST BENCHMARK COMPARISON:")
    logger.info("=================================================================")
    logger.info(f" CatBoost Solo:         RMSE={cat_test_eval['rmse_log']:.4f} | R²={cat_test_eval['r2_log']:.4f} | SMAPE={cat_test_eval['smape_pct']:.2f}%")
    logger.info(f" LightGBM Solo:         RMSE={lgb_test_eval['rmse_log']:.4f} | R²={lgb_test_eval['r2_log']:.4f} | SMAPE={lgb_test_eval['smape_pct']:.2f}%")
    logger.info(f" XGBoost Solo:          RMSE={xgb_test_eval['rmse_log']:.4f} | R²={xgb_test_eval['r2_log']:.4f} | SMAPE={xgb_test_eval['smape_pct']:.2f}%")
    logger.info(f" 🔥 STACKED ENSEMBLE:   RMSE={stacked_test_eval['rmse_log']:.4f} | R²={stacked_test_eval['r2_log']:.4f} | SMAPE={stacked_test_eval['smape_pct']:.2f}%")
    logger.info("=================================================================")

    # 7. Fit Conformal Calibrator for Stacked Ensemble
    logger.info("Calibrating Conformal Uncertainty on Stacked Validation residuals...")
    calibrator = ConformalCalibrator()
    calibrator.calibrate(y_val, pred_val_stacked)
    coverage_dict = calibrator.evaluate_coverage(y_test, pred_test_stacked)
    logger.info(f"Stacked Conformal Test Coverage: {coverage_dict}")

    # 8. Export Production Models & Metadata
    lgb_path = PRODUCTION_MODELS_DIR / "lightgbm_revenue_v1.txt"
    xgb_path = PRODUCTION_MODELS_DIR / "xgboost_revenue_v1.json"
    stacker_path = PRODUCTION_MODELS_DIR / "ensemble_stacker_v1.joblib"
    calibrator_path = PRODUCTION_MODELS_DIR / "ensemble_conformal_calibrator_v1.joblib"
    meta_path = PRODUCTION_MODELS_DIR / "ensemble_metadata_v1.json"

    lgb_model.save_model(str(lgb_path))
    xgb_model.save_model(str(xgb_path))

    cat_vocab_dict = {col: list(cat_types[col].categories) for col in CAT_COLS}

    stacker_payload = {
        "weights": weights.tolist(),
        "feature_names": ALL_MODEL_COLS,
        "num_cols": NUM_COLS,
        "cat_cols": CAT_COLS,
        "cat_vocabularies": cat_vocab_dict,
    }
    joblib.dump(stacker_payload, stacker_path)
    joblib.dump(calibrator, calibrator_path)

    metadata = {
        "model_name": "CineMetrics 3-Way Stacking Ensemble (Production)",
        "version": "v1.0-stacked",
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "meta_weights": {
            "catboost": float(weights[0]),
            "lightgbm": float(weights[1]),
            "xgboost": float(weights[2]),
        },
        "test_benchmarks": {
            "catboost": cat_test_eval,
            "lightgbm": lgb_test_eval,
            "xgboost": xgb_test_eval,
            "stacked_ensemble": stacked_test_eval,
        },
        "conformal_test_coverage": coverage_dict,
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Successfully saved all Stacking Ensemble artifacts to {PRODUCTION_MODELS_DIR}!")


if __name__ == "__main__":
    main()
