"""
Tests for /health, root landing, and /model/performance endpoints.
"""

def test_root_landing(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "CineMetrics API"
    assert data["status"] == "online"
    assert "version" in data


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "model_loaded" in data


def test_model_performance_benchmarks(client):
    response = client.get("/api/v1/model/performance")
    assert response.status_code == 200
    data = response.json()
    assert data["production_model"] == "CatBoost Regressor + Conformal Calibrator"
    assert data["test_r2_score"] > 0.40
    assert data["conformal_coverage_80_empirical"] > 0.70
    assert data["shap_additivity_pass_rate"] == 1.0

