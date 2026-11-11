"""
CineMetrics — Automated Weekly Data Synchronization Pipeline
Provides automated weekly sync across OMDb, trailer velocity tracking, release date monitoring,
and continuous prediction recalibration with immutable audit logging.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.models import Movie, Prediction, DigitalBuzzObservation, PredictionHistoryRecord
from backend.app.services.omdb_service import omdb_service
from backend.app.services.prediction_service import prediction_service

logger = logging.getLogger("WeeklySyncService")

SYNC_STATUS_FILE = settings.PROCESSED_DIR / "sync_status.json"
SYNC_INTERVAL_DAYS = 7


class WeeklySyncService:
    def __init__(self):
        self.is_running: bool = False
        self._ensure_status_file()

    def _ensure_status_file(self):
        """Initializes sync status file if not already present."""
        if not SYNC_STATUS_FILE.exists():
            default_status = {
                "last_sync_timestamp": datetime.now(timezone.utc).isoformat(),
                "next_scheduled_sync": (datetime.now(timezone.utc) + timedelta(days=SYNC_INTERVAL_DAYS)).isoformat(),
                "sync_interval_days": SYNC_INTERVAL_DAYS,
                "status": "IDLE",
                "total_movies_checked": 0,
                "movies_updated": 0,
                "posters_updated": 0,
                "dates_updated": 0,
                "box_office_actuals_updated": 0,
                "predictions_recalibrated": 0,
                "recent_events": [
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event": "Pipeline initialized with weekly synchronization cadence.",
                    }
                ],
            }
            with open(SYNC_STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_status, f, indent=2)

    def get_sync_status(self) -> Dict[str, Any]:
        """Reads current sync status metadata."""
        self._ensure_status_file()
        try:
            with open(SYNC_STATUS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["is_running"] = self.is_running
            return data
        except Exception as e:
            logger.error(f"Error reading sync status file: {e}")
            return {
                "last_sync_timestamp": None,
                "next_scheduled_sync": None,
                "status": "ERROR",
                "error": str(e),
                "is_running": self.is_running,
            }

    def _save_sync_status(self, status_data: Dict[str, Any]):
        """Persists updated sync status."""
        try:
            with open(SYNC_STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sync status: {e}")

    def run_sync(self, db: Session, force: bool = False, max_titles: int = 50) -> Dict[str, Any]:
        """
        Executes a weekly sync cycle:
        1. Checks whether 7 days have elapsed (unless force=True).
        2. Iterates over upcoming movies and recently released tentpoles.
        3. Queries OMDb API for latest posters, release dates, and theatrical box office actuals.
        4. Simulates/tracks weekly trailer view momentum and updates digital buzz observations.
        5. Recalibrates predictions when new info arrives and appends immutable audit records.
        """
        if self.is_running:
            return {"status": "SKIPPED", "message": "Sync cycle already currently in progress."}

        current_status = self.get_sync_status()
        now = datetime.now(timezone.utc)

        # Check time interval
        last_str = current_status.get("last_sync_timestamp")
        if not force and last_str:
            try:
                last_dt = datetime.fromisoformat(last_str)
                if now - last_dt < timedelta(days=SYNC_INTERVAL_DAYS):
                    remaining_days = round((timedelta(days=SYNC_INTERVAL_DAYS) - (now - last_dt)).total_seconds() / 86400.0, 1)
                    return {
                        "status": "IDLE",
                        "message": f"Weekly sync not due yet. Next scheduled run in {remaining_days} days.",
                        "last_sync": last_str,
                        "next_sync": current_status.get("next_scheduled_sync"),
                    }
            except Exception:
                pass

        self.is_running = True
        logger.info(f"Starting CineMetrics weekly data synchronization (force={force})...")

        posters_updated = 0
        dates_updated = 0
        actuals_updated = 0
        predictions_recalibrated = 0
        movies_scanned = 0
        events: List[Dict[str, Any]] = []

        try:
            # Query candidate movies: Prioritize upcoming release-week (nearest dated) titles first
            upcoming_movies = (
                db.query(Movie)
                .filter(Movie.is_released == False)
                .order_by(Movie.release_date.is_(None), Movie.release_date)
                .limit(max_titles)
                .all()
            )
            recent_movies = db.query(Movie).filter(Movie.is_released == True).order_by(Movie.release_date.desc()).limit(20).all()
            candidate_movies = upcoming_movies + recent_movies

            today_iso = datetime.now().strftime("%Y-%m-%d")

            for movie in candidate_movies:
                movies_scanned += 1
                movie_changed = False
                change_notes: List[str] = []

                # Check for theatrical release transition against current system date
                if not movie.is_released and movie.release_date and str(movie.release_date).split("T")[0] <= today_iso:
                    movie.is_released = True
                    movie_changed = True
                    change_notes.append("Theatrical release date reached; transitioned to released catalog")

                # 1. Query OMDb API for latest authoritative information
                omdb_info = omdb_service.fetch_movie_by_title(movie.primary_title, movie.release_year)

                if omdb_info:
                    raw_omdb_year = str(omdb_info.get("year") or "")[:4]
                    if raw_omdb_year.isdigit() and movie.release_year and abs(int(raw_omdb_year) - int(movie.release_year)) > 2:
                        logger.info(
                            f"Ignoring mismatched OMDb record for '{movie.primary_title}': "
                            f"OMDb year {raw_omdb_year} vs tracked year {movie.release_year}"
                        )
                        omdb_info = None

                if omdb_info:
                    # Only backfill Poster from OMDb for released movies with no TMDB poster
                    if movie.is_released and not movie.poster_path and omdb_info.get("poster_url"):
                        new_poster = omdb_info["poster_url"]
                        if new_poster != movie.poster_path:
                            movie.poster_path = new_poster
                            posters_updated += 1
                            movie_changed = True
                            change_notes.append("Official IMDb theatrical poster linked")

                    # Check for Plot / Overview
                    if not movie.overview and omdb_info.get("plot"):
                        movie.overview = omdb_info["plot"]
                        movie_changed = True

                    # Check for Release Date shifts
                    omdb_date = omdb_info.get("released_date")
                    if omdb_date:
                        try:
                            # OMDb returns e.g. "20 Jul 2026" or "N/A"
                            parsed_date = datetime.strptime(omdb_date, "%d %b %Y").strftime("%Y-%m-%d")
                            parsed_year = int(parsed_date[:4])
                            # Guard against OMDb fuzzy fallback matching an unrelated legacy film from a different decade
                            if movie.release_year and abs(parsed_year - int(movie.release_year)) > 2:
                                logger.info(
                                    f"Skipping OMDb release date shift for '{movie.primary_title}': "
                                    f"OMDb returned {parsed_date} vs tracked year {movie.release_year}"
                                )
                            elif parsed_date != movie.release_date:
                                old_d = movie.release_date
                                movie.release_date = parsed_date
                                movie.release_year = parsed_year
                                dates_updated += 1
                                movie_changed = True
                                change_notes.append(f"Release date shifted from {old_d} to {parsed_date}")
                        except Exception:
                            pass

                    # Check for theatrical release transition & box office actuals
                    if not movie.is_released and movie.release_date and movie.release_date <= today_iso:
                        movie.is_released = True
                        movie_changed = True
                        change_notes.append("Theatrical release date reached; transitioned to active cinema run")

                    # Update Box Office Actuals if movie is released and OMDb has gross
                    if movie.is_released and omdb_info.get("box_office_usd"):
                        omdb_gross = omdb_info["box_office_usd"]
                        if not movie.box_office_gross_usd or abs(omdb_gross - movie.box_office_gross_usd) > 10_000:
                            movie.box_office_gross_usd = omdb_gross
                            movie.box_office_gross_inr_crores = round(omdb_gross * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)
                            actuals_updated += 1
                            movie_changed = True
                            change_notes.append(f"Box office actual updated: ${omdb_gross / 1_000_000:.1f}M USD")

                # 2. Check & Update Real YouTube Trailer Views (when valid 11-char ID exists)
                buzz = db.query(DigitalBuzzObservation).filter(DigitalBuzzObservation.movie_id == movie.id).first()
                if buzz and movie.youtube_trailer_id:
                    from backend.app.services.advance_booking_service import fetch_youtube_view_count
                    live_views = fetch_youtube_view_count(movie.youtube_trailer_id)
                    if live_views is not None and live_views > 0 and live_views != buzz.view_count:
                        view_delta = live_views - (buzz.view_count or 0)
                        buzz.view_count = live_views
                        buzz.observed_at = now
                        change_notes.append(f"Live trailer views synced ({view_delta:+,} delta)")
                        movie_changed = True

                # 3. Check if movie is in Stage 4 Release-Week window (1..7 days to release)
                days_to_rel = None
                if not movie.is_released and movie.release_date and str(movie.release_date).strip() not in ("None", "TBD", ""):
                    try:
                        rdt = datetime.fromisoformat(str(movie.release_date).split("T")[0]).date()
                        days_to_rel = (rdt - datetime.now(timezone.utc).date()).days
                    except Exception:
                        days_to_rel = None

                if not movie.is_released and days_to_rel is not None and 0 < days_to_rel <= 7:
                    from backend.app.services.advance_booking_service import sync_stage4_for_movie
                    pred_record = db.query(Prediction).filter(Prediction.movie_id == movie.id).first()
                    sync_stage4_for_movie(db, movie, prediction=pred_record, fetch_live=True, persist=True)
                    change_notes.append(f"Auto Stage 4 live recalibration executed (T-{days_to_rel}d)")
                    predictions_recalibrated += 1
                elif movie_changed or not movie.is_released:
                    # Standard Stage 1-3 recalibration when metadata changed or movie is >7d out
                    pred_record = db.query(Prediction).filter(Prediction.movie_id == movie.id).first()
                    
                    movie_dict = {
                        "canonical_id": movie.canonical_id,
                        "primary_title": movie.primary_title,
                        "release_date": movie.release_date,
                        "release_year": movie.release_year,
                        "industry": movie.industry,
                        "genres": movie.genres,
                        "director": movie.director,
                        "lead_actor": movie.lead_actor,
                        "budget_usd": movie.budget_usd,
                        "youtube_trailer_id": movie.youtube_trailer_id,
                        "trailer_view_count": buzz.view_count if buzz else 0,
                        "comment_sentiment_net_polarity": buzz.sentiment_net_polarity if buzz else 0.5,
                    }

                    prev_pred_dict = {
                        "expected_gross_usd": pred_record.expected_gross_usd if pred_record else None,
                        "youtube_trailer_id": movie.youtube_trailer_id,
                    } if pred_record else None

                    new_forecast = prediction_service.evaluate_movie_forecast(movie_dict, previous_prediction=prev_pred_dict)

                    if new_forecast.get("expected_gross_usd"):
                        exp_usd = new_forecast["expected_gross_usd"]
                        exp_inr = round(exp_usd * settings.DEFAULT_INR_USD_RATE / 10_000_000.0, 2)

                        if pred_record:
                            pred_record.expected_gross_usd = exp_usd
                            pred_record.expected_gross_inr_crores = exp_inr
                            pred_record.pessimistic_bound_80_usd = round(exp_usd * 0.70, 2)
                            pred_record.optimistic_bound_80_usd = round(exp_usd * 1.45, 2)
                            pred_record.pessimistic_bound_80_inr = round(exp_inr * 0.70, 2)
                            pred_record.optimistic_bound_80_inr = round(exp_inr * 1.45, 2)
                            pred_record.extreme_downside_95_usd = round(exp_usd * 0.45, 2)
                            pred_record.extreme_upside_95_usd = round(exp_usd * 2.10, 2)
                            pred_record.readiness_score = new_forecast["readiness_score"]
                            pred_record.status_badge = new_forecast["status_badge"]
                            pred_record.evaluated_at = now
                        else:
                            pred_record = Prediction(
                                movie_id=movie.id,
                                prediction_stage=new_forecast["lifecycle_stage"],
                                readiness_score=new_forecast["readiness_score"],
                                status_badge=new_forecast["status_badge"],
                                model_version="catboost_revenue_v1",
                                expected_gross_usd=exp_usd,
                                expected_gross_inr_crores=exp_inr,
                                pessimistic_bound_80_usd=round(exp_usd * 0.70, 2),
                                optimistic_bound_80_usd=round(exp_usd * 1.45, 2),
                                pessimistic_bound_80_inr=round(exp_inr * 0.70, 2),
                                optimistic_bound_80_inr=round(exp_inr * 1.45, 2),
                                success_category="Hit",
                                risk_assessment_tier=new_forecast.get("risk_assessment_tier", "Moderate Risk"),
                                risk_badge=new_forecast.get("risk_badge", "Favorable"),
                            )
                            db.add(pred_record)

                        # Record prediction history
                        delta_usd = new_forecast["delta_tracking"]["delta_usd"] if "delta_tracking" in new_forecast else 0.0
                        delta_pct = new_forecast["delta_tracking"]["delta_pct"] if "delta_tracking" in new_forecast else 0.0
                        attr_text = "; ".join(change_notes) if change_notes else "Weekly automated model recalibration"

                        hist = PredictionHistoryRecord(
                            movie_id=movie.id,
                            prediction_stage=new_forecast["lifecycle_stage"],
                            readiness_score=new_forecast["readiness_score"],
                            expected_gross_usd=exp_usd,
                            delta_usd=delta_usd,
                            delta_pct=delta_pct,
                            change_attribution=f"Weekly Sync: {attr_text}",
                            evaluated_at=now,
                        )
                        db.add(hist)
                        predictions_recalibrated += 1

                if change_notes:
                    events.append({
                        "title": movie.primary_title,
                        "timestamp": now.isoformat(),
                        "notes": change_notes,
                    })

            db.commit()

            # Record success in status file
            updated_status = {
                "last_sync_timestamp": now.isoformat(),
                "next_scheduled_sync": (now + timedelta(days=SYNC_INTERVAL_DAYS)).isoformat(),
                "sync_interval_days": SYNC_INTERVAL_DAYS,
                "status": "SUCCESS",
                "total_movies_checked": movies_scanned,
                "movies_updated": len(events),
                "posters_updated": posters_updated,
                "dates_updated": dates_updated,
                "box_office_actuals_updated": actuals_updated,
                "predictions_recalibrated": predictions_recalibrated,
                "recent_events": events[:20] if events else current_status.get("recent_events", []),
            }
            self._save_sync_status(updated_status)
            logger.info(
                f"Weekly sync completed successfully: {movies_scanned} movies scanned, "
                f"{len(events)} updated, {posters_updated} posters, {dates_updated} dates, "
                f"{predictions_recalibrated} predictions recalibrated."
            )

            return {
                "status": "SUCCESS",
                "summary": {
                    "movies_scanned": movies_scanned,
                    "movies_updated": len(events),
                    "posters_updated": posters_updated,
                    "dates_updated": dates_updated,
                    "box_office_actuals_updated": actuals_updated,
                    "predictions_recalibrated": predictions_recalibrated,
                    "completed_at": now.isoformat(),
                    "next_sync": (now + timedelta(days=SYNC_INTERVAL_DAYS)).isoformat(),
                },
                "events_sample": events[:5],
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Weekly sync failed with error: {e}", exc_info=True)
            current_status["status"] = "ERROR"
            current_status["last_error"] = str(e)
            current_status["last_error_time"] = now.isoformat()
            self._save_sync_status(current_status)
            return {"status": "ERROR", "error": str(e)}

        finally:
            self.is_running = False


# Singleton instance
weekly_sync_service = WeeklySyncService()
