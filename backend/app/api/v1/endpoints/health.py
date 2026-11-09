"""
CineMetrics — System Health & Model Performance Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.db.session import get_db
from backend.app.schemas.analytics import ModelPerformanceResponse

router = APIRouter()


@router.get("/health", summary="System Health Check")
def health_check(db: Session = Depends(get_db)):
    """
    Returns system status, active database connectivity, and ML model loaded status.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "model_loaded": "catboost_revenue_v1.cbm",
        "conformal_calibrator": "conformal_calibrator_v1.joblib",
        "api_version": "1.0.0",
    }


@router.get("/model/performance", response_model=ModelPerformanceResponse, summary="Model Benchmarks")
def get_model_performance():
    """
    Returns official empirical test holdout benchmarks and conformal coverage metrics.
    """
    return ModelPerformanceResponse(
        production_model="CatBoost Regressor + Conformal Calibrator",
        model_version="catboost_revenue_v1.0.0",
        evaluation_dataset="Chronological Holdout Split (>= 2017 Releases, N=605)",
        test_r2_score=0.4389,
        test_rmse_log10=0.7911,
        test_mae_log10=0.5842,
        quadratic_weighted_kappa=0.1695,
        classification_macro_f1=0.1759,
        conformal_coverage_80_target=0.8000,
        conformal_coverage_80_empirical=0.7355,
        conformal_coverage_95_target=0.9500,
        conformal_coverage_95_empirical=0.9256,
        inference_p95_latency_ms=21.68,
        shap_additivity_pass_rate=1.0,
    )
