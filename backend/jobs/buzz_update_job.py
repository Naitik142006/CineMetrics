"""
CineMetrics — Continuous Digital Buzz Update & Prediction Lifecycle Worker
Periodically polls YouTube trailer metrics, updates digital buzz scores,
detects significant feature deltas, and recalculates versioned movie forecasts.
"""

import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

from ml.nlp.trailer_buzz_harvester import TrailerBuzzHarvester
from backend.app.services.prediction_service import (
    prediction_service,
    ACTIVE_PREDICTIONS_PATH,
    PREDICTION_HISTORY_PATH,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("BuzzLifecycleWorker")

CATALOG_PATH = Path("data") / "processed" / "upcoming_discovery_catalog.parquet"
REPORT_PATH = Path("backend") / "jobs" / "PREDICTION_LIFECYCLE_REPORT.md"


class BuzzLifecycleEngine:
    """
    Automated worker updating trailer buzz metrics and triggering prediction revisions.
    """

    def __init__(self):
        self.harvester = TrailerBuzzHarvester()

    def run_lifecycle_update(self, max_trailers_to_poll: int = 15) -> Dict[str, Any]:
        """
        Executes a continuous lifecycle refresh:
        1. Loads upcoming radar catalog
        2. Polls YouTube trailer statistics for active trailers
        3. Recalculates Prediction Readiness Scores
        4. Re-evaluates forecasts and logs significant deltas
        5. Updates active_predictions.parquet and generates markdown report
        """
        t0 = time.perf_counter()
        cycle_timestamp = datetime.now(timezone.utc).isoformat()
        logger.info(f"Starting prediction lifecycle & buzz update cycle at {cycle_timestamp}...")

        if not CATALOG_PATH.exists():
            logger.warning(f"Upcoming catalog not found at {CATALOG_PATH}")
            return {"status": "error", "message": "Catalog not found"}

        catalog_df = pd.read_parquet(CATALOG_PATH)
        logger.info(f"Loaded {len(catalog_df)} upcoming releases from catalog.")

        # Load existing active predictions if available for delta comparison
        existing_predictions: Dict[str, Dict[str, Any]] = {}
        if ACTIVE_PREDICTIONS_PATH.exists():
            try:
                pred_df = pd.read_parquet(ACTIVE_PREDICTIONS_PATH)
                for _, r in pred_df.iterrows():
                    cid = r.get("canonical_id")
                    if cid:
                        existing_predictions[cid] = r.to_dict()
                logger.info(f"Loaded {len(existing_predictions)} existing active predictions.")
            except Exception as e:
                logger.warning(f"Could not load existing predictions ({e}); initializing fresh.")

        # 1. Update Buzz Metrics for films with official trailer IDs
        trailer_films = catalog_df[catalog_df["youtube_trailer_id"].notna() & (catalog_df["youtube_trailer_id"] != "")].copy()
        logger.info(f"Identified {len(trailer_films)} releases with active trailer keys.")

        updated_records = []
        poll_count = 0

        for _, row in catalog_df.iterrows():
            rec = row.to_dict()
            yt_id = rec.get("youtube_trailer_id")

            # Poll YouTube metrics if trailer is linked and within quota cap
            if yt_id and poll_count < max_trailers_to_poll:
                try:
                    logger.info(f"Polling YouTube buzz for '{rec.get('primary_title')}' ({yt_id})...")
                    buzz_res = self.harvester.process_movie_trailer_buzz(
                        movie_title=rec.get("primary_title", "Unknown"),
                        release_year=rec.get("release_year"),
                        release_date=rec.get("release_date"),
                        video_id=yt_id,
                        max_comments=25,
                    )
                    if buzz_res.get("has_trailer_data"):
                        rec["trailer_view_count"] = buzz_res.get("trailer_view_count")
                        rec["trailer_like_count"] = buzz_res.get("trailer_like_count")
                        rec["trailer_comment_count"] = buzz_res.get("trailer_comment_count")
                        rec["like_to_view_ratio"] = buzz_res.get("like_to_view_ratio")
                        rec["daily_view_velocity"] = buzz_res.get("daily_view_velocity")
                        rec["comment_sentiment_net_polarity"] = buzz_res.get("comment_sentiment_net_polarity")
                        rec["composite_buzz_score"] = buzz_res.get("composite_buzz_score")
                    poll_count += 1
                except Exception as e:
                    logger.warning(f"Failed to refresh buzz for {rec.get('primary_title')}: {e}")

            updated_records.append(rec)

        # Save updated catalog
        updated_catalog_df = pd.DataFrame(updated_records)
        updated_catalog_df.to_parquet(CATALOG_PATH, engine="pyarrow", compression="snappy", index=False)
        logger.info(f"Updated catalog saved to {CATALOG_PATH}.")

        # 2. Evaluate Multi-Stage Predictions across all releases
        active_prediction_records = []
        revisions_count = 0

        for rec in updated_records:
            cid = rec.get("canonical_id") or f"tmdb_{rec.get('tmdb_id')}"
            prev_pred = existing_predictions.get(cid)

            pred_res = prediction_service.evaluate_movie_forecast(rec, previous_prediction=prev_pred)
            if pred_res.get("forecast_status") != "SUPPRESSED":
                active_prediction_records.append(pred_res)
                if pred_res.get("delta_tracking", {}).get("is_significant_revision"):
                    revisions_count += 1

        # 3. Save Active Predictions Parquet
        if active_prediction_records:
            active_df = pd.DataFrame(active_prediction_records)
            # Flatten dict columns for clean Parquet export
            active_df_export = active_df.copy()
            if "delta_tracking" in active_df_export.columns:
                active_df_export["delta_attribution"] = active_df_export["delta_tracking"].apply(
                    lambda x: x.get("change_attribution") if isinstance(x, dict) else ""
                )
                active_df_export = active_df_export.drop(columns=["delta_tracking"])
            active_df_export.to_parquet(ACTIVE_PREDICTIONS_PATH, engine="pyarrow", compression="snappy", index=False)
            logger.info(f"Persisted {len(active_df)} active predictions to {ACTIVE_PREDICTIONS_PATH}.")

        duration = round(time.perf_counter() - t0, 2)

        summary = {
            "cycle_timestamp": cycle_timestamp,
            "duration_seconds": duration,
            "total_releases_evaluated": len(updated_records),
            "trailers_polled": poll_count,
            "active_forecasts_generated": len(active_prediction_records),
            "significant_revisions_logged": revisions_count,
        }

        # 4. Generate Report
        report_md = self.generate_lifecycle_report(summary, active_prediction_records)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report_md)
        logger.info(f"Generated prediction lifecycle report at {REPORT_PATH}")

        return summary

    def generate_lifecycle_report(
        self,
        summary: Dict[str, Any],
        predictions: List[Dict[str, Any]],
    ) -> str:
        """Constructs markdown report for prediction lifecycle status."""
        md = []
        md.append("# CineMetrics — Prediction Lifecycle, Readiness & Revision Report\n")
        md.append(f"**Execution Timestamp:** `{summary['cycle_timestamp']}`  ")
        md.append(f"**Cycle Duration:** `{summary['duration_seconds']}s`  ")
        md.append(f"**Active Live Forecasts:** `{summary['active_forecasts_generated']}` releases  ")
        md.append(f"**Significant Revisions Logged:** `{summary['significant_revisions_logged']}` updates  \n")
        md.append("---\n")

        md.append("## 1. Executive Prediction Lifecycle Overview\n")
        md.append("| Metric | Value | Architectural Purpose |")
        md.append("|---|:---:|---|")
        md.append(f"| **Total Candidates Evaluated** | `{summary['total_releases_evaluated']}` | Full upcoming release portfolio scanned |")
        md.append(f"| **Active Trailers Polled** | `{summary['trailers_polled']}` | Real-time YouTube view counts and velocity updated |")
        md.append(f"| **Active Forecasts Generated** | `{summary['active_forecasts_generated']}` | Passed Prediction Readiness Gate (PRS $\ge 40$) |")
        md.append(f"| **Significant Revisions Logged** | `{summary['significant_revisions_logged']}` | Delta $\ge 5\%$ or stage advancement appended to `prediction_history` |")
        md.append("\n---\n")

        # Table of Active Upcoming Forecasts
        md.append("## 2. Active Upcoming Theatrical Forecasts (Live Radar)\n")
        md.append("| Movie Title | Industry | Release Date | Readiness Score | Lifecycle Stage | Expected Forecast (USD / INR) | 80% Conformal Range | Capital Risk | Change Attribution |")
        md.append("|---|---|:---:|:---:|---|:---:|:---:|:---:|---|")

        sorted_preds = sorted(predictions, key=lambda x: x.get("expected_gross_usd", 0), reverse=True)
        for r in sorted_preds:
            p_usd = r.get("expected_gross_formatted_usd")
            p_inr = r.get("expected_gross_formatted_inr")
            range_str = f"`{r.get('pessimistic_bound_80')} - {r.get('optimistic_bound_80')}`"
            attr = r.get("delta_tracking", {}).get("change_attribution") or "Initial baseline established"
            md.append(
                f"| **{r.get('primary_title')}** | {r.get('industry')} | "
                f"`{r.get('release_date', 'TBD')}` | `{r.get('readiness_score')}/100` | "
                f"`{r.get('lifecycle_stage')}` | **{p_usd}** / {p_inr} | {range_str} | "
                f"{r.get('risk_badge')} | *{attr}* |"
            )
        md.append("\n---\n")

        md.append("## 3. Prediction Readiness Governance Audit\n")
        md.append("- **PRS 0–39 (Insufficient Data):** Predictions are strictly suppressed to avoid publishing irresponsible forecasts.")
        md.append("- **PRS 40–59 (Early Estimate):** Wide conformal bands ($\pm 65\%$) communicate early uncertainty.")
        md.append("- **PRS 60–79 (Preliminary Forecast):** Trailer buzz and digital velocity incorporated; intervals shrink by $\sim 15\%$.")
        md.append("- **PRS 80–100 (Refined / Final Pre-Release):** Full TreeSHAP attribution and multi-modal risk calculation unlocked.\n")

        md.append("## 4. Architectural Conclusions & Downstream API Serving\n")
        md.append("1. **Continuous Forecast Evolution:** Static one-off predictions are eliminated; forecasts live as versioned entities updated automatically.")
        md.append("2. **Auditability:** Every delta $\ge 5\%$ is appended to `data/processed/prediction_history.jsonl` with clear causal attribution.")
        md.append("3. **Ready for FastAPI Service:** `active_predictions.parquet` serves instant cached HTTP reads for the Upcoming Releases radar in Phase 13.\n")

        return "\n".join(md)


def start_buzz_scheduler():
    """Starts background recurring scheduler for continuous buzz updates."""
    scheduler = BackgroundScheduler()
    engine = BuzzLifecycleEngine()

    # Poll every 6 hours
    scheduler.add_job(
        engine.run_lifecycle_update,
        "interval",
        hours=6,
        id="continuous_buzz_lifecycle",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Continuous Buzz Lifecycle scheduler started (running every 6 hours).")
    return scheduler


if __name__ == "__main__":
    logger.info("Executing standalone prediction lifecycle update cycle...")
    engine = BuzzLifecycleEngine()
    res = engine.run_lifecycle_update(max_trailers_to_poll=10)
    print("\n" + "=" * 60)
    print("PHASE 12 PREDICTION LIFECYCLE UPDATE COMPLETE")
    print("=" * 60)
    print(f"Releases Evaluated:    {res.get('total_releases_evaluated')}")
    print(f"Trailers Polled:       {res.get('trailers_polled')}")
    print(f"Active Forecasts:      {res.get('active_forecasts_generated')}")
    print(f"Significant Revisions: {res.get('significant_revisions_logged')}")
    print("=" * 60)

