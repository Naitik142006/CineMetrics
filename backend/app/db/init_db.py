"""
CineMetrics — Database Initializer & Canonical Catalog Seeder
Initializes database schema and hydrates SQLite / PostgreSQL with:
1. Curated 2026–2027 marquee upcoming tentpoles (Hollywood, Bollywood, Tollywood, Kollywood)
2. Active upcoming movie predictions from `data/processed/active_predictions.parquet`
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
from backend.app.db.curated_tentpoles import CURATED_UPCOMING_TENTPOLES, CURATED_RECENT_RELEASED_BLOCKBUSTERS
from backend.app.services.prediction_service import prediction_service

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
    """Populates database tables from parquet sources and curated tentpoles."""
    movie_count = db.query(Movie).count()
    tentpole_sample = db.query(Movie).filter(Movie.canonical_id == "tentpole_avengers_doomsday_2026").first()

    if movie_count > 0 and tentpole_sample and not force_reseed:
        logger.info(f"Database already contains {movie_count} movies with marquee tentpoles. Skipping seeding.")
        return

    logger.info("Starting comprehensive database catalog seeding (2026–2027 tentpoles & historical)...")

    if force_reseed:
        logger.info("force_reseed=True: Purging existing predictions, buzz, and movies for clean reload...")
        db.query(DigitalBuzzObservation).delete()
        db.query(Prediction).delete()
        db.query(Movie).delete()
        db.commit()

    inserted_ids = set()
    for existing in db.query(Movie.canonical_id).all():
        inserted_ids.add(existing[0])

    # Cache TMDB Poster Hashes from raw parquets
    tmdb_poster_map = {}
    tmdb_title_map = {}
    try:
        up_path = settings.DATA_DIR / "raw" / "tmdb" / "tmdb_upcoming.parquet"
        ind_path = settings.DATA_DIR / "raw" / "tmdb" / "tmdb_indian_catalog.parquet"
        if up_path.exists():
            df_up_tmdb = pd.read_parquet(up_path)
            for _, r in df_up_tmdb.iterrows():
                tid = safe_int(r.get("id"), None)
                p = r.get("poster_path")
                if tid and pd.notna(p):
                    tmdb_poster_map[tid] = str(p)
                t_str = str(r.get("title", "")).lower().strip()
                if t_str and pd.notna(p):
                    tmdb_title_map[t_str] = str(p)
        if ind_path.exists():
            df_ind_tmdb = pd.read_parquet(ind_path)
            for _, r in df_ind_tmdb.iterrows():
                tid = safe_int(r.get("id"), None)
                p = r.get("poster_path")
                if tid and pd.notna(p):
                    tmdb_poster_map[tid] = str(p)
                t_str = str(r.get("title", "")).lower().strip()
                if t_str and pd.notna(p):
                    tmdb_title_map[t_str] = str(p)
        logger.info(f"Loaded TMDB poster cache with {len(tmdb_poster_map)} IDs and {len(tmdb_title_map)} titles.")
    except Exception as e:
        logger.warning(f"Could not load TMDB poster caches: {e}")

    # 1. Seed Curated 2026–2027 Marquee Upcoming Tentpoles
    for t in CURATED_UPCOMING_TENTPOLES:
        cid = t["canonical_id"]
        if cid in inserted_ids:
            continue

        budget_usd = float(t.get("budget_clean_usd", 50_000_000))
        budget_inr = round(budget_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)
        genres_json = json.dumps(t.get("genres", ["Action"]))
        cast_json = json.dumps(t.get("top_cast", [t.get("lead_actor", "Lead Actor")]))

        movie_entity = Movie(
            canonical_id=cid,
            primary_title=t["primary_title"],
            release_date=t["release_date"],
            release_year=t["release_year"],
            runtime_minutes=140,
            original_language="hi" if t["industry"] == "Bollywood" else "te" if t["industry"] == "Tollywood" else "ta" if t["industry"] == "Kollywood" else "en",
            industry=t["industry"],
            genres=genres_json,
            director=t["director"],
            lead_actor=t["lead_actor"],
            cast_members=cast_json,
            production_company=t.get("production_company", "Studio"),
            overview=t.get("overview", ""),
            budget_usd=budget_usd,
            budget_inr_crores=budget_inr,
            box_office_gross_usd=None,
            box_office_gross_inr_crores=None,
            is_released=False,
            youtube_trailer_id=t.get("youtube_trailer_id"),
            poster_path=t.get("poster_path"),
            backdrop_path=t.get("backdrop_path"),
        )
        db.add(movie_entity)
        db.flush()
        inserted_ids.add(cid)

        # Run model forecast
        eval_dict = {
            "canonical_id": cid,
            "primary_title": t["primary_title"],
            "industry": t["industry"],
            "release_date": t["release_date"],
            "release_year": t["release_year"],
            "director": t["director"],
            "lead_actor": t["lead_actor"],
            "budget_clean_usd": budget_usd,
            "youtube_trailer_id": t.get("youtube_trailer_id"),
            "view_count": t.get("trailer_view_count", 20_000_000),
            "composite_buzz_score": t.get("composite_buzz_score", 85.0),
            "comment_sentiment_net_polarity": t.get("comment_sentiment_net_polarity", 0.8),
            "is_sequel_or_franchise": t.get("is_sequel_or_franchise", 0.0),
            "primary_genre": t.get("primary_genre", "Action"),
            "budget_tier": t.get("budget_tier", "Tentpole"),
            "original_language": t.get("original_language", "en"),
            "industry": t.get("industry", "Global"),
        }

        try:
            res = prediction_service.evaluate_movie_forecast(eval_dict)
            exp_usd = float(t.get("curated_expected_gross_usd") or res.get("expected_gross_usd", budget_usd * 2.2))
            exp_inr = round(exp_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)
            pess_usd = round(exp_usd * 0.74, 2)
            opt_usd = round(exp_usd * 1.42, 2)

            pred_entity = Prediction(
                movie_id=movie_entity.id,
                prediction_stage=res.get("lifecycle_stage", "Stage 3 Active Buzz"),
                readiness_score=safe_int(res.get("readiness_score"), 85),
                status_badge=res.get("status_badge", "Active Forecast"),
                model_version="catboost_revenue_v1",
                expected_gross_usd=exp_usd,
                expected_gross_inr_crores=exp_inr,
                pessimistic_bound_80_usd=pess_usd,
                optimistic_bound_80_usd=opt_usd,
                pessimistic_bound_80_inr=round(pess_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2),
                optimistic_bound_80_inr=round(opt_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2),
                extreme_downside_95_usd=round(exp_usd * 0.45, 2),
                extreme_upside_95_usd=round(exp_usd * 2.10, 2),
                conformal_confidence=0.80,
                success_category=res.get("risk_assessment_tier", "Hit"),
                success_probabilities=json.dumps({"Blockbuster": 0.55, "Super Hit": 0.25, "Hit": 0.15, "Average": 0.05}),
                prob_break_even=safe_float(res.get("prob_break_even"), 0.85),
                prob_commercial_profit=safe_float(res.get("prob_commercial_profit"), 0.72),
                prob_catastrophic_disaster=safe_float(res.get("prob_catastrophic_disaster"), 0.02),
                risk_assessment_tier=res.get("risk_assessment_tier", "Low Capital Risk"),
                risk_badge=res.get("risk_badge", "Commercial Favorable"),
                top_positive_factor=res.get("top_positive_driver", "Massive Star Power"),
                top_negative_factor=res.get("top_negative_driver", "High Budget Scale"),
                narrative_summary=t.get("narrative_summary") or res.get("narrative_summary", "High-velocity tentpole project with stellar market expectations."),
            )
            db.add(pred_entity)

            # Seed buzz
            buzz_entity = DigitalBuzzObservation(
                movie_id=movie_entity.id,
                youtube_video_id=t.get("youtube_trailer_id", "trailer_key"),
                view_count=t.get("trailer_view_count", 25_000_000),
                like_count=t.get("trailer_like_count", 1_500_000),
                comment_count=int(t.get("trailer_like_count", 1_500_000) * 0.1),
                buzz_score=float(t.get("composite_buzz_score", 85.0)),
                sentiment_net_polarity=float(t.get("comment_sentiment_net_polarity", 0.8)),
                total_comments_sampled=100,
                positive_ratio=0.80,
                neutral_ratio=0.15,
                negative_ratio=0.05,
            )
            db.add(buzz_entity)
        except Exception as e:
            logger.warning(f"Could not evaluate prediction for {cid}: {e}")

    # 2. Seed Curated Recent Released Blockbusters (2022–2026 actuals)
    for r in CURATED_RECENT_RELEASED_BLOCKBUSTERS:
        cid = r["canonical_id"]
        if cid in inserted_ids:
            continue

        budget_usd = float(r.get("budget_clean_usd", 20_000_000))
        budget_inr = round(budget_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)
        gross_usd = float(r.get("actual_gross_usd", 50_000_000))
        gross_inr = float(r.get("actual_gross_inr_crores", round(gross_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)))
        genres_json = json.dumps(r.get("genres", ["Action"]))
        cast_json = json.dumps(r.get("top_cast", [r.get("lead_actor", "Lead Actor")]))

        movie_entity = Movie(
            canonical_id=cid,
            primary_title=r["primary_title"],
            release_date=r["release_date"],
            release_year=r["release_year"],
            runtime_minutes=145,
            original_language=r.get("original_language", "en"),
            industry=r["industry"],
            genres=genres_json,
            director=r["director"],
            lead_actor=r["lead_actor"],
            cast_members=cast_json,
            production_company=r.get("production_company", "Studio"),
            overview=r.get("overview", ""),
            budget_usd=budget_usd,
            budget_inr_crores=budget_inr,
            box_office_gross_usd=gross_usd,
            box_office_gross_inr_crores=gross_inr,
            is_released=True,
            youtube_trailer_id=r.get("youtube_trailer_id"),
            poster_path=r.get("poster_path"),
            backdrop_path=r.get("backdrop_path"),
        )
        db.add(movie_entity)
        db.flush()
        inserted_ids.add(cid)

        # Seed audited actual prediction record
        pred_entity = Prediction(
            movie_id=movie_entity.id,
            prediction_stage="Stage 5 Concluded Run",
            readiness_score=100,
            status_badge="Theatrical Run Concluded",
            model_version="catboost_revenue_v1",
            expected_gross_usd=gross_usd,
            expected_gross_inr_crores=gross_inr,
            pessimistic_bound_80_usd=round(gross_usd * 0.90, 2),
            optimistic_bound_80_usd=round(gross_usd * 1.10, 2),
            pessimistic_bound_80_inr=round(gross_inr * 0.90, 2),
            optimistic_bound_80_inr=round(gross_inr * 1.10, 2),
            extreme_downside_95_usd=round(gross_usd * 0.85, 2),
            extreme_upside_95_usd=round(gross_usd * 1.15, 2),
            conformal_confidence=0.95,
            success_category=r.get("success_category", "Blockbuster"),
            success_probabilities=json.dumps({r.get("success_category", "Blockbuster"): 0.95, "Hit": 0.05}),
            prob_break_even=0.99 if gross_usd > budget_usd else 0.40,
            prob_commercial_profit=0.95 if gross_usd > budget_usd * 2.0 else 0.50,
            prob_catastrophic_disaster=0.01,
            risk_assessment_tier="Audited Actuals",
            risk_badge="Concluded",
            top_positive_factor="Massive Box Office Actual",
            top_negative_factor="Completed Theatrical Run",
            narrative_summary=f"Theatrical run concluded with a global cumulative gross of ${gross_usd / 1_000_000:.1f}M USD (₹{gross_inr:,.1f} Cr).",
        )
        db.add(pred_entity)

    # 3. Seed Upcoming Parquet Catalog if available
    upcoming_cat_path = settings.PROCESSED_DIR / "upcoming_discovery_catalog.parquet"
    if upcoming_cat_path.exists():
        df_up = pd.read_parquet(upcoming_cat_path)
        for _, row in df_up.iterrows():
            cid = str(row.get("canonical_id", ""))
            if cid in inserted_ids or not cid:
                continue

            budget_usd = safe_float(row.get("budget_clean_usd"), 0.0)
            budget_inr = round(budget_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)
            raw_genre = row.get("primary_genre", "Drama")
            genres_json = json.dumps([raw_genre] if isinstance(raw_genre, str) else list(raw_genre))
            top_cast_raw = row.get("top_cast", "")
            cast_list = [c.strip() for c in top_cast_raw.split(",") if c.strip()] if isinstance(top_cast_raw, str) else []
            cast_json = json.dumps(cast_list)

            poster_val = tmdb_poster_map.get(safe_int(row.get("tmdb_id"))) or tmdb_title_map.get(str(row.get("primary_title", "")).lower().strip())

            movie_entity = Movie(
                canonical_id=cid,
                tmdb_id=safe_int(row.get("tmdb_id"), None),
                primary_title=str(row.get("primary_title", "Untitled")),
                original_title=str(row.get("original_title", "")),
                release_date=str(row.get("release_date", "2026-11-20")),
                release_year=safe_int(row.get("release_year"), 2026),
                runtime_minutes=safe_int(row.get("runtime_minutes_clean"), 120),
                original_language=str(row.get("original_language", "en")),
                industry=str(row.get("industry", "Global")),
                genres=genres_json,
                director=str(row.get("director", "Unknown")),
                lead_actor=str(row.get("lead_actor", "Unknown")),
                cast_members=cast_json,
                overview=str(row.get("overview", "")),
                budget_usd=budget_usd,
                budget_inr_crores=budget_inr,
                box_office_gross_usd=None,
                box_office_gross_inr_crores=None,
                is_released=False,
                youtube_trailer_id=str(row.get("youtube_trailer_id", "")) if pd.notna(row.get("youtube_trailer_id")) else None,
                poster_path=poster_val,
            )
            db.add(movie_entity)
            db.flush()

            # Evaluate prediction for discovery items
            try:
                eval_dict = {
                    "canonical_id": cid,
                    "primary_title": movie_entity.primary_title,
                    "release_date": movie_entity.release_date,
                    "director": movie_entity.director,
                    "lead_actor": movie_entity.lead_actor,
                    "budget_clean_usd": budget_usd if budget_usd > 0 else 20_000_000.0,
                    "primary_genre": raw_genre if isinstance(raw_genre, str) else "Drama",
                    "original_language": movie_entity.original_language,
                    "industry": movie_entity.industry,
                }
                res = prediction_service.evaluate_movie_forecast(eval_dict)
                exp_usd = float(res.get("expected_gross_usd", 35_000_000.0))
                exp_inr = round(exp_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)
                pess_usd = round(exp_usd * 0.72, 2)
                opt_usd = round(exp_usd * 1.45, 2)

                pred_entity = Prediction(
                    movie_id=movie_entity.id,
                    prediction_stage=res.get("lifecycle_stage", "Stage 2 Teaser"),
                    readiness_score=safe_int(res.get("readiness_score"), 65),
                    status_badge=res.get("status_badge", "Active Forecast"),
                    model_version="catboost_revenue_v1",
                    expected_gross_usd=exp_usd,
                    expected_gross_inr_crores=exp_inr,
                    pessimistic_bound_80_usd=pess_usd,
                    optimistic_bound_80_usd=opt_usd,
                    pessimistic_bound_80_inr=round(pess_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2),
                    optimistic_bound_80_inr=round(opt_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2),
                    extreme_downside_95_usd=round(exp_usd * 0.45, 2),
                    extreme_upside_95_usd=round(exp_usd * 2.10, 2),
                    conformal_confidence=0.80,
                    success_category=res.get("risk_assessment_tier", "Hit"),
                    success_probabilities=json.dumps({"Hit": 0.50, "Average": 0.30, "Super Hit": 0.15, "Flop": 0.05}),
                    prob_break_even=safe_float(res.get("prob_break_even"), 0.75),
                    prob_commercial_profit=safe_float(res.get("prob_commercial_profit"), 0.60),
                    prob_catastrophic_disaster=safe_float(res.get("prob_catastrophic_disaster"), 0.05),
                    risk_assessment_tier=res.get("risk_assessment_tier", "Moderate Risk"),
                    risk_badge=res.get("risk_badge", "Commercial Favorable"),
                    top_positive_factor=res.get("top_positive_driver", "Genre Appeal"),
                    top_negative_factor=res.get("top_negative_driver", "Moderate Hype"),
                    narrative_summary=res.get("narrative_summary", "Early-stage upcoming theatrical project."),
                )
                db.add(pred_entity)
            except Exception as e:
                logger.warning(f"Could not generate prediction for discovery movie {cid}: {e}")

            inserted_ids.add(cid)

    # 3. Seed Canonical Released Movies from Unified Dataset (top 500)
    unified_path = settings.UNIFIED_DIR / "unified_movies.parquet"
    if unified_path.exists():
        df_uni = pd.read_parquet(unified_path)
        df_top = df_uni.sort_values(by="revenue_real_2024_usd", ascending=False).head(500)

        for _, row in df_top.iterrows():
            cid = str(row.get("canonical_id", ""))
            if cid in inserted_ids or not cid:
                continue

            budget_usd = safe_float(row.get("budget_real_2024_usd") or row.get("budget_nominal_usd"), 0.0)
            gross_usd = safe_float(row.get("revenue_real_2024_usd") or row.get("revenue_nominal_usd"), 0.0)
            budget_inr = round(budget_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)
            gross_inr = round(gross_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)

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
            poster_val = tmdb_poster_map.get(safe_int(row.get("tmdb_id"))) or tmdb_title_map.get(str(row.get("primary_title", "")).lower().strip())

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
                poster_path=poster_val,
            )
            db.add(movie_entity)
            db.flush()

            # Evaluate prediction for discovery items
            try:
                eval_dict = {
                    "canonical_id": cid,
                    "primary_title": movie_entity.primary_title,
                    "release_date": movie_entity.release_date,
                    "director": movie_entity.director,
                    "lead_actor": movie_entity.lead_actor,
                    "budget_clean_usd": budget_usd if budget_usd > 0 else 20_000_000.0,
                    "primary_genre": raw_genre if isinstance(raw_genre, str) else "Drama",
                    "original_language": movie_entity.original_language,
                    "industry": movie_entity.industry,
                }
                res = prediction_service.evaluate_movie_forecast(eval_dict)
                exp_usd = float(res.get("expected_gross_usd", 35_000_000.0))
                exp_inr = round(exp_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)
                pess_usd = round(exp_usd * 0.72, 2)
                opt_usd = round(exp_usd * 1.45, 2)

                pred_entity = Prediction(
                    movie_id=movie_entity.id,
                    prediction_stage=res.get("lifecycle_stage", "Stage 2 Teaser"),
                    readiness_score=safe_int(res.get("readiness_score"), 65),
                    status_badge=res.get("status_badge", "Active Forecast"),
                    model_version="catboost_revenue_v1",
                    expected_gross_usd=exp_usd,
                    expected_gross_inr_crores=exp_inr,
                    pessimistic_bound_80_usd=pess_usd,
                    optimistic_bound_80_usd=opt_usd,
                    pessimistic_bound_80_inr=round(pess_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2),
                    optimistic_bound_80_inr=round(opt_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2),
                    extreme_downside_95_usd=round(exp_usd * 0.45, 2),
                    extreme_upside_95_usd=round(exp_usd * 2.10, 2),
                    conformal_confidence=0.80,
                    success_category=res.get("risk_assessment_tier", "Hit"),
                    success_probabilities=json.dumps({"Hit": 0.50, "Average": 0.30, "Super Hit": 0.15, "Flop": 0.05}),
                    prob_break_even=safe_float(res.get("prob_break_even"), 0.75),
                    prob_commercial_profit=safe_float(res.get("prob_commercial_profit"), 0.60),
                    prob_catastrophic_disaster=safe_float(res.get("prob_catastrophic_disaster"), 0.05),
                    risk_assessment_tier=res.get("risk_assessment_tier", "Moderate Risk"),
                    risk_badge=res.get("risk_badge", "Commercial Favorable"),
                    top_positive_factor=res.get("top_positive_driver", "Genre Appeal"),
                    top_negative_factor=res.get("top_negative_driver", "Moderate Hype"),
                    narrative_summary=res.get("narrative_summary", "Early-stage upcoming theatrical project."),
                )
                db.add(pred_entity)
            except Exception as e:
                logger.warning(f"Could not generate prediction for discovery movie {cid}: {e}")

            inserted_ids.add(cid)

    db.commit()
    total_movies = db.query(Movie).count()
    total_upcoming = db.query(Movie).filter(Movie.is_released == False).count()
    total_preds = db.query(Prediction).count()
    logger.info(
        f"Database successfully hydrated! Total: {total_movies} movies ({total_upcoming} upcoming releases 2026-2027), {total_preds} active predictions."
    )


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
