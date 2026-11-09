"""
CineMetrics — Cinema Analytics & Talent Dossier Endpoints
Computes historical actor/director career track records, hit rates, and multi-market distributions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.db.session import get_db
from backend.app.db.models import Movie
from backend.app.schemas.analytics import (
    TalentDossierResponse,
    FilmCredit,
    MarketTrendResponse,
    MarketSegmentMetric,
)

router = APIRouter()


@router.get("/analytics/actor/{person_name}", response_model=TalentDossierResponse, summary="Get Actor Historical Dossier")
def get_actor_dossier(person_name: str, db: Session = Depends(get_db)):
    """
    Retrieves career box-office track record, hit rate, rolling star power tier, and film highlights for an actor.
    """
    clean_name = person_name.strip()
    movies = db.query(Movie).filter(
        Movie.lead_actor.ilike(f"%{clean_name}%"),
        Movie.is_released == True,
    ).order_by(desc(Movie.release_year)).all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No released film records found for actor '{clean_name}'.",
        )

    total_gross = sum(m.box_office_gross_usd or 0.0 for m in movies)
    avg_gross = total_gross / len(movies) if movies else 0.0
    avg_inr = round(avg_gross * 83.50 / 100_000_000.0, 2)

    credits = []
    hits = 0
    rois = []

    for m in movies:
        gross = m.box_office_gross_usd or 0.0
        budget = m.budget_usd or 1.0
        roi = round(gross / budget, 2)
        rois.append(roi)

        category = "Hit" if roi >= 2.0 else "Average" if roi >= 1.0 else "Flop"
        if category in ("Hit", "Super Hit", "Blockbuster"):
            hits += 1

        credits.append(
            FilmCredit(
                title=m.primary_title,
                year=m.release_year or 2020,
                gross_usd=gross,
                gross_formatted_usd=f"${gross/1e6:.1f}M",
                roi_multiplier=roi,
                success_category=category,
            )
        )

    hit_rate = round(hits / max(len(movies), 1), 2)
    median_roi = round(sorted(rois)[len(rois) // 2], 2) if rois else 1.0

    star_tier = "Tier-1 Megastar" if avg_gross >= 100_000_000 else "A-List Commercial Draw" if avg_gross >= 40_000_000 else "Established Lead"

    return TalentDossierResponse(
        person_name=clean_name,
        role="Actor",
        total_films_tracked=len(movies),
        career_cumulative_gross_usd=round(total_gross, 2),
        career_cumulative_gross_formatted_usd=f"${total_gross/1e6:.1f}M",
        career_average_gross_formatted_usd=f"${avg_gross/1e6:.1f}M",
        career_average_gross_formatted_inr=f"₹{avg_inr:,.1f} Cr",
        career_median_roi=median_roi,
        commercial_hit_rate=hit_rate,
        star_power_tier=star_tier,
        filmography_highlights=credits[:10],
    )


@router.get("/analytics/director/{person_name}", response_model=TalentDossierResponse, summary="Get Director Historical Dossier")
def get_director_dossier(person_name: str, db: Session = Depends(get_db)):
    """
    Retrieves career box-office pedigree, commercial hit ratio, and filmography for a director.
    """
    clean_name = person_name.strip()
    movies = db.query(Movie).filter(
        Movie.director.ilike(f"%{clean_name}%"),
        Movie.is_released == True,
    ).order_by(desc(Movie.release_year)).all()

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No released film records found for director '{clean_name}'.",
        )

    total_gross = sum(m.box_office_gross_usd or 0.0 for m in movies)
    avg_gross = total_gross / len(movies) if movies else 0.0
    avg_inr = round(avg_gross * 83.50 / 100_000_000.0, 2)

    credits = []
    hits = 0
    rois = []

    for m in movies:
        gross = m.box_office_gross_usd or 0.0
        budget = m.budget_usd or 1.0
        roi = round(gross / budget, 2)
        rois.append(roi)

        category = "Hit" if roi >= 2.0 else "Average" if roi >= 1.0 else "Flop"
        if category in ("Hit", "Super Hit", "Blockbuster"):
            hits += 1

        credits.append(
            FilmCredit(
                title=m.primary_title,
                year=m.release_year or 2020,
                gross_usd=gross,
                gross_formatted_usd=f"${gross/1e6:.1f}M",
                roi_multiplier=roi,
                success_category=category,
            )
        )

    hit_rate = round(hits / max(len(movies), 1), 2)
    median_roi = round(sorted(rois)[len(rois) // 2], 2) if rois else 1.0
    pedigree_tier = "Elite Auteur / Tentpole Director" if avg_gross >= 150_000_000 else "Proven Commercial Director" if avg_gross >= 50_000_000 else "Mid-Budget Filmmaker"

    return TalentDossierResponse(
        person_name=clean_name,
        role="Director",
        total_films_tracked=len(movies),
        career_cumulative_gross_usd=round(total_gross, 2),
        career_cumulative_gross_formatted_usd=f"${total_gross/1e6:.1f}M",
        career_average_gross_formatted_usd=f"${avg_gross/1e6:.1f}M",
        career_average_gross_formatted_inr=f"₹{avg_inr:,.1f} Cr",
        career_median_roi=median_roi,
        commercial_hit_rate=hit_rate,
        star_power_tier=pedigree_tier,
        filmography_highlights=credits[:10],
    )


@router.get("/analytics/market", response_model=MarketTrendResponse, summary="Get Market Trend Analytics")
def get_market_trends(db: Session = Depends(get_db)):
    """
    Returns comparative cross-market analytics across Bollywood, Tollywood, Kollywood, and Hollywood.
    """
    movies = db.query(Movie).filter(Movie.is_released == True).all()

    segments = ["Hollywood", "Bollywood", "Tollywood", "Kollywood"]
    segment_data = {}

    for s in segments:
        segment_data[s] = {"count": 0, "gross": 0.0, "budget": 0.0, "hits": 0}

    total_gross_all = 0.0
    for m in movies:
        gross = m.box_office_gross_usd or 0.0
        budget = m.budget_usd or 0.0
        total_gross_all += gross

        ind = (m.industry or "Hollywood").title()
        for s in segments:
            if s.lower() in ind.lower():
                segment_data[s]["count"] += 1
                segment_data[s]["gross"] += gross
                segment_data[s]["budget"] += budget
                if budget > 0 and (gross / budget) >= 2.0:
                    segment_data[s]["hits"] += 1
                break

    output_segments = []
    for s in segments:
        data = segment_data[s]
        count = data["count"]
        gross = data["gross"]
        avg_budget = data["budget"] / max(count, 1)
        hit_pct = round((data["hits"] / max(count, 1)) * 100.0, 1)
        mkt_share = round((gross / max(total_gross_all, 1.0)) * 100.0, 1)

        output_segments.append(
            MarketSegmentMetric(
                segment_name=s,
                film_count=count,
                total_box_office_usd=round(gross, 2),
                total_box_office_formatted=f"${gross/1e6:,.1f}M",
                average_budget_formatted=f"${avg_budget/1e6:.1f}M",
                hit_rate_pct=hit_pct,
                market_share_pct=mkt_share,
            )
        )

    return MarketTrendResponse(
        reporting_period="Historical Canonical Catalog (Unified)",
        total_films_analyzed=len(movies),
        segments=output_segments,
    )

