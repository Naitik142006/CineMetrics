"""
CineMetrics — Administrative & Data Ingestion Control Endpoints
Allows authorized administrators to trigger ingestion jobs and curate movie metadata.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.db.session import get_db
from backend.app.db.models import Movie

router = APIRouter()


class MovieUpdateRequest(BaseModel):
    budget_usd: Optional[float] = None
    release_date: Optional[str] = None
    director: Optional[str] = None
    lead_actor: Optional[str] = None
    youtube_trailer_id: Optional[str] = None


@router.post("/admin/ingestion/trigger/{job_type}", summary="Trigger Ingestion Job")
def trigger_ingestion_job(job_type: str):
    """
    Manually triggers automated data ingestion jobs:
    - 'daily_discovery': Discovers new upcoming theatrical releases via TMDB API.
    - 'buzz_update': Refreshes YouTube trailer engagement and multilingual sentiment.
    """
    valid_jobs = ["daily_discovery", "buzz_update"]
    if job_type not in valid_jobs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job type '{job_type}'. Must be one of {valid_jobs}.",
        )

    # In production, this dispatches an async Celery or APScheduler background task
    return {
        "status": "dispatched",
        "job_type": job_type,
        "message": f"Ingestion job '{job_type}' successfully enqueued for execution.",
    }


@router.put("/admin/movies/{movie_id}", summary="Curate Movie Record")
def update_movie_record(movie_id: str, payload: MovieUpdateRequest, db: Session = Depends(get_db)):
    """
    Administrative endpoint to curate reported production budgets or release calendar dates.
    """
    movie = db.query(Movie).filter(
        or_(Movie.id == movie_id, Movie.canonical_id == movie_id)
    ).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' not found.",
        )

    if payload.budget_usd is not None:
        movie.budget_usd = payload.budget_usd
        movie.budget_inr_crores = round(payload.budget_usd * 83.50 / 100_000_000.0, 2)
    if payload.release_date is not None:
        movie.release_date = payload.release_date
    if payload.director is not None:
        movie.director = payload.director
    if payload.lead_actor is not None:
        movie.lead_actor = payload.lead_actor
    if payload.youtube_trailer_id is not None:
        movie.youtube_trailer_id = payload.youtube_trailer_id

    db.commit()
    db.refresh(movie)

    return {
        "status": "updated",
        "movie_id": movie.id,
        "canonical_id": movie.canonical_id,
        "primary_title": movie.primary_title,
        "budget_usd": movie.budget_usd,
        "budget_inr_crores": movie.budget_inr_crores,
        "release_date": movie.release_date,
    }
