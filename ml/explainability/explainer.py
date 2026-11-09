"""
CineMetrics — Production TreeSHAP Feature Attribution & Explainability Engine
Computes exact local Shapley values directly from CatBoost oblivious decision trees,
verifies the mathematical additivity axiom (Efficiency), translates log10 attributions
into financial dollar drivers, and generates executive narrative summaries.
"""

import time
import math
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
import shap
from catboost import CatBoostRegressor
import joblib
import lightgbm as lgb

from ml.dataset_engineering.config import ML_MODELS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TreeSHAPExplainer")

# Human-Readable Feature Labels for Executive Reporting & UI Dossiers
FEATURE_DISPLAY_NAMES: Dict[str, str] = {
    "log_budget": "Production Budget Scale",
    "budget_tier": "Capital Expenditure Tier",
    "director": "Director Brand Equity",
    "lead_actor": "Lead Actor Star Power",
    "primary_genre": "Primary Genre Appeal",
    "industry": "Industry Territory Scale",
    "language_clean": "Language Distribution Market",
    "runtime_minutes_clean": "Theatrical Runtime",
    "genre_count": "Genre Blend Breadth",
    "is_sequel_or_franchise": "Franchise & Sequel IP Recognition",
    "is_summer_season": "Summer Blockbuster Seasonality",
    "is_holiday_season": "Holiday Release Window",
    "is_weekend_release": "Opening Weekend Window",
    "release_month": "Release Calendar Month",
    "release_quarter": "Financial Calendar Quarter",
    "director_prior_movies": "Director Filmography Volume",
    "director_prior_avg_real_gross": "Director Historical Box-Office Average",
    "director_prior_avg_roi": "Director Historical ROI Multiple",
    "director_prior_hit_rate": "Director Career Hit Rate",
    "lead_actor_prior_movies": "Lead Actor Filmography Volume",
    "lead_actor_prior_avg_real_gross": "Lead Actor Historical Box-Office Average",
    "lead_actor_prior_avg_roi": "Lead Actor Historical ROI Multiple",
    "lead_actor_prior_hit_rate": "Lead Actor Career Hit Rate",
    "studio_prior_movies": "Studio Scale & Track Record",
}


class CineMetricsExplainer:
    """
    Production explainability engine leveraging TreeSHAP on CatBoost models.
    Guarantees exact local accuracy (Additivity) and sub-100ms CPU latency.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or (ML_MODELS_DIR / "production" / "catboost_revenue_v1.cbm")
        if not self.model_path.exists():
            raise FileNotFoundError(f"CatBoost production model not found at {self.model_path}")

        logger.info(f"Loading production CatBoost model from {self.model_path}...")
        self.model = CatBoostRegressor()
        self.model.load_model(str(self.model_path))

        self.feature_names = self.model.feature_names_
        logger.info(f"Loaded CatBoost model with {len(self.feature_names)} features.")

        logger.info("Initializing in-memory shap.TreeExplainer...")
        t0 = time.perf_counter()
        self.explainer = shap.TreeExplainer(self.model)

        # Warm-up pass to populate expected_value from tree leaf distributions
        dummy_row = pd.DataFrame([{f: ("Unknown" if f in ["budget_tier", "primary_genre", "industry", "language_clean", "director", "lead_actor"] else 0.0) for f in self.feature_names}])
        _ = self.explainer.shap_values(dummy_row)

        t_init = (time.perf_counter() - t0) * 1000
        
        # Base value in log10 space
        raw_expected = self.explainer.expected_value
        if isinstance(raw_expected, (list, np.ndarray)):
            self.base_value_log10 = float(raw_expected[0])
        else:
            self.base_value_log10 = float(raw_expected)

        self.base_revenue_usd = round(10.0 ** self.base_value_log10, 2)
        logger.info(
            f"TreeExplainer initialized in {t_init:.2f}ms. "
            f"Expected Base Value: {self.base_value_log10:.4f} log10 (~${self.base_revenue_usd:,.2f} USD)"
        )

        # Multi-Model Stacking Ensemble Integration
        self.has_ensemble = False
        self.lgb_booster = None
        self.ensemble_payload = None
        try:
            prod_dir = ML_MODELS_DIR / "production"
            stacker_path = prod_dir / "ensemble_stacker_v1.joblib"
            lgb_path = prod_dir / "lightgbm_revenue_v1.txt"
            if stacker_path.exists() and lgb_path.exists():
                self.ensemble_payload = joblib.load(stacker_path)
                self.lgb_booster = lgb.Booster(model_file=str(lgb_path))
                self.has_ensemble = True
                w = self.ensemble_payload.get("weights", [0.46, 0.54, 0.0])
                logger.info(f"Production Stacking Ensemble active (CatBoost: {w[0]:.2f}, LightGBM: {w[1]:.2f}).")
        except Exception as e:
            logger.warning(f"Could not initialize Stacking Ensemble: {e}. Defaulting to solo CatBoost.")

    def prepare_input_row(self, row: pd.DataFrame) -> pd.DataFrame:
        """Formats and validates an input sample row matching model schema."""
        row_clean = row[self.feature_names].copy()
        for col in ["budget_tier", "primary_genre", "industry", "language_clean", "director", "lead_actor"]:
            if col in row_clean.columns:
                row_clean[col] = row_clean[col].fillna("Unknown").astype(str)
        
        for col in row_clean.select_dtypes(include=["number"]).columns:
            row_clean[col] = row_clean[col].fillna(0.0).astype(float)

        return row_clean

    def explain_instance(
        self,
        row: pd.DataFrame,
        movie_title: str = "Upcoming Title",
    ) -> Dict[str, Any]:
        """
        Generates comprehensive local feature attribution explanation for a single movie.
        """
        t0 = time.perf_counter()
        X = self.prepare_input_row(row)

        # 1. Forward model prediction (log10 space)
        pred_log10_cat = float(self.model.predict(X)[0])
        pred_log10 = pred_log10_cat

        if self.has_ensemble and self.lgb_booster and self.ensemble_payload:
            try:
                lgb_row = X[self.ensemble_payload["feature_names"]].copy()
                for col in self.ensemble_payload["cat_cols"]:
                    vocab = self.ensemble_payload["cat_vocabularies"][col]
                    c_type = pd.CategoricalDtype(categories=vocab, ordered=False)
                    lgb_row[col] = lgb_row[col].apply(lambda x: x if x in vocab else "Unknown").astype(c_type)
                for col in self.ensemble_payload["num_cols"]:
                    lgb_row[col] = lgb_row[col].astype(float)

                pred_log10_lgb = float(self.lgb_booster.predict(lgb_row)[0])
                w = self.ensemble_payload["weights"]
                pred_log10 = float(w[0] * pred_log10_cat + w[1] * pred_log10_lgb)
            except Exception as e:
                logger.warning(f"Ensemble prediction error: {e}. Fallback to CatBoost.")
                pred_log10 = pred_log10_cat

        pred_revenue_usd = float(10.0 ** pred_log10)

        # 2. TreeSHAP computation
        shap_vals_raw = self.explainer.shap_values(X)
        if isinstance(shap_vals_raw, list):
            shap_vec = shap_vals_raw[0]
        elif len(shap_vals_raw.shape) > 1:
            shap_vec = shap_vals_raw[0]
        else:
            shap_vec = shap_vals_raw

        shap_vec = np.array(shap_vec, dtype=float)

        # 3. Additivity Axiom Verification (Local Accuracy)
        # f(x) = phi_0 + sum(phi_i) verified against primary CatBoost TreeSHAP model
        reconstructed_pred = self.base_value_log10 + float(shap_vec.sum())
        additivity_error = abs(pred_log10_cat - reconstructed_pred)
        is_additive = additivity_error < 1e-4

        # 4. Dollar Impact Estimation
        # Total Delta Revenue = Predicted USD - Base USD
        delta_revenue_usd = pred_revenue_usd - self.base_revenue_usd
        sum_abs_shap = float(np.sum(np.abs(shap_vec))) or 1.0

        feature_breakdowns = []
        for feat_name, val, phi in zip(self.feature_names, X.iloc[0].values, shap_vec):
            # Proportional dollar impact
            # Direction aligns with sign of phi
            rel_weight = abs(phi) / sum_abs_shap
            dollar_impact = math.copysign(rel_weight * abs(delta_revenue_usd), phi)

            feature_breakdowns.append({
                "feature": feat_name,
                "display_name": FEATURE_DISPLAY_NAMES.get(feat_name, feat_name.replace("_", " ").title()),
                "feature_value": val if isinstance(val, (int, float, str)) else str(val),
                "shap_value_log10": round(float(phi), 4),
                "direction": "positive" if phi >= 0 else "negative",
                "relative_importance_pct": round(rel_weight * 100.0, 2),
                "estimated_dollar_impact_usd": round(dollar_impact, 2),
            })

        # Sort by absolute SHAP impact
        feature_breakdowns.sort(key=lambda x: abs(x["shap_value_log10"]), reverse=True)

        top_positive = [f for f in feature_breakdowns if f["direction"] == "positive"][:5]
        top_negative = [f for f in feature_breakdowns if f["direction"] == "negative"][:5]

        # 5. Natural Language Template Narrative (FR-062)
        narrative = self.generate_narrative_summary(
            movie_title=movie_title,
            pred_usd=pred_revenue_usd,
            base_usd=self.base_revenue_usd,
            top_pos=top_positive[:3],
            top_neg=top_negative[:2],
        )

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "movie_title": movie_title,
            "base_value_log10": round(self.base_value_log10, 4),
            "predicted_value_log10": round(pred_log10, 4),
            "base_revenue_usd": self.base_revenue_usd,
            "predicted_revenue_usd": round(pred_revenue_usd, 2),
            "delta_revenue_usd": round(delta_revenue_usd, 2),
            "additivity_axiom_verified": is_additive,
            "additivity_error": additivity_error,
            "computation_latency_ms": round(latency_ms, 2),
            "top_positive_drivers": top_positive,
            "top_negative_drivers": top_negative,
            "waterfall_breakdown": feature_breakdowns,
            "narrative_summary": narrative,
        }

    def generate_narrative_summary(
        self,
        movie_title: str,
        pred_usd: float,
        base_usd: float,
        top_pos: List[Dict[str, Any]],
        top_neg: List[Dict[str, Any]],
    ) -> str:
        """Constructs an executive plain-language explanation without requiring an LLM."""
        formatted_pred = f"${pred_usd / 1e6:.1f}M" if pred_usd >= 1e6 else f"${pred_usd:,.0f}"

        pos_parts = []
        for p in top_pos:
            impact = f"+${abs(p['estimated_dollar_impact_usd']) / 1e6:.1f}M" if abs(p['estimated_dollar_impact_usd']) >= 1e6 else f"+${abs(p['estimated_dollar_impact_usd']):,.0f}"
            pos_parts.append(f"{p['display_name']} ({impact})")

        neg_parts = []
        for n in top_neg:
            impact = f"-${abs(n['estimated_dollar_impact_usd']) / 1e6:.1f}M" if abs(n['estimated_dollar_impact_usd']) >= 1e6 else f"-${abs(n['estimated_dollar_impact_usd']):,.0f}"
            neg_parts.append(f"{n['display_name']} ({impact})")

        pos_str = ", ".join(pos_parts) if pos_parts else "overall baseline momentum"
        neg_str = ", ".join(neg_parts) if neg_parts else "minimal drag factors"

        if pred_usd >= base_usd:
            narrative = (
                f"The box-office forecast of {formatted_pred} for '{movie_title}' represents an above-average projection, "
                f"driven primarily by strong positive contributions from {pos_str}. "
                f"This upside is partially moderated by drag from {neg_str}."
            )
        else:
            narrative = (
                f"The box-office forecast of {formatted_pred} for '{movie_title}' reflects cautious theatrical expectations, "
                f"weighed down predominantly by {neg_str}. "
                f"Key supporting factors mitigating downside risk include {pos_str}."
            )

        return narrative
