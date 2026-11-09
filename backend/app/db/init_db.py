"""
CineMetrics — Database Initializer & Canonical Catalog Seeder
Initializes database schema and hydrates SQLite / PostgreSQL with:
1. Active upcoming movie predictions from `data/processed/active_predictions.parquet`
2. Upcoming metadata from `data/processed/upcoming_discovery_catalog.parquet`
3. Canonical historical movies from `data/unified/unified_movies.parquet`
4. Historical prediction revisions from `data/processed/prediction_history.jsonl`
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import engine, SessionLocal, Base
from backend.app.db.models import (
    Movie,
    Prediction,
    DigitalBuzzObservation,
    PredictionHistoryRecord,
)

logger = logging.getLogger("InitDB")


def safe_int(val: Any, default: int = 0) -> int:
    if pd.isna(val) or val is None:
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def safe_float(val: Any, default: float = 0.0) -> float:
    if pd.isna(val) or val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def seed_database(db: Session, force_reseed: bool = False):
    """Populates database tables from parquet sources if empty or force_reseed=True."""
    movie_count = db.query(Movie).count()
    if movie_count > 0 and not force_reseed:
        logger.info(f"Database already contains {movie_count} movies. Skipping seeding.")
        return

    logger.info("Starting database catalog seeding...")

    # 1. Load Upcoming Catalog and Active Predictions
    upcoming_cat_path = settings.PROCESSED_DIR / "upcoming_discovery_catalog.parquet"
    active_pred_path = settings.PROCESSED_DIR / "active_predictions.parquet"

    upcoming_dict = {}
    if upcoming_cat_path.exists():
        df_up = pd.read_parquet(upcoming_cat_path)
        for _, row in df_up.iterrows():
            cid = str(row.get("canonical_id", ""))
            if cid:
                upcoming_dict[cid] = row.to_dict()

    active_pred_dict = {}
    if active_pred_path.exists():
        df_act = pd.read_parquet(active_pred_path)
        for _, row in df_act.iterrows():
            cid = str(row.get("canonical_id", ""))
            if cid:
                active_pred_dict[cid] = row.to_dict()

    inserted_ids = set()
    for cid, up_row in upcoming_dict.items():
        if cid in inserted_ids:
            continue

        pred = active_pred_dict.get(cid, {})
        budget_usd = safe_float(up_row.get("budget_clean_usd"), 0.0)
        budget_inr = round(budget_usd * settings.DEFAULT_INR_USD_RATE / 100_000_000.0, 2)

        # Parse genres
        raw_genre = up_row.get("primary_genre", "Drama")
        genres_json = json.dumps([raw_genre] if isinstance(raw_genre, str) else list(raw_genre))

        # Parse cast
        top_cast_raw = up_row.get("top_cast", "")
        if isinstance(top_cast_raw, str):
            cast_list = [c.strip() for c in top_cast_raw.split(",") if c.strip()]
        elif isinstance(top_cast_raw, (list, tuple)):
            cast_list = list(top_cast_raw)
        else:
            cast_list = []
        cast_json = json.dumps(cast_list)

        trailer_id = up_row.get("youtube_trailer_id")
        trailer_str = str(trailer_id) if pd.notna(trailer_id) and str(trailer_id) not in ("nan", "None", "") else None

        movie_entity = Movie(
            canonical_id=cid,
            tmdb_id=safe_int(up_row.get("tmdb_id"), None),
            primary_title=str(up_row.get("primary_title", "Untitled")),
            original_title=str(up_row.get("original_title", "")),
            release_date=str(up_row.get("release_date", "2025-01-01")),
            release_year=safe_int(up_row.get("release_year"), 2025),
            runtime_minutes=safe_int(up_row.get("runtime_minutes_clean"), 120),
            original_language=str(up_row.get("original_language", "en")),
            industry=str(up_row.get("industry", "Global")),
            genres=genres_json,
            director=str(up_row.get("director", "Unknown")),
            lead_actor=str(up_row.get("lead_actor", "Unknown")),
            cast_members=cast_json,
            overview=str(up_row.get("overview", "")),
            budget_usd=budget_usd,
            budget_inr_crores=budget_inr,
            box_office_gross_usd=None,
            box_office_gross_inr_crores=None,
            is_released=False,
            youtube_trailer_id=trailer_str,
        )
        db.add(movie_entity)
        db.flush()
        inserted_ids.add(cid)

        # Create active prediction record if available
        if pred:
            exp_usd = safe_float(pred.get("expected_gross_usd"), 50_000_000.0)
            exp_inr = round(exp_usd * settings.DEFAULT_INR_USD_RATE / 100_000_000.0, 2)
            pess_usd = round(exp_usd * 0.70, 2)
            opt_usd = round(exp_usd * 1.45, 2)

            pred_entity = Prediction(
                movie_id=movie_entity.id,
                prediction_stage=str(pred.get("lifecycle_stage", "Stage 1 Announcement")),
                readiness_score=safe_int(pred.get("readiness_score"), 65),
                status_badge=str(pred.get("status_badge", "Preview Forecast")),
                model_version="catboost_revenue_v1",
                expected_gross_usd=exp_usd,
                expected_gross_inr_crores=exp_inr,
                pessimistic_bound_80_usd=pess_usd,
                optimistic_bound_80_usd=opt_usd,
                pessimistic_bound_80_inr=round(pess_usd * settings.DEFAULT_INR_USD_RATE / 100_000_000.0, 2),
                optimistic_bound_80_inr=round(opt_usd * settings.DEFAULT_INR_USD_RATE / 100_000_000.0, 2),
                extreme_downside_95_usd=round(exp_usd * 0.45, 2),
                extreme_upside_95_usd=round(exp_usd * 2.10, 2),
                conformal_confidence=0.80,
                success_category=str(pred.get("risk_assessment_tier", "Hit")),
                success_probabilities=json.dumps({"Hit": 0.45, "Super Hit": 0.30, "Blockbuster": 0.15, "Average": 0.10}),
                prob_break_even=safe_float(pred.get("prob_break_even"), 0.75),
                prob_commercial_profit=safe_float(pred.get("prob_commercial_profit"), 0.60),
                prob_catastrophic_disaster=safe_float(pred.get("prob_catastrophic_disaster"), 0.05),
                risk_assessment_tier=str(pred.get("risk_assessment_tier", "Moderate Risk")),
                risk_badge=str(pred.get("risk_badge", "Commercial Favorable")),
                top_positive_factor=str(pred.get("top_positive_driver", "Director Track Record")),
                top_negative_factor=str(pred.get("top_negative_driver", "Capital Expenditure")),
                narrative_summary=str(pred.get("narrative_summary", "")),
            )
            db.add(pred_entity)

        # Seed Digital Buzz if available
        views = safe_int(up_row.get("trailer_view_count"), 0)
        if views > 0 and movie_entity.youtube_trailer_id:
            buzz_entity = DigitalBuzzObservation(
                movie_id=movie_entity.id,
                youtube_video_id=movie_entity.youtube_trailer_id,
                view_count=views,
                like_count=safe_int(up_row.get("trailer_like_count"), 0),
                comment_count=safe_int(up_row.get("trailer_comment_count"), 0),
                buzz_score=safe_float(up_row.get("composite_buzz_score"), 50.0),
                sentiment_net_polarity=safe_float(up_row.get("comment_sentiment_net_polarity"), 0.5),
                total_comments_sampled=100,
                positive_ratio=0.70,
                neutral_ratio=0.20,
                negative_ratio=0.10,
            )
            db.add(buzz_entity)

    # 2. Seed Canonical Released Movies from Unified Dataset (top 500)
    unified_path = settings.UNIFIED_DIR / "unified_movies.parquet"
    if unified_path.exists():
        df_uni = pd.read_parquet(unified_path)
        df_top = df_uni.sort_values(by="revenue_real_2024_usd", ascending=False).head(500)

        for _, row in df_top.iterrows():
            cid = str(row.get("canonical_id", ""))
            if cid in inserted_ids:
                continue

            budget_usd = safe_float(row.get("budget_real_2024_usd") or row.get("budget_nominal_usd"), 0.0)
            gross_usd = safe_float(row.get("revenue_real_2024_usd") or row.get("revenue_nominal_usd"), 0.0)
            budget_inr = round(budget_usd * settings.DEFAULT_INR_USD_RATE / 100_000_000.0, 2)
            gross_inr = round(gross_usd * settings.DEFAULT_INR_USD_RATE / 100_000_000.0, 2)

            genres_val = row.get("genres")
            if isinstance(genres_val, (list, tuple)):
                genres_json = json.dumps(list(genres_val))
            elif isinstance(genres_val, str) and genres_val.startswith("["):
                genres_json = genres_val
            elif isinstance(genres_val, str):
                genres_json = json.dumps([g.strip() for g in genres_val.split(",") if g.strip()])
            else:
                genres_json = json.dumps(["Feature Film"])

            lead_actor = str(row.get("lead_actor") or "Unknown")
            cast_json = json.dumps([lead_actor] if lead_actor != "Unknown" else [])

            movie_entity = Movie(
                canonical_id=cid,
                imdb_id=str(row.get("imdb_tconst", "")) if pd.notna(row.get("imdb_tconst")) else None,
                tmdb_id=safe_int(row.get("tmdb_id"), None),
                primary_title=str(row.get("primary_title", "Untitled")),
                original_title=str(row.get("original_title", "")),
                release_date=str(row.get("release_date", f"{safe_int(row.get('release_year'), 2020)}-01-01")),
                release_year=safe_int(row.get("release_year"), 2020),
                runtime_minutes=safe_int(row.get("runtime_minutes"), 120),
                original_language=str(row.get("original_language", "en")),
                industry=str(row.get("industry", "Global")),
                genres=genres_json,
                director=str(row.get("director", "Unknown")),
                lead_actor=lead_actor,
                cast_members=cast_json,
                production_company=str(row.get("production_company", "")),
                overview=f"Canonical release directed by {row.get('director', 'Unknown')}, starring {lead_actor}.",
                budget_usd=budget_usd,
                budget_inr_crores=budget_inr,
                box_office_gross_usd=gross_usd,
                box_office_gross_inr_crores=gross_inr,
                is_released=True,
            )
            db.add(movie_entity)
            inserted_ids.add(cid)

    # 3. Seed Prediction History if JSONL exists
    history_path = settings.PROCESSED_DIR / "prediction_history.jsonl"
    if history_path.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    cid = rec.get("canonical_id")
                    movie_match = db.query(Movie).filter(Movie.canonical_id == cid).first()
                    if movie_match:
                        hist_entity = PredictionHistoryRecord(
                            movie_id=movie_match.id,
                            prediction_stage=str(rec.get("lifecycle_stage", "Stage 1 Announcement")),
                            readiness_score=safe_int(rec.get("readiness_score"), 70),
                            expected_gross_usd=safe_float(rec.get("expected_gross_usd"), 0.0),
                            delta_usd=safe_float(rec.get("delta_tracking", {}).get("delta_usd"), 0.0),
                            delta_pct=safe_float(rec.get("delta_tracking", {}).get("delta_pct"), 0.0),
                            change_attribution=str(rec.get("delta_tracking", {}).get("change_attribution", "Initial forecast")),
                        )
                        db.add(hist_entity)
        except Exception as e:
            logger.warning(f"Could not load prediction history: {e}")

    db.commit()
    total_movies = db.query(Movie).count()
    total_preds = db.query(Prediction).count()
    logger.info(f"Database successfully seeded! Total movies: {total_movies}, Active predictions: {total_preds}")


def init_db(force_reseed: bool = False):
    """Initializes tables and runs seeder."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db, force_reseed=force_reseed)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db(force_reseed=True)
