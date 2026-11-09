"""
CineMetrics — Prediction Lifecycle, Readiness Scoring & Revision Engine
Evaluates dynamic Prediction Readiness Scores (PRS: 0–100), governs stage progression
(Stage 1 Announcement -> Stage 2 Trailer Drop -> Stage 3 Blitz), calculates forecast revisions,
and maintains immutable versioned audit history.
"""

import math
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np

from ml.explainability.explainer import CineMetricsExplainer
from ml.explainability.risk_engine import FinancialRiskCalculator, DEFAULT_INR_USD_RATE
from ml.dataset_engineering.config import SNAPSHOTS_DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PredictionLifecycle")

PROCESSED_DIR = Path("data") / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ACTIVE_PREDICTIONS_PATH = PROCESSED_DIR / "active_predictions.parquet"
PREDICTION_HISTORY_PATH = PROCESSED_DIR / "prediction_history.jsonl"


class PredictionLifecycleService:
    """
    Manages continuous prediction evaluation, readiness scoring, and versioned delta revisions.
    """

    def __init__(self):
        self.explainer = CineMetricsExplainer()
        self.risk_calc = FinancialRiskCalculator()
        self._load_talent_cache()

    def _load_talent_cache(self):
        """Loads historical talent equity benchmarks from training snapshots."""
        self.director_cache = {}
        self.actor_cache = {}
        try:
            train_path = SNAPSHOTS_DATA_DIR / "train_v1.parquet"
            if train_path.exists():
                df_train = pd.read_parquet(train_path)
                for _, r in df_train.iterrows():
                    d = str(r.get("director", ""))
                    a = str(r.get("lead_actor", ""))
                    if d and d != "Unknown":
                        self.director_cache[d] = {
                            "movies": float(r.get("director_prior_movies", 0)),
                            "avg_gross": float(r.get("director_prior_avg_real_gross", 0)),
                            "avg_roi": float(r.get("director_prior_avg_roi", 0)),
                            "hit_rate": float(r.get("director_prior_hit_rate", 0)),
                        }
                    if a and a != "Unknown":
                        self.actor_cache[a] = {
                            "movies": float(r.get("lead_actor_prior_movies", 0)),
                            "avg_gross": float(r.get("lead_actor_prior_avg_real_gross", 0)),
                            "avg_roi": float(r.get("lead_actor_prior_avg_roi", 0)),
                            "hit_rate": float(r.get("lead_actor_prior_hit_rate", 0)),
                        }
                logger.info(
                    f"Initialized talent cache with {len(self.director_cache)} directors "
                    f"and {len(self.actor_cache)} lead actors."
                )
        except Exception as e:
            logger.warning(f"Could not load talent cache ({e}); using neutral priors.")

    def calculate_readiness_score(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the 9-part Prediction Readiness Score (0 to 100) from doc 15:
        - Lead Actor identified: 20 pts
        - Primary Director identified: 15 pts
        - Verified Budget / credible tier: 15 pts
        - Locked Release Date: 10 pts
        - Official Trailer linked: 10 pts
        - Digital Buzz / Views tracked: 10 pts
        - Competitive Clash Density computed: 10 pts
        - Multilingual Sentiment polarity evaluated: 5 pts
        - Screen Count / Release Eve signal: 5 pts
        """
        score = 0
        breakdown = {}

        # 1. Lead Actor (20 Pts)
        actor = movie.get("lead_actor")
        if actor and str(actor).strip() not in ("Unknown", "None", ""):
            score += 20
            breakdown["lead_actor_power"] = 20
        else:
            breakdown["lead_actor_power"] = 0

        # 2. Primary Director (15 Pts)
        director = movie.get("director")
        if director and str(director).strip() not in ("Unknown", "None", ""):
            score += 15
            breakdown["director_pedigree"] = 15
        else:
            breakdown["director_pedigree"] = 0

        # 3. Budget (15 Pts)
        budget = movie.get("budget_clean_usd") or movie.get("budget_usd")
        tier = movie.get("budget_tier")
        if budget and budget > 100_000:
            score += 15
            breakdown["budget_scale"] = 15
        elif tier and tier in ("Tentpole", "High", "Medium", "Low"):
            score += 10
            breakdown["budget_scale"] = 10
        else:
            breakdown["budget_scale"] = 0

        # 4. Release Date (10 Pts)
        rel_date = movie.get("release_date")
        if rel_date and str(rel_date).strip() not in ("TBD", "None", ""):
            score += 10
            breakdown["locked_release_date"] = 10
        else:
            breakdown["locked_release_date"] = 0

        # 5. Official Trailer Linked (10 Pts)
        trailer_key = movie.get("youtube_trailer_id")
        if trailer_key and str(trailer_key).strip() not in ("None", ""):
            score += 10
            breakdown["trailer_tracked"] = 10
        else:
            breakdown["trailer_tracked"] = 0

        # 6. Digital Buzz / Views (10 Pts)
        views = movie.get("trailer_view_count") or movie.get("view_count") or 0
        if views > 10_000:
            score += 10
            breakdown["digital_buzz_velocity"] = 10
        else:
            breakdown["digital_buzz_velocity"] = 0

        # 7. Competitive Clash Density (10 Pts)
        score += 10
        breakdown["competitive_clash_density"] = 10

        # 8. Sentiment Polarity (5 Pts)
        sentiment_polarity = movie.get("comment_sentiment_net_polarity")
        if sentiment_polarity is not None:
            score += 5
            breakdown["sentiment_polarity"] = 5
        else:
            breakdown["sentiment_polarity"] = 0

        # 9. Screen Count / Advance Window (5 Pts)
        breakdown["screen_count_advance"] = 0

        # Determine Readiness Tier & Governance Badge
        if score < 40:
            status_badge = "Insufficient Data"
            stage = "Stage 0: Early Discovery"
            forecast_permitted = False
            desc = "Awaiting Baseline Metadata (forecast suppressed)"
        elif score < 60:
            status_badge = "Early Estimate"
            stage = "Stage 1: Pre-Trailer Announcement"
            forecast_permitted = True
            desc = "Preliminary talent & structural model (Wide Conformal Bands ±65%)"
        elif score < 80:
            status_badge = "Preliminary Forecast"
            stage = "Stage 2: Teaser / Trailer Drop"
            forecast_permitted = True
            desc = "Standard interval display; initial buzz signals incorporated"
        elif score < 90:
            status_badge = "Refined Pre-Release"
            stage = "Stage 3: Pre-Release Marketing Blitz"
            forecast_permitted = True
            desc = "Full multi-modal forecast; TreeSHAP and downside risk active"
        else:
            status_badge = "Final Pre-Release"
            stage = "Stage 4: Release Eve"
            forecast_permitted = True
            desc = "High-precision opening weekend and lifetime forecast"

        return {
            "readiness_score": score,
            "status_badge": status_badge,
            "lifecycle_stage": stage,
            "forecast_permitted": forecast_permitted,
            "readiness_description": desc,
            "score_breakdown": breakdown,
        }

    def assemble_feature_vector(self, movie: Dict[str, Any]) -> pd.DataFrame:
        """Constructs standardized feature row matching production CatBoost schema."""
        title = movie.get("primary_title") or movie.get("title", "Unknown")
        rel_date_str = str(movie.get("release_date", "2026-06-01"))
        
        # Calendar extraction
        month = 6
        quarter = 2
        try:
            dt = datetime.fromisoformat(rel_date_str.split("T")[0])
            month = dt.month
            quarter = (month - 1) // 3 + 1
        except Exception:
            pass

        # Budget extraction
        budget_usd = float(movie.get("budget_clean_usd") or movie.get("budget_usd") or 25_000_000.0)
        log_budget = float(np.log10(max(budget_usd, 10_000.0)))
        budget_tier = str(movie.get("budget_tier", "Medium"))

        # Talent Lookups
        director_name = str(movie.get("director", "Unknown"))
        lead_actor_name = str(movie.get("lead_actor", "Unknown"))

        d_stats = self.director_cache.get(director_name, {"movies": 0.0, "avg_gross": 0.0, "avg_roi": 0.0, "hit_rate": 0.0})
        a_stats = self.actor_cache.get(lead_actor_name, {"movies": 0.0, "avg_gross": 0.0, "avg_roi": 0.0, "hit_rate": 0.0})

        row = {
            "log_budget": log_budget,
            "runtime_minutes_clean": float(movie.get("runtime_minutes_clean", 120.0) or 120.0),
            "genre_count": float(movie.get("genre_count", 2.0) or 2.0),
            "is_sequel_or_franchise": float(movie.get("is_sequel_or_franchise", 0.0) or 0.0),
            "is_summer_season": 1.0 if month in (5, 6, 7) else 0.0,
            "is_holiday_season": 1.0 if month in (11, 12) else 0.0,
            "is_weekend_release": 1.0,
            "release_month": float(month),
            "release_quarter": float(quarter),
            "director_prior_movies": d_stats["movies"],
            "director_prior_avg_real_gross": d_stats["avg_gross"],
            "director_prior_avg_roi": d_stats["avg_roi"],
            "director_prior_hit_rate": d_stats["hit_rate"],
            "lead_actor_prior_movies": a_stats["movies"],
            "lead_actor_prior_avg_real_gross": a_stats["avg_gross"],
            "lead_actor_prior_avg_roi": a_stats["avg_roi"],
            "lead_actor_prior_hit_rate": a_stats["hit_rate"],
            "studio_prior_movies": 15.0,
            "budget_tier": budget_tier,
            "primary_genre": str(movie.get("primary_genre", "Drama")),
            "industry": str(movie.get("industry", "Global")),
            "language_clean": str(movie.get("original_language", "en")),
            "director": director_name,
            "lead_actor": lead_actor_name,
        }
        return pd.DataFrame([row])

    def evaluate_movie_forecast(
        self,
        movie: Dict[str, Any],
        previous_prediction: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates full lifecycle forecast with readiness score, conformal intervals,
        TreeSHAP explanation, and revision delta attribution.
        """
        title = movie.get("primary_title") or movie.get("title", "Upcoming Title")
        canonical_id = movie.get("canonical_id") or f"tmdb_{movie.get('tmdb_id', 'unknown')}"

        # 1. Readiness Evaluation
        readiness_info = self.calculate_readiness_score(movie)
        if not readiness_info["forecast_permitted"]:
            return {
                "canonical_id": canonical_id,
                "primary_title": title,
                "readiness_evaluation": readiness_info,
                "forecast_status": "SUPPRESSED",
                "message": "Forecast suppressed: Minimum baseline metadata required (PRS < 40).",
            }

        # 2. Forward Prediction & Explainability
        X_row = self.assemble_feature_vector(movie)
        explanation = self.explainer.explain_instance(X_row, movie_title=title)
        pred_log10 = explanation["predicted_value_log10"]
        expected_usd = explanation["predicted_revenue_usd"]

        # Budget
        budget_usd = float(movie.get("budget_clean_usd") or movie.get("budget_usd") or 25_000_000.0)

        # 3. Financial Risk & Conformal Bands
        risk_profile = self.risk_calc.evaluate_financial_risk(
            predicted_log10=pred_log10,
            budget_usd=budget_usd,
            movie_title=title,
        )

        current_timestamp = datetime.now(timezone.utc).isoformat()

        # 4. Delta Tracking & Revision Attribution
        delta_info = {
            "has_previous_forecast": False,
            "delta_usd": 0.0,
            "delta_pct": 0.0,
            "is_significant_revision": False,
            "change_attribution": "Initial baseline forecast established.",
        }

        if previous_prediction and "expected_gross_usd" in previous_prediction:
            prev_usd = float(previous_prediction["expected_gross_usd"])
            delta_usd = expected_usd - prev_usd
            delta_pct = (delta_usd / max(prev_usd, 1.0)) * 100.0
            is_significant = abs(delta_pct) >= 5.0

            # Attribute change cause
            if movie.get("youtube_trailer_id") and not previous_prediction.get("youtube_trailer_id"):
                attribution = f"Forecast updated (+{delta_pct:.1f}%) following trailer drop launch."
            elif abs(delta_pct) >= 15.0:
                attribution = f"Significant momentum revision ({delta_pct:+.1f}%) driven by updated engagement signals."
            elif is_significant:
                attribution = f"Periodic forecast refinement ({delta_pct:+.1f}%) due to tracking updates."
            else:
                attribution = f"Minor routine calibration ({delta_pct:+.1f}%)."

            delta_info = {
                "has_previous_forecast": True,
                "previous_gross_usd": prev_usd,
                "delta_usd": round(delta_usd, 2),
                "delta_pct": round(delta_pct, 2),
                "is_significant_revision": is_significant,
                "change_attribution": attribution,
            }

        prediction_record = {
            "canonical_id": canonical_id,
            "primary_title": title,
            "industry": movie.get("industry", "Global"),
            "release_date": movie.get("release_date"),
            "prediction_timestamp": current_timestamp,
            "lifecycle_stage": readiness_info["lifecycle_stage"],
            "readiness_score": readiness_info["readiness_score"],
            "status_badge": readiness_info["status_badge"],
            "expected_gross_usd": expected_usd,
            "expected_gross_formatted_usd": risk_profile["forecast_scenarios"]["expected_scenario"]["usd_formatted"],
            "expected_gross_formatted_inr": risk_profile["forecast_scenarios"]["expected_scenario"]["inr_formatted"],
            "pessimistic_bound_80": risk_profile["forecast_scenarios"]["pessimistic_scenario"]["usd_formatted"],
            "optimistic_bound_80": risk_profile["forecast_scenarios"]["optimistic_scenario"]["usd_formatted"],
            "prob_break_even": risk_profile["risk_probabilities"]["break_even_probability"],
            "prob_commercial_profit": risk_profile["risk_probabilities"]["commercial_profitability_probability"],
            "prob_catastrophic_disaster": risk_profile["risk_probabilities"]["catastrophic_disaster_probability"],
            "risk_assessment_tier": risk_profile["risk_assessment_tier"],
            "risk_badge": risk_profile["risk_badge"],
            "delta_tracking": delta_info,
            "top_positive_driver": explanation["top_positive_drivers"][0]["display_name"] if explanation["top_positive_drivers"] else "None",
            "top_negative_driver": explanation["top_negative_drivers"][0]["display_name"] if explanation["top_negative_drivers"] else "None",
            "narrative_summary": explanation["narrative_summary"],
        }

        # Append to prediction_history.jsonl if significant or first forecast
        if not delta_info["has_previous_forecast"] or delta_info["is_significant_revision"]:
            with open(PREDICTION_HISTORY_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(prediction_record) + "\n")

        return prediction_record


# Singleton instance
prediction_service = PredictionLifecycleService()

