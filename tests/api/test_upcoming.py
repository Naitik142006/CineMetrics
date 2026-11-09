"""
Tests for /upcoming and /upcoming/dashboard endpoints.
"""

def test_get_upcoming_feed(client):
    response = client.get("/api/v1/upcoming?limit=20")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) > 0
    first = items[0]
    assert "primary_title" in first
    assert "expected_gross_usd" in first
    assert "readiness_score" in first
    assert "risk_badge" in first


def test_upcoming_sort_options(client):
    resp_forecast = client.get("/api/v1/upcoming?sort_by=forecast&limit=5")
    assert resp_forecast.status_code == 200
    items = resp_forecast.json()
    if len(items) >= 2:
        assert items[0]["expected_gross_usd"] >= items[1]["expected_gross_usd"]

    resp_readiness = client.get("/api/v1/upcoming?sort_by=readiness&limit=5")
    assert resp_readiness.status_code == 200
    r_items = resp_readiness.json()
    if len(r_items) >= 2:
        assert r_items[0]["readiness_score"] >= r_items[1]["readiness_score"]


def test_upcoming_dashboard(client):
    response = client.get("/api/v1/upcoming/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_upcoming_tracked" in data
    assert data["total_upcoming_tracked"] > 0
    sections = data["sections"]
    expected_sections = [
        "top_predicted_grossers",
        "highest_digital_buzz",
        "high_risk_tentpoles",
        "sleeper_breakouts",
        "bollywood_spotlight",
        "south_indian_powerhouses",
        "hollywood_blockbusters",
    ]
    for sec_key in expected_sections:
        assert sec_key in sections
        assert "items" in sections[sec_key]
        assert "title" in sections[sec_key]

