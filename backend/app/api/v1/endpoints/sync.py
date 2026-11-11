"""
CineMetrics — Automated Synchronization & Data Refresh Endpoints
Exposes API routes to inspect weekly synchronization status, trigger manual refreshes,
and monitor continuous OMDb / digital momentum recalibrations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.db.models import AdvanceBookingObservation, Movie
from backend.app.db.session import SessionLocal, get_db
from backend.app.services.advance_booking_service import resolve_screen_and_atp, sync_stage4_for_movie
from backend.app.services.weekly_sync_service import weekly_sync_service

router = APIRouter(prefix="/sync", tags=["Weekly Synchronization Pipeline"])


@router.get("/status", summary="Get Weekly Synchronization Status")
def get_sync_status() -> Dict[str, Any]:
    """
    Returns the current state of the weekly data synchronization engine:
    - Last sync timestamp & next scheduled run (+7 days)
    - Total movies scanned, posters updated, release dates adjusted
    - Box office actuals updated & predictions recalibrated
    - Running status (IDLE / SYNCING / SUCCESS / ERROR)
    """
    return weekly_sync_service.get_sync_status()


def _run_background_sync(force: bool, max_titles: int):
    """Worker task executed in background thread with isolated DB session."""
    db = SessionLocal()
    try:
        weekly_sync_service.run_sync(db=db, force=force, max_titles=max_titles)
    finally:
        db.close()


@router.post("/trigger", summary="Trigger Data Synchronization Run")
def trigger_sync(
    force: bool = Query(True, description="Force sync immediately even if 7 days have not elapsed"),
    max_titles: int = Query(50, ge=1, le=200, description="Maximum candidate movies to inspect"),
    async_mode: bool = Query(False, description="Execute asynchronously in background"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Triggers a data synchronization cycle:
    - Queries OMDb for newly published posters, release date changes, and box office actuals.
    - Updates YouTube trailer views, comment velocity, and buzz scores.
    - Recalibrates machine learning forecasts for active movies with new information.
    """
    if weekly_sync_service.is_running:
        return {
            "status": "ALREADY_RUNNING",
            "message": "A synchronization run is already actively executing.",
        }

    if async_mode:
        background_tasks.add_task(_run_background_sync, force, max_titles)
        return {
            "status": "QUEUED",
            "message": "Synchronization task dispatched to background worker.",
        }

    # Synchronous execution
    result = weekly_sync_service.run_sync(db=db, force=force, max_titles=max_titles)
    return result


class TicketFeedRecord(BaseModel):
    movie_id_or_title: str = Field(..., description="Movie UUID, canonical_id, or exact title")
    advance_tickets_sold: int = Field(..., ge=100, description="Confirmed advance tickets sold")
    average_ticket_price_usd: Optional[float] = Field(None, gt=0)
    hours_to_release: int = Field(24, ge=1, le=168)
    screen_count: Optional[int] = Field(None, ge=100)
    early_critic_score_pct: Optional[float] = Field(None, ge=0, le=100)


class BatchAdvanceBookingIngest(BaseModel):
    records: List[TicketFeedRecord]


@router.post("/advance-bookings", summary="Ingest Verified Advance Booking Feed & Recalibrate Stage 4")
def ingest_advance_booking_feed(
    payload: BatchAdvanceBookingIngest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Accepts confirmed ticketing numbers from external ticketing partners or trade feeds,
    stores verified observations, and automatically updates Stage 4 Bayesian forecasts.
    """
    updated: List[Dict[str, Any]] = []
    unmatched: List[str] = []
    now = datetime.now(timezone.utc)

    for rec in payload.records:
        key = rec.movie_id_or_title.strip()
        movie = (
            db.query(Movie)
            .filter(
                or_(
                    Movie.id == key,
                    Movie.canonical_id == key,
                    Movie.primary_title.ilike(key),
                )
            )
            .first()
        )
        if not movie:
            unmatched.append(key)
            continue

        def_screens, def_atp = resolve_screen_and_atp(movie.industry or "Global", movie.budget_usd or 0.0)
        db.add(
            AdvanceBookingObservation(
                movie_id=movie.id,
                signal_source="verified_ticketing",
                advance_tickets_sold=rec.advance_tickets_sold,
                average_ticket_price_usd=rec.average_ticket_price_usd or def_atp,
                hours_to_release=rec.hours_to_release,
                screen_count=rec.screen_count or def_screens,
                early_critic_score_pct=rec.early_critic_score_pct,
                observed_at=now,
            )
        )
        db.flush()
        stage4_res = sync_stage4_for_movie(db, movie, fetch_live=False, persist=True)
        updated.append(
            {
                "movie_id": movie.id,
                "title": movie.primary_title,
                "advance_tickets_sold": rec.advance_tickets_sold,
                "posterior_expected_gross_usd": stage4_res["bayesian_posterior"]["posterior_expected_gross_usd"],
            }
        )

    return {
        "status": "OK",
        "recalibrated_count": len(updated),
        "unmatched": unmatched,
        "updated_movies": updated,
    }

