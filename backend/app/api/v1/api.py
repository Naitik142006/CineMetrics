"""
CineMetrics — API v1 Master Router
Assembles and prefixes all v1 endpoints (health, movies, upcoming, predictions, simulation, analytics, admin).
"""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    auth,
    health,
    movies,
    upcoming,
    predictions,
    simulation,
    analytics,
    admin,
    sync,
)

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(health.router, tags=["Health & Governance"])
api_router.include_router(movies.router, tags=["Movie Catalog & Search"])
api_router.include_router(upcoming.router, tags=["Upcoming Releases & Intelligence"])
api_router.include_router(predictions.router, tags=["ML Predictions & Explainability"])
api_router.include_router(simulation.router, tags=["Counterfactual Simulation"])
api_router.include_router(analytics.router, tags=["Cinema Analytics & Talent Dossier"])
api_router.include_router(sync.router, tags=["Weekly Synchronization Pipeline"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administration & Operations"])

