"""
Tests for /simulate/what-if endpoint.
"""

def test_counterfactual_simulation(client):
    up_resp = client.get("/api/v1/upcoming?limit=1")
    movie_id = up_resp.json()[0]["id"]

    payload = {
        "base_movie_id": movie_id,
        "budget_usd_override": 100_000_000.0,
        "director_override": "Christopher Nolan",
        "simulated_trailer_views": 50_000_000,
    }

    sim_resp = client.post("/api/v1/simulate/what-if", json=payload)
    assert sim_resp.status_code == 200
    res = sim_resp.json()
    assert res["base_movie_id"] == movie_id
    assert res["execution_latency_ms"] < 250.0  # Well within our SLA
    assert "baseline_scenario" in res
    assert "simulated_scenario" in res
    assert "delta_analysis" in res
    assert "strategic_verdict" in res["delta_analysis"]


def test_simulation_invalid_movie(client):
    payload = {
        "base_movie_id": "invalid_id_9999",
        "budget_usd_override": 50_000_000.0,
    }
    sim_resp = client.post("/api/v1/simulate/what-if", json=payload)
    assert sim_resp.status_code == 404
