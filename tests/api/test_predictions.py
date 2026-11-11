"""
Tests for /movies/{id}/prediction, /movies/{id}/explanation, and /prediction/history.
"""

def test_get_active_prediction(client):
    up_resp = client.get("/api/v1/upcoming?limit=1")
    movie = up_resp.json()[0]
    movie_id = movie["id"]

    pred_resp = client.get(f"/api/v1/movies/{movie_id}/prediction")
    assert pred_resp.status_code == 200
    pred = pred_resp.json()
    assert pred["movie_id"] == movie_id
    assert "forecast" in pred
    assert pred["forecast"]["expected_gross_usd"] > 0
    assert pred["forecast"]["pessimistic_bound_80_usd"] <= pred["forecast"]["expected_gross_usd"]
    assert pred["forecast"]["optimistic_bound_80_usd"] >= pred["forecast"]["expected_gross_usd"]
    assert "success_classification" in pred
    assert "financial_risk" in pred
    assert 0.0 <= pred["financial_risk"]["prob_break_even"] <= 1.0


def test_get_shap_explanation(client):
    up_resp = client.get("/api/v1/upcoming?limit=1")
    movie_id = up_resp.json()[0]["id"]

    expl_resp = client.get(f"/api/v1/movies/{movie_id}/explanation")
    assert expl_resp.status_code == 200
    expl = expl_resp.json()
    assert expl["movie_id"] == movie_id
    assert expl["additivity_axiom_verified"] is True
    assert expl["additivity_error"] < 1e-4
    assert len(expl["waterfall_breakdown"]) > 0
    assert "narrative_summary" in expl


def test_get_prediction_history(client):
    up_resp = client.get("/api/v1/upcoming?limit=1")
    movie_id = up_resp.json()[0]["id"]

    hist_resp = client.get(f"/api/v1/movies/{movie_id}/prediction/history")
    assert hist_resp.status_code == 200
    assert isinstance(hist_resp.json(), list)


def test_stage4_advance_booking_update(client):
    up_resp = client.get("/api/v1/upcoming?limit=1")
    movie_id = up_resp.json()[0]["id"]

    payload = {
        "advance_tickets_sold": 450000,
        "average_ticket_price_usd": 15.0,
        "hours_to_release": 24,
        "screen_count": 4200,
        "early_rotten_tomatoes_pct": 85.0,
        "persist_update": True,
    }
    resp = client.post(f"/api/v1/movies/{movie_id}/advance-booking-update", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["prediction_stage"] == "Stage 4: Advance Booking Velocity (Release Eve)"
    assert data["readiness_score"] == 98
    assert "bayesian_posterior" in data
    assert data["bayesian_posterior"]["uncertainty_reduction_pct"] > 50.0
    assert data["accuracy_benchmarks"]["expected_model_r2"] >= 0.90


def test_stage4_live_telemetry_sync_and_feed_ingest(client):
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import AdvanceBookingObservation

    up_resp = client.get("/api/v1/upcoming?limit=1")
    movie_id = up_resp.json()[0]["id"]

    # On-demand live signal sync returns telemetry cleanly without manual ticket entry
    sync_resp = client.post(f"/api/v1/movies/{movie_id}/sync-stage4?persist=false")
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert "signal_telemetry" in sync_data
    assert sync_data["advance_tickets_sold"] > 0
    assert "bayesian_posterior" in sync_data

    # Active T-7..T-0 movies expose automatic stage4_details directly on GET /prediction
    st4_up = client.get("/api/v1/upcoming?stage_filter=stage4&limit=1")
    assert st4_up.status_code == 200
    if st4_up.json():
        st4_id = st4_up.json()[0]["id"]
        st4_pred = client.get(f"/api/v1/movies/{st4_id}/prediction")
        assert st4_pred.status_code == 200
        assert st4_pred.json()["is_stage4_active"] is True
        assert st4_pred.json()["stage4_details"] is not None

    # Batch verified ticketing ingestion endpoint
    try:
        ingest_resp = client.post(
            "/api/v1/sync/advance-bookings",
            json={
                "records": [
                    {
                        "movie_id_or_title": movie_id,
                        "advance_tickets_sold": 320000,
                        "average_ticket_price_usd": 14.0,
                        "hours_to_release": 24,
                        "early_critic_score_pct": 84.0,
                    }
                ]
            },
        )
        assert ingest_resp.status_code == 200
        ingest_data = ingest_resp.json()
        assert ingest_data["status"] == "OK"
        assert ingest_data["recalibrated_count"] == 1
    finally:
        db = SessionLocal()
        try:
            db.query(AdvanceBookingObservation).filter(
                AdvanceBookingObservation.movie_id == movie_id,
                AdvanceBookingObservation.advance_tickets_sold == 320000,
                AdvanceBookingObservation.signal_source == "verified_ticketing",
            ).delete()
            db.commit()
        finally:
            db.close()

