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
