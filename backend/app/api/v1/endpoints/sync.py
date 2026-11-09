"""
CineMetrics — Automated Synchronization & Data Refresh Endpoints
Exposes API routes to inspect weekly synchronization status, trigger manual refreshes,
and monitor continuous OMDb / digital momentum recalibrations.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session

from backend.app.db.session import get_db, SessionLocal
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

