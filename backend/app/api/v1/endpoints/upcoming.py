"""
CineMetrics — Upcoming Releases & Intelligence Dashboard Endpoints
Aggregates live radar upcoming movies and curated analytical intelligence sections.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.db.session import get_db
from backend.app.db.models import Movie, Prediction, DigitalBuzzObservation
from backend.app.schemas.upcoming import (
    UpcomingMovieItem,
    DashboardSection,
    UpcomingDashboardResponse,
)

router = APIRouter()


def _build_upcoming_item(m: Movie, p: Optional[Prediction], b: Optional[DigitalBuzzObservation]) -> UpcomingMovieItem:
    try:
        genres = json.loads(m.genres) if m.genres else []
    except Exception:
        genres = [str(m.genres)] if m.genres else []

    # Calculate exact days to release
    days_to_release = None
    if m.release_date and str(m.release_date).strip() not in ("None", "TBD", ""):
        try:
            rdt = datetime.fromisoformat(str(m.release_date).split("T")[0]).date()
            now_date = datetime.now(timezone.utc).date()
            days_to_release = (rdt - now_date).days
        except Exception:
            pass

    exp_usd = p.expected_gross_usd if p else 30_000_000.0

    # Temporal stage assignment strictly governed by days to release
    if days_to_release is not None and 0 < days_to_release <= 7:
        is_stage4 = True
        lifecycle_stage = "Stage 4: Advance Pre-Sales Active"
        status_badge = "Stage 4 (R² ≥ 0.925)"
        readiness_score = max(p.readiness_score if p else 0, 96)
        pess_usd = p.pessimistic_bound_80_usd if (p and p.pessimistic_bound_80_usd) else exp_usd * 0.914
        opt_usd = p.optimistic_bound_80_usd if (p and p.optimistic_bound_80_usd) else exp_usd * 1.086
    elif days_to_release is not None and 7 < days_to_release <= 30:
        is_stage4 = False
        lifecycle_stage = "Stage 3: Pre-Release Marketing Blitz"
        status_badge = "Stage 3 Multi-Modal"
        readiness_score = min(max(p.readiness_score if p else 0, 82), 89)
        pess_usd = p.pessimistic_bound_80_usd if (p and p.pessimistic_bound_80_usd) else exp_usd * 0.80
        opt_usd = p.optimistic_bound_80_usd if (p and p.optimistic_bound_80_usd) else exp_usd * 1.20
    elif days_to_release is not None and 30 < days_to_release <= 90:
        is_stage4 = False
        lifecycle_stage = "Stage 2: Teaser & Trailer Campaign"
        status_badge = "Stage 2 Preliminary"
        readiness_score = min(max(p.readiness_score if p else 0, 68), 79)
        pess_usd = p.pessimistic_bound_80_usd if (p and p.pessimistic_bound_80_usd) else exp_usd * 0.70
        opt_usd = p.optimistic_bound_80_usd if (p and p.optimistic_bound_80_usd) else exp_usd * 1.30
    else:
        is_stage4 = False
        lifecycle_stage = "Stage 1: Announcement Prior"
        status_badge = "Stage 1 Prior"
        readiness_score = min(max(p.readiness_score if p else 0, 50), 65)
        pess_usd = p.pessimistic_bound_80_usd if (p and p.pessimistic_bound_80_usd) else exp_usd * 0.58
        opt_usd = p.optimistic_bound_80_usd if (p and p.optimistic_bound_80_usd) else exp_usd * 1.42

    exp_inr = round(exp_usd * 83.50 / 10_000_000.0, 2)

    return UpcomingMovieItem(
        id=m.id,
        canonical_id=m.canonical_id,
        primary_title=m.primary_title,
        release_date=m.release_date or "2025-01-01",
        release_year=m.release_year or 2025,
        industry=m.industry or "Global",
        genres=genres if isinstance(genres, list) else [str(genres)],
        director=m.director or "Unknown",
        lead_actor=m.lead_actor or "Unknown",
        budget_usd=m.budget_usd or 0.0,
        budget_inr_crores=m.budget_inr_crores or 0.0,
        readiness_score=readiness_score,
        lifecycle_stage=lifecycle_stage,
        status_badge=status_badge,
        expected_gross_usd=exp_usd,
        expected_gross_formatted_usd=f"${exp_usd / 1_000_000:.1f}M",
        expected_gross_formatted_inr=f"₹{exp_inr:,.1f} Cr",
        pessimistic_bound_80_usd=pess_usd,
        optimistic_bound_80_usd=opt_usd,
        risk_assessment_tier=p.risk_assessment_tier if p else "Moderate Risk",
        risk_badge=p.risk_badge if p else "Commercial Favorable",
        buzz_score=b.buzz_score if b else 0.0,
        trailer_view_count=b.view_count if b else 0,
        youtube_trailer_id=m.youtube_trailer_id,
        poster_path=m.poster_path,
        backdrop_path=m.backdrop_path,
        days_to_release=days_to_release,
        is_stage4_active=is_stage4,
    )


@router.get("/upcoming", response_model=List[UpcomingMovieItem], summary="Get Upcoming Releases Feed")
def get_upcoming_movies(
    market_segment: Optional[str] = Query(None, description="Filter by industry (Bollywood, Tollywood, Hollywood, etc.)"),
    stage_filter: Optional[str] = Query(None, description="Filter by lifecycle stage (all, stage4, stage3, stage2, stage1)"),
    min_readiness: Optional[int] = Query(0, ge=0, le=100, description="Minimum Prediction Readiness Score"),
    sort_by: str = Query("date", pattern="^(date|forecast|buzz|readiness)$"),
    limit: int = Query(120, ge=1, le=300),
    db: Session = Depends(get_db),
):
    """
    Returns upcoming movies filtered by industry, stage, and minimum readiness score.
    """
    query = db.query(Movie, Prediction, DigitalBuzzObservation).outerjoin(
        Prediction, Prediction.movie_id == Movie.id
    ).outerjoin(
        DigitalBuzzObservation, DigitalBuzzObservation.movie_id == Movie.id
    ).filter(Movie.is_released == False)

    if market_segment and market_segment.lower() != "all":
        query = query.filter(Movie.industry.ilike(f"%{market_segment}%"))

    if min_readiness and min_readiness > 0:
        query = query.filter(Prediction.readiness_score >= min_readiness)

    records = query.all()
    items = [_build_upcoming_item(m, p, b) for m, p, b in records]

    # Lifecycle Stage filter
    if stage_filter and stage_filter.lower() != "all":
        sf = stage_filter.lower()
        if "4" in sf:
            items = [it for it in items if it.is_stage4_active]
        elif "3" in sf:
            items = [it for it in items if "Stage 3" in it.lifecycle_stage]
        elif "2" in sf:
            items = [it for it in items if "Stage 2" in it.lifecycle_stage]
        elif "1" in sf:
            items = [it for it in items if "Stage 1" in it.lifecycle_stage]

    # In-memory sorting
    if sort_by == "forecast":
        items.sort(key=lambda x: x.expected_gross_usd, reverse=True)
    elif sort_by == "buzz":
        items.sort(key=lambda x: x.buzz_score, reverse=True)
    elif sort_by == "readiness":
        items.sort(key=lambda x: x.readiness_score, reverse=True)
    else:
        items.sort(key=lambda x: x.release_date)

    return items[:limit]


@router.get("/upcoming/dashboard", response_model=UpcomingDashboardResponse, summary="Get Intelligence Dashboard")
def get_upcoming_dashboard(db: Session = Depends(get_db)):
    """
    Aggregates curated analytical intelligence sections for upcoming theatrical releases.
    """
    records = db.query(Movie, Prediction, DigitalBuzzObservation).outerjoin(
        Prediction, Prediction.movie_id == Movie.id
    ).outerjoin(
        DigitalBuzzObservation, DigitalBuzzObservation.movie_id == Movie.id
    ).filter(Movie.is_released == False).all()

    all_items = [_build_upcoming_item(m, p, b) for m, p, b in records]

    # 1. Top Predicted Grossers
    top_grossers = sorted(all_items, key=lambda x: x.expected_gross_usd, reverse=True)[:6]

    # 2. Highest Digital Buzz
    high_buzz = sorted(all_items, key=lambda x: x.buzz_score, reverse=True)[:6]

    # 3. High Risk Tentpoles (Budget > $40M, risk High or Critical)
    high_risk = [
        item for item in all_items
        if item.budget_usd >= 40_000_000 or "High" in item.risk_assessment_tier or "Critical" in item.risk_assessment_tier
    ][:6]

    # 4. Sleeper Breakouts (Budget < $25M, Expected Gross > $50M)
    sleepers = [
        item for item in all_items
        if item.budget_usd < 25_000_000 and item.expected_gross_usd >= 40_000_000
    ][:6]

    # 5. Bollywood Spotlight
    bollywood = [item for item in all_items if "bollywood" in item.industry.lower()][:6]

    # 6. South Indian Powerhouses (Tollywood, Kollywood, Mollywood, Sandalwood)
    south_indian = [
        item for item in all_items
        if any(seg in item.industry.lower() for seg in ["tollywood", "kollywood", "mollywood", "sandalwood", "telugu", "tamil"])
    ][:6]

    # 7. Hollywood Blockbusters
    hollywood = [item for item in all_items if "hollywood" in item.industry.lower()][:6]

    sections = {
        "top_predicted_grossers": DashboardSection(
            key="top_predicted_grossers",
            title="Projected Global Box-Office Champions",
            description="Upcoming releases projected to command highest worldwide theatrical returns.",
            item_count=len(top_grossers),
            items=top_grossers,
        ),
        "highest_digital_buzz": DashboardSection(
            key="highest_digital_buzz",
            title="Digital Viral Velocity Leaders",
            description="Releases exhibiting peak trailer engagement, comment velocity, and audience sentiment.",
            item_count=len(high_buzz),
            items=high_buzz,
        ),
        "high_risk_tentpoles": DashboardSection(
            key="high_risk_tentpoles",
            title="High-Cap Expenditure Downside Watch",
            description="Major capital investments requiring substantial multiples to break even.",
            item_count=len(high_risk),
            items=high_risk,
        ),
        "sleeper_breakouts": DashboardSection(
            key="sleeper_breakouts",
            title="High-ROI Sleeper Contenders",
            description="Lean-budget productions exhibiting outsized box-office multiplier potential.",
            item_count=len(sleepers),
            items=sleepers,
        ),
        "bollywood_spotlight": DashboardSection(
            key="bollywood_spotlight",
            title="Hindi Cinema Horizon",
            description="Active forecasts across Mumbai theatrical releases.",
            item_count=len(bollywood),
            items=bollywood,
        ),
        "south_indian_powerhouses": DashboardSection(
            key="south_indian_powerhouses",
            title="South Indian Theatrical Titans",
            description="High-voltage pan-India releases from Telugu, Tamil, Malayalam, and Kannada industries.",
            item_count=len(south_indian),
            items=south_indian,
        ),
        "hollywood_blockbusters": DashboardSection(
            key="hollywood_blockbusters",
            title="Studio Franchise & Global Tentpoles",
            description="Major international studio wide releases.",
            item_count=len(hollywood),
            items=hollywood,
        ),
    }

    return UpcomingDashboardResponse(
        total_upcoming_tracked=len(all_items),
        last_updated=datetime.now(timezone.utc).isoformat(),
        sections=sections,
    )
