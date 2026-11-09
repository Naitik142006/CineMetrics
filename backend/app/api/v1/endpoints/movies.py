"""
CineMetrics — Movie Catalog, Search & Similarity Endpoints
Provides debounced full-text search, detailed dossiers, and similar movie embeddings.
"""

import time
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from backend.app.db.session import get_db
from backend.app.db.models import Movie, Prediction, DigitalBuzzObservation
from backend.app.schemas.movie import (
    MovieSummary,
    MovieDetail,
    SimilarMovie,
    MovieSearchResponse,
)

router = APIRouter()


def _format_movie_summary(m: Movie) -> MovieSummary:
    try:
        genres = json.loads(m.genres) if m.genres else []
    except Exception:
        genres = [str(m.genres)] if m.genres else []

    return MovieSummary(
        id=m.id,
        canonical_id=m.canonical_id,
        primary_title=m.primary_title,
        original_title=m.original_title,
        release_date=m.release_date,
        release_year=m.release_year,
        industry=m.industry,
        genres=genres if isinstance(genres, list) else [str(genres)],
        director=m.director,
        lead_actor=m.lead_actor,
        budget_usd=m.budget_usd or 0.0,
        budget_inr_crores=m.budget_inr_crores or 0.0,
        box_office_gross_usd=m.box_office_gross_usd,
        box_office_gross_inr_crores=m.box_office_gross_inr_crores,
        is_released=m.is_released,
        youtube_trailer_id=m.youtube_trailer_id,
        poster_path=m.poster_path,
        backdrop_path=m.backdrop_path,
    )


@router.get("/movies/search", response_model=MovieSearchResponse, summary="Search Movies")
def search_movies(
    q: Optional[str] = Query(None, description="Search term for title, director, or actor"),
    market_segment: Optional[str] = Query(None, description="Industry filter (e.g. Bollywood, Hollywood, Tollywood)"),
    release_year: Optional[int] = Query(None, description="Filter by release year"),
    status: Optional[str] = Query("all", description="Filter by status: all, released, or upcoming"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    High-speed fuzzy search across titles, directors, and lead cast with multi-attribute filtering.
    """
    t0 = time.perf_counter()
    query = db.query(Movie)

    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Movie.primary_title.ilike(term),
                Movie.original_title.ilike(term),
                Movie.director.ilike(term),
                Movie.lead_actor.ilike(term),
            )
        )

    if market_segment and market_segment.lower() != "all":
        query = query.filter(Movie.industry.ilike(f"%{market_segment}%"))

    if release_year:
        query = query.filter(Movie.release_year == release_year)

    if status == "released":
        query = query.filter(Movie.is_released == True)
    elif status == "upcoming":
        query = query.filter(Movie.is_released == False)

    total_count = query.count()
    results = query.order_by(
        desc(Movie.release_year),
        desc(Movie.box_office_gross_usd),
    ).offset(offset).limit(limit).all()

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    summaries = [_format_movie_summary(m) for m in results]

    return MovieSearchResponse(
        query=q or "",
        total_results=total_count,
        latency_ms=latency_ms,
        movies=summaries,
    )


@router.get("/movies/{movie_id}", response_model=MovieDetail, summary="Get Movie Dossier")
def get_movie_detail(movie_id: str, db: Session = Depends(get_db)):
    """
    Retrieves full metadata dossier, cast credits, financial figures, and latest predictions.
    Supports either internal UUID or canonical ID (e.g., tmdb_12345 or tt1234567).
    """
    movie = db.query(Movie).filter(
        or_(Movie.id == movie_id, Movie.canonical_id == movie_id)
    ).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID or canonical ID '{movie_id}' not found.",
        )

    try:
        genres = json.loads(movie.genres) if movie.genres else []
    except Exception:
        genres = [str(movie.genres)] if movie.genres else []

    try:
        cast = json.loads(movie.cast_members) if movie.cast_members else []
    except Exception:
        cast = [str(movie.cast_members)] if movie.cast_members else []

    # Get active prediction if exists
    active_pred = db.query(Prediction).filter(Prediction.movie_id == movie.id).first()
    pred_data = None
    if active_pred:
        pred_data = {
            "prediction_stage": active_pred.prediction_stage,
            "readiness_score": active_pred.readiness_score,
            "expected_gross_usd": active_pred.expected_gross_usd,
            "expected_gross_inr_crores": active_pred.expected_gross_inr_crores,
            "pessimistic_bound_80_usd": active_pred.pessimistic_bound_80_usd,
            "optimistic_bound_80_usd": active_pred.optimistic_bound_80_usd,
            "status_badge": active_pred.status_badge,
            "risk_assessment_tier": active_pred.risk_assessment_tier,
            "top_positive_factor": active_pred.top_positive_factor,
            "top_negative_factor": active_pred.top_negative_factor,
            "narrative_summary": active_pred.narrative_summary,
        }

    # Get buzz metrics if exists
    buzz = db.query(DigitalBuzzObservation).filter(DigitalBuzzObservation.movie_id == movie.id).first()
    buzz_data = None
    if buzz:
        buzz_data = {
            "buzz_score": buzz.buzz_score,
            "view_count": buzz.view_count,
            "like_count": buzz.like_count,
            "comment_count": buzz.comment_count,
            "sentiment_net_polarity": buzz.sentiment_net_polarity,
        }

    return MovieDetail(
        id=movie.id,
        canonical_id=movie.canonical_id,
        primary_title=movie.primary_title,
        original_title=movie.original_title,
        release_date=movie.release_date,
        release_year=movie.release_year,
        runtime_minutes=movie.runtime_minutes,
        original_language=movie.original_language,
        industry=movie.industry,
        genres=genres if isinstance(genres, list) else [str(genres)],
        director=movie.director,
        lead_actor=movie.lead_actor,
        cast_members=cast if isinstance(cast, list) else [str(cast)],
        overview=movie.overview,
        production_company=movie.production_company,
        poster_path=movie.poster_path,
        backdrop_path=movie.backdrop_path,
        budget_usd=movie.budget_usd or 0.0,
        budget_inr_crores=movie.budget_inr_crores or 0.0,
        box_office_gross_usd=movie.box_office_gross_usd,
        box_office_gross_inr_crores=movie.box_office_gross_inr_crores,
        is_released=movie.is_released,
        youtube_trailer_id=movie.youtube_trailer_id,
        active_prediction=pred_data,
        buzz_metrics=buzz_data,
    )


@router.get("/movies/{movie_id}/similar", response_model=List[SimilarMovie], summary="Get Similar Movies")
def get_similar_movies(movie_id: str, limit: int = Query(6, ge=1, le=20), db: Session = Depends(get_db)):
    """
    Returns structurally comparable historical movies based on industry, genre profile,
    budget tier, and talent star power.
    """
    target = db.query(Movie).filter(
        or_(Movie.id == movie_id, Movie.canonical_id == movie_id)
    ).first()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' not found.",
        )

    # Parse target genres
    target_genres = set()
    try:
        if target.genres:
            parsed = json.loads(target.genres)
            target_genres = set(parsed) if isinstance(parsed, list) else {str(parsed)}
    except Exception:
        target_genres = {str(target.genres)}

    # Fetch candidate historical released movies
    candidates = db.query(Movie).filter(
        Movie.id != target.id,
        Movie.is_released == True,
        Movie.box_office_gross_usd > 1_000_000,
    ).limit(200).all()

    scored_candidates = []
    for cand in candidates:
        score = 0.0
        # Industry match
        if cand.industry and target.industry and cand.industry.lower() == target.industry.lower():
            score += 0.35

        # Genre Jaccard similarity
        cand_genres = set()
        try:
            if cand.genres:
                cp = json.loads(cand.genres)
                cand_genres = set(cp) if isinstance(cp, list) else {str(cp)}
        except Exception:
            cand_genres = {str(cand.genres)}

        if target_genres and cand_genres:
            jaccard = len(target_genres & cand_genres) / float(len(target_genres | cand_genres))
            score += jaccard * 0.40

        # Director / Actor overlap
        if target.director and cand.director and target.director == cand.director:
            score += 0.25
        if target.lead_actor and cand.lead_actor and target.lead_actor == cand.lead_actor:
            score += 0.25

        # Budget proximity
        if target.budget_usd and cand.budget_usd and target.budget_usd > 0 and cand.budget_usd > 0:
            ratio = min(target.budget_usd, cand.budget_usd) / max(target.budget_usd, cand.budget_usd)
            score += ratio * 0.15

        scored_candidates.append((score, cand, list(cand_genres)))

    # Sort descending by similarity score
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    top_matches = scored_candidates[:limit]

    output = []
    for score, cand, c_genres in top_matches:
        gross = cand.box_office_gross_usd or 0.0
        inr_cr = round(gross * 83.50 / 10_000_000.0, 2)
        output.append(
            SimilarMovie(
                id=cand.id,
                canonical_id=cand.canonical_id,
                primary_title=cand.primary_title,
                release_year=cand.release_year or 2020,
                industry=cand.industry or "Global",
                genres=c_genres,
                director=cand.director or "Unknown",
                lead_actor=cand.lead_actor or "Unknown",
                budget_usd=cand.budget_usd or 0.0,
                gross_usd=gross,
                gross_formatted_usd=f"${gross / 1_000_000:.1f}M",
                gross_formatted_inr=f"₹{inr_cr:,.1f} Cr",
                similarity_score=round(score, 3),
                poster_path=cand.poster_path,
            )
        )

    return output

