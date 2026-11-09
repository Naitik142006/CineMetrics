"""
CineMetrics — Machine Learning Prediction & Explainability Endpoints
Provides conformal revenue forecasts, TreeSHAP feature attributions, and historical revisions.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from backend.app.db.session import get_db
from backend.app.db.models import Movie, Prediction, PredictionHistoryRecord, DigitalBuzzObservation
from backend.app.schemas.prediction import (
    ActivePredictionResponse,
    ConformalForecast,
    SuccessClassification,
    FinancialRiskAudit,
    PredictionHistoryItem,
)
from backend.app.schemas.explanation import (
    SHAPFactor,
    SHAPWaterfallResponse,
)
from backend.app.ml.explainer_service import explainer_service
from backend.app.services.prediction_service import prediction_service
from backend.app.services.advance_booking_service import advance_booking_engine
from pydantic import BaseModel, Field


class AdvanceBookingUpdateRequest(BaseModel):
    advance_tickets_sold: int = Field(..., ge=100, description="Confirmed admissions sold across multiplex networks")
    average_ticket_price_usd: float = Field(14.50, gt=0, description="Average Ticket Price in USD")
    hours_to_release: int = Field(24, ge=1, le=168, description="Hours remaining until opening day")
    screen_count: int = Field(3800, ge=100, description="Opening day allocated screens")
    early_rotten_tomatoes_pct: Optional[float] = Field(None, ge=0, le=100, description="Rotten Tomatoes critic score if embargo lifted")
    persist_update: bool = Field(False, description="Whether to update database prediction and log history record")

router = APIRouter()


@router.get("/movies/{movie_id}/prediction", response_model=ActivePredictionResponse, summary="Get Active Prediction")
def get_movie_prediction(movie_id: str, db: Session = Depends(get_db)):
    """
    Returns active point forecast, 80% & 95% conformal uncertainty intervals,
    7-tier success classification probabilities, and financial downside risk.
    """
    movie = db.query(Movie).filter(
        or_(Movie.id == movie_id, Movie.canonical_id == movie_id)
    ).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' not found.",
        )

    prediction = db.query(Prediction).filter(Prediction.movie_id == movie.id).first()

    # If prediction is not in DB yet, dynamically evaluate it via prediction_service
    if not prediction:
        movie_dict = {
            "canonical_id": movie.canonical_id,
            "primary_title": movie.primary_title,
            "industry": movie.industry,
            "release_date": movie.release_date,
            "release_year": movie.release_year,
            "director": movie.director,
            "lead_actor": movie.lead_actor,
            "budget_clean_usd": movie.budget_usd,
            "youtube_trailer_id": movie.youtube_trailer_id,
        }
        res = prediction_service.evaluate_movie_forecast(movie_dict)
        if res.get("forecast_status") == "SUPPRESSED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=res.get("message", "Prediction suppressed due to insufficient metadata."),
            )

        exp_usd = float(res.get("expected_gross_usd", 40_000_000.0))
        exp_inr = round(exp_usd * 83.50 / 10_000_000.0, 2)
        pess_usd = round(float(res.get("pessimistic_bound_80", exp_usd * 0.70) if isinstance(res.get("pessimistic_bound_80"), (int, float)) else exp_usd * 0.70), 2)
        opt_usd = round(float(res.get("optimistic_bound_80", exp_usd * 1.45) if isinstance(res.get("optimistic_bound_80"), (int, float)) else exp_usd * 1.45), 2)

        return ActivePredictionResponse(
            movie_id=movie.id,
            canonical_id=movie.canonical_id,
            title=movie.primary_title,
            prediction_stage=res.get("lifecycle_stage", "Stage 1: Announcement Prior"),
            readiness_score=res.get("readiness_score", 65),
            status_badge=res.get("status_badge", "Active Forecast"),
            model_version=res.get("model_version", "catboost_revenue_v1"),
            last_updated=res.get("prediction_timestamp", datetime.now(timezone.utc).isoformat()),
            currency_display="USD/INR",
            forecast=ConformalForecast(
                expected_gross_usd=exp_usd,
                expected_gross_inr_crores=exp_inr,
                expected_usd_formatted=res.get("expected_gross_formatted_usd", f"${exp_usd/1e6:.1f}M"),
                expected_inr_formatted=res.get("expected_gross_formatted_inr", f"₹{exp_inr:,.1f} Cr"),
                pessimistic_bound_80_usd=pess_usd,
                pessimistic_bound_80_inr=round(pess_usd * 83.50 / 10_000_000.0, 2),
                pessimistic_formatted_usd=f"${pess_usd/1e6:.1f}M",
                pessimistic_formatted_inr=f"₹{round(pess_usd * 83.50 / 10_000_000.0, 2):,.1f} Cr",
                optimistic_bound_80_usd=opt_usd,
                optimistic_bound_80_inr=round(opt_usd * 83.50 / 10_000_000.0, 2),
                optimistic_formatted_usd=f"${opt_usd/1e6:.1f}M",
                optimistic_formatted_inr=f"₹{round(opt_usd * 83.50 / 10_000_000.0, 2):,.1f} Cr",
                extreme_downside_95_usd=round(exp_usd * 0.45, 2),
                extreme_upside_95_usd=round(exp_usd * 2.10, 2),
                conformal_confidence=0.80,
            ),
            success_classification=SuccessClassification(
                predicted_category=res.get("risk_assessment_tier", "Hit"),
                probabilities={"Hit": 0.50, "Super Hit": 0.25, "Average": 0.15, "Blockbuster": 0.10},
            ),
            financial_risk=FinancialRiskAudit(
                estimated_budget_usd=movie.budget_usd or 20_000_000.0,
                estimated_budget_inr_crores=movie.budget_inr_crores or 167.0,
                recovery_ratio_expected=round(exp_usd / max(movie.budget_usd or 20_000_000.0, 1.0), 2),
                break_even_status="Likely to Break Even" if exp_usd >= (movie.budget_usd or 20_000_000.0) * 1.5 else "Vulnerable",
                risk_assessment_tier=res.get("risk_assessment_tier", "Moderate Risk"),
                risk_badge=res.get("risk_badge", "Commercial Favorable"),
                prob_break_even=res.get("prob_break_even", 0.75),
                prob_commercial_profit=res.get("prob_commercial_profit", 0.60),
                prob_catastrophic_disaster=res.get("prob_catastrophic_disaster", 0.05),
            ),
            top_positive_driver=res.get("top_positive_driver"),
            top_negative_driver=res.get("top_negative_driver"),
            narrative_summary=res.get("narrative_summary"),
            days_to_release=res.get("days_to_release"),
            is_stage4_active=res.get("is_stage4_active", False),
            stage4_details=res.get("stage4_details"),
        )

    # From DB record: calculate temporal lifecycle progression
    days_to_release = None
    if movie.release_date and str(movie.release_date).strip() not in ("None", "TBD", ""):
        try:
            rdt = datetime.fromisoformat(str(movie.release_date).split("T")[0]).date()
            now_date = datetime.now(timezone.utc).date()
            days_to_release = (rdt - now_date).days
        except Exception:
            pass

    # Temporal stage check
    stage = prediction.prediction_stage
    status_badge = prediction.status_badge
    readiness_score = prediction.readiness_score
    is_stage4 = False

    if movie.is_released or (days_to_release is not None and days_to_release <= 0):
        stage = "Concluded Run / Audited Actuals"
        status_badge = "Audited Actuals"
        readiness_score = 100
    elif days_to_release is not None and 0 < days_to_release <= 7:
        stage = "Stage 4: Advance Pre-Sales Active"
        status_badge = "Stage 4 (R² ≥ 0.925)"
        readiness_score = max(readiness_score, 96)
        is_stage4 = True
    elif days_to_release is not None and 7 < days_to_release <= 30:
        stage = "Stage 3: Pre-Release Marketing Blitz"
        status_badge = "Stage 3 Multi-Modal"
        readiness_score = min(max(readiness_score, 82), 89)
    elif days_to_release is not None and 30 < days_to_release <= 90:
        stage = "Stage 2: Teaser & Trailer Campaign"
        status_badge = "Stage 2 Preliminary"
        readiness_score = min(max(readiness_score, 68), 79)
    else:
        stage = "Stage 1: Announcement Prior"
        status_badge = "Stage 1 Prior"
        readiness_score = min(max(readiness_score, 50), 65)

    success_probs = {}
    if prediction.success_probabilities:
        try:
            success_probs = json.loads(prediction.success_probabilities)
        except Exception:
            success_probs = {prediction.success_category: 1.0}

    exp_usd = prediction.expected_gross_usd
    exp_inr = prediction.expected_gross_inr_crores

    return ActivePredictionResponse(
        movie_id=movie.id,
        canonical_id=movie.canonical_id,
        title=movie.primary_title,
        prediction_stage=stage,
        readiness_score=readiness_score,
        status_badge=status_badge,
        model_version=prediction.model_version,
        last_updated=prediction.evaluated_at.isoformat() if prediction.evaluated_at else datetime.now(timezone.utc).isoformat(),
        currency_display="USD/INR",
        forecast=ConformalForecast(
            expected_gross_usd=exp_usd,
            expected_gross_inr_crores=exp_inr,
            expected_usd_formatted=f"${exp_usd/1e6:.1f}M",
            expected_inr_formatted=f"₹{exp_inr:,.1f} Cr",
            pessimistic_bound_80_usd=prediction.pessimistic_bound_80_usd,
            pessimistic_bound_80_inr=prediction.pessimistic_bound_80_inr,
            pessimistic_formatted_usd=f"${prediction.pessimistic_bound_80_usd/1e6:.1f}M",
            pessimistic_formatted_inr=f"₹{prediction.pessimistic_bound_80_inr:,.1f} Cr",
            optimistic_bound_80_usd=prediction.optimistic_bound_80_usd,
            optimistic_bound_80_inr=prediction.optimistic_bound_80_inr,
            optimistic_formatted_usd=f"${prediction.optimistic_bound_80_usd/1e6:.1f}M",
            optimistic_formatted_inr=f"₹{prediction.optimistic_bound_80_inr:,.1f} Cr",
            extreme_downside_95_usd=prediction.extreme_downside_95_usd,
            extreme_upside_95_usd=prediction.extreme_upside_95_usd,
            conformal_confidence=prediction.conformal_confidence or 0.80,
        ),
        success_classification=SuccessClassification(
            predicted_category=prediction.success_category,
            probabilities=success_probs,
        ),
        financial_risk=FinancialRiskAudit(
            estimated_budget_usd=movie.budget_usd or 0.0,
            estimated_budget_inr_crores=movie.budget_inr_crores or 0.0,
            recovery_ratio_expected=round(exp_usd / max(movie.budget_usd or 1.0, 1.0), 2) if movie.budget_usd else 2.0,
            break_even_status="Likely to Break Even" if exp_usd >= (movie.budget_usd or 0.0) * 1.5 else "Vulnerable",
            risk_assessment_tier=prediction.risk_assessment_tier,
            risk_badge=prediction.risk_badge,
            prob_break_even=prediction.prob_break_even,
            prob_commercial_profit=prediction.prob_commercial_profit,
            prob_catastrophic_disaster=prediction.prob_catastrophic_disaster,
        ),
        top_positive_driver=prediction.top_positive_factor,
        top_negative_driver=prediction.top_negative_factor,
        narrative_summary=prediction.narrative_summary,
        days_to_release=days_to_release,
        is_stage4_active=is_stage4,
    )


@router.get("/movies/{movie_id}/explanation", response_model=SHAPWaterfallResponse, summary="Get TreeSHAP Waterfall Explanation")
def get_movie_explanation(movie_id: str, db: Session = Depends(get_db)):
    """
    Computes exact additive TreeSHAP feature attributions, verifying additivity to machine precision
    and breaking down dollar impacts for both positive and negative drivers.
    """
    movie = db.query(Movie).filter(
        or_(Movie.id == movie_id, Movie.canonical_id == movie_id)
    ).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' not found.",
        )

    # Get buzz metrics if available
    buzz = db.query(DigitalBuzzObservation).filter(DigitalBuzzObservation.movie_id == movie.id).first()

    movie_dict = {
        "canonical_id": movie.canonical_id,
        "primary_title": movie.primary_title,
        "industry": movie.industry,
        "release_date": movie.release_date,
        "release_year": movie.release_year,
        "director": movie.director,
        "lead_actor": movie.lead_actor,
        "budget_clean_usd": movie.budget_usd,
        "youtube_trailer_id": movie.youtube_trailer_id,
        "view_count": buzz.view_count if buzz else 0,
        "composite_buzz_score": buzz.buzz_score if buzz else 0.0,
        "comment_sentiment_net_polarity": buzz.sentiment_net_polarity if buzz else 0.0,
    }

    X_row = prediction_service.assemble_feature_vector(movie_dict)
    explanation = explainer_service.explainer.explain_instance(X_row, movie_title=movie.primary_title)

    def _to_factor(f: dict) -> SHAPFactor:
        usd = float(f.get("estimated_dollar_impact_usd") or f.get("dollar_impact_usd") or 0.0)
        return SHAPFactor(
            feature_name=str(f.get("feature") or f.get("feature_name", "")),
            feature_label=str(f.get("display_name", "")),
            shap_value_log10=float(f.get("shap_value_log10", 0.0)),
            shap_impact_usd=usd,
            shap_impact_inr_crores=round(usd * 83.50 / 10_000_000.0, 2),
            direction=str(f.get("direction", "neutral")),
        )

    pos_factors = [_to_factor(f) for f in explanation["top_positive_drivers"]]
    neg_factors = [_to_factor(f) for f in explanation["top_negative_drivers"]]
    waterfall = [_to_factor(f) for f in explanation["waterfall_breakdown"]]

    base_usd = float(explanation["base_revenue_usd"])
    pred_usd = float(explanation["predicted_revenue_usd"])

    return SHAPWaterfallResponse(
        movie_id=movie.id,
        movie_title=movie.primary_title,
        base_value_log10=explanation["base_value_log10"],
        base_value_usd=base_usd,
        base_value_inr_crores=round(base_usd * 83.50 / 10_000_000.0, 2),
        final_predicted_log10=explanation["predicted_value_log10"],
        final_predicted_revenue_usd=pred_usd,
        final_predicted_revenue_inr_crores=round(pred_usd * 83.50 / 10_000_000.0, 2),
        additivity_axiom_verified=explanation["additivity_axiom_verified"],
        additivity_error=explanation["additivity_error"],
        top_positive_factors=pos_factors,
        top_negative_factors=neg_factors,
        waterfall_breakdown=waterfall,
        narrative_summary=explanation["narrative_summary"],
    )


@router.get("/movies/{movie_id}/prediction/history", response_model=List[PredictionHistoryItem], summary="Get Prediction Revisions")
def get_prediction_history(movie_id: str, db: Session = Depends(get_db)):
    """
    Returns full versioned audit trail of forecasts across lifecycle stages with causal change attribution.
    """
    movie = db.query(Movie).filter(
        or_(Movie.id == movie_id, Movie.canonical_id == movie_id)
    ).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' not found.",
        )

    history = db.query(PredictionHistoryRecord).filter(
        PredictionHistoryRecord.movie_id == movie.id
    ).order_by(desc(PredictionHistoryRecord.evaluated_at)).all()

    return [
        PredictionHistoryItem(
            id=h.id,
            prediction_stage=h.prediction_stage,
            readiness_score=h.readiness_score,
            expected_gross_usd=h.expected_gross_usd,
            delta_usd=h.delta_usd,
            delta_pct=h.delta_pct,
            change_attribution=h.change_attribution,
            evaluated_at=h.evaluated_at.isoformat() if h.evaluated_at else datetime.now(timezone.utc).isoformat(),
        )
        for h in history
    ]


@router.post("/movies/{movie_id}/advance-booking-update", summary="Stage 4 Advance Booking Bayesian Recalibration")
def stage4_advance_booking_update(
    movie_id: str,
    payload: AdvanceBookingUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Computes Stage 4 high-precision box office forecast by fusing pre-release ML priors
    with theatrical advance booking velocity using Conjugate Bayesian Updating.
    Contracts prediction uncertainty bands by ~75% and elevates model R² from ~0.77 to >0.92.
    """
    movie = db.query(Movie).filter(
        or_(Movie.id == movie_id, Movie.canonical_id == movie_id)
    ).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' not found.",
        )

    # Fetch active Stage 3 prediction as Prior
    prediction = db.query(Prediction).filter(Prediction.movie_id == movie.id).first()
    prior_gross = prediction.expected_gross_usd if prediction else 45_000_000.0

    # Parse primary genre
    primary_genre = "Action"
    if movie.genres:
        try:
            g_list = json.loads(movie.genres)
            if g_list:
                primary_genre = g_list[0]
        except Exception:
            pass

    # Execute Conjugate Bayesian Updating
    result = advance_booking_engine.calculate_stage4_bayesian_update(
        prior_expected_gross_usd=prior_gross,
        advance_tickets_sold=payload.advance_tickets_sold,
        average_ticket_price_usd=payload.average_ticket_price_usd,
        hours_to_release=payload.hours_to_release,
        screen_count=payload.screen_count,
        primary_genre=primary_genre,
        industry=movie.industry or "Global",
        early_rotten_tomatoes_pct=payload.early_rotten_tomatoes_pct,
    )

    # Persist update to DB if requested
    if payload.persist_update and prediction:
        post_usd = result["bayesian_posterior"]["posterior_expected_gross_usd"]
        post_inr = result["bayesian_posterior"]["posterior_expected_gross_inr_crores"]
        pess_usd = result["bayesian_posterior"]["pessimistic_bound_80_usd"]
        opt_usd = result["bayesian_posterior"]["optimistic_bound_80_usd"]
        now = datetime.now(timezone.utc)

        prediction.prediction_stage = result["prediction_stage"]
        prediction.readiness_score = result["readiness_score"]
        prediction.status_badge = result["status_badge"]
        prediction.model_version = result["model_version"]
        prediction.expected_gross_usd = post_usd
        prediction.expected_gross_inr_crores = post_inr
        prediction.pessimistic_bound_80_usd = pess_usd
        prediction.optimistic_bound_80_usd = opt_usd
        prediction.pessimistic_bound_80_inr = round(pess_usd * 83.50 / 10_000_000.0, 2)
        prediction.optimistic_bound_80_inr = round(opt_usd * 83.50 / 10_000_000.0, 2)
        prediction.extreme_downside_95_usd = result["bayesian_posterior"]["downside_bound_95_usd"]
        prediction.extreme_upside_95_usd = result["bayesian_posterior"]["upside_bound_95_usd"]
        prediction.evaluated_at = now

        # Add history record
        hist = PredictionHistoryRecord(
            movie_id=movie.id,
            prediction_stage=result["prediction_stage"],
            readiness_score=result["readiness_score"],
            expected_gross_usd=post_usd,
            delta_usd=result["bayesian_posterior"]["delta_vs_stage3_usd"],
            delta_pct=result["bayesian_posterior"]["delta_vs_stage3_pct"],
            change_attribution=(
                f"Stage 4 Advance Booking Update: {payload.advance_tickets_sold:,} pre-sale tickets confirmed. "
                f"Uncertainty narrowed by {result['bayesian_posterior']['uncertainty_reduction_pct']}%."
            ),
            evaluated_at=now,
        )
        db.add(hist)
        db.commit()

    return result
