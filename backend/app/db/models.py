"""
CineMetrics — SQLAlchemy Relational ORM Models
Defines canonical tables for Movies, Predictions, Digital Buzz, and Prediction History.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Movie(Base):
    __tablename__ = "movies"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    canonical_id = Column(String(128), unique=True, index=True, nullable=False)
    imdb_id = Column(String(32), index=True, nullable=True)
    tmdb_id = Column(Integer, index=True, nullable=True)
    primary_title = Column(String(255), index=True, nullable=False)
    original_title = Column(String(255), nullable=True)
    release_date = Column(String(32), index=True, nullable=True)
    release_year = Column(Integer, index=True, nullable=True)
    runtime_minutes = Column(Integer, nullable=True)
    original_language = Column(String(16), index=True, nullable=True)
    industry = Column(String(64), index=True, nullable=True)
    genres = Column(Text, nullable=True)  # JSON-encoded array
    director = Column(String(255), index=True, nullable=True)
    lead_actor = Column(String(255), index=True, nullable=True)
    cast_members = Column(Text, nullable=True)  # JSON-encoded array
    production_company = Column(String(255), nullable=True)
    poster_path = Column(String(512), nullable=True)
    backdrop_path = Column(String(512), nullable=True)
    overview = Column(Text, nullable=True)
    budget_usd = Column(Float, default=0.0)
    budget_inr_crores = Column(Float, default=0.0)
    box_office_gross_usd = Column(Float, nullable=True)
    box_office_gross_inr_crores = Column(Float, nullable=True)
    is_released = Column(Boolean, default=False, index=True)
    youtube_trailer_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    predictions = relationship("Prediction", back_populates="movie", cascade="all, delete-orphan")
    buzz_observations = relationship("DigitalBuzzObservation", back_populates="movie", cascade="all, delete-orphan")
    history_records = relationship("PredictionHistoryRecord", back_populates="movie", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    movie_id = Column(String(64), ForeignKey("movies.id"), index=True, nullable=False)
    prediction_stage = Column(String(64), index=True, nullable=False)
    readiness_score = Column(Integer, nullable=False)
    status_badge = Column(String(64), nullable=False)
    model_version = Column(String(64), default="catboost_revenue_v1")
    expected_gross_usd = Column(Float, nullable=False)
    expected_gross_inr_crores = Column(Float, nullable=False)
    pessimistic_bound_80_usd = Column(Float, nullable=False)
    optimistic_bound_80_usd = Column(Float, nullable=False)
    pessimistic_bound_80_inr = Column(Float, nullable=False)
    optimistic_bound_80_inr = Column(Float, nullable=False)
    extreme_downside_95_usd = Column(Float, nullable=True)
    extreme_upside_95_usd = Column(Float, nullable=True)
    conformal_confidence = Column(Float, default=0.80)
    success_category = Column(String(64), nullable=False)
    success_probabilities = Column(Text, nullable=True)  # JSON-encoded dict
    prob_break_even = Column(Float, default=0.0)
    prob_commercial_profit = Column(Float, default=0.0)
    prob_catastrophic_disaster = Column(Float, default=0.0)
    risk_assessment_tier = Column(String(64), nullable=False)
    risk_badge = Column(String(64), nullable=False)
    top_positive_factor = Column(String(255), nullable=True)
    top_negative_factor = Column(String(255), nullable=True)
    narrative_summary = Column(Text, nullable=True)
    evaluated_at = Column(DateTime, default=utc_now)

    movie = relationship("Movie", back_populates="predictions")


class DigitalBuzzObservation(Base):
    __tablename__ = "digital_buzz_observations"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    movie_id = Column(String(64), ForeignKey("movies.id"), index=True, nullable=False)
    youtube_video_id = Column(String(64), nullable=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    buzz_score = Column(Float, default=0.0)
    sentiment_net_polarity = Column(Float, default=0.0)
    total_comments_sampled = Column(Integer, default=0)
    positive_ratio = Column(Float, default=0.0)
    neutral_ratio = Column(Float, default=0.0)
    negative_ratio = Column(Float, default=0.0)
    observed_at = Column(DateTime, default=utc_now)

    movie = relationship("Movie", back_populates="buzz_observations")


class PredictionHistoryRecord(Base):
    __tablename__ = "prediction_history"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    movie_id = Column(String(64), ForeignKey("movies.id"), index=True, nullable=False)
    prediction_stage = Column(String(64), nullable=False)
    readiness_score = Column(Integer, nullable=False)
    expected_gross_usd = Column(Float, nullable=False)
    delta_usd = Column(Float, default=0.0)
    delta_pct = Column(Float, default=0.0)
    change_attribution = Column(String(512), nullable=False)
    evaluated_at = Column(DateTime, default=utc_now)

    movie = relationship("Movie", back_populates="history_records")

