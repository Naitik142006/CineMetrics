"""
Tests for /analytics endpoints (talent dossiers and market trends).
"""

def test_actor_dossier(client):
    response = client.get("/api/v1/analytics/actor/Tom%20Cruise")
    assert response.status_code == 200
    data = response.json()
    assert "Tom Cruise" in data["person_name"]
    assert data["role"] == "Actor"
    assert data["career_cumulative_gross_usd"] > 1_000_000_000.0
    assert data["commercial_hit_rate"] > 0.0
    assert len(data["filmography_highlights"]) > 0


def test_director_dossier(client):
    response = client.get("/api/v1/analytics/director/James%20Cameron")
    assert response.status_code == 200
    data = response.json()
    assert "James Cameron" in data["person_name"]
    assert data["role"] == "Director"
    assert data["career_cumulative_gross_usd"] > 1_000_000_000.0


def test_talent_not_found(client):
    response = client.get("/api/v1/analytics/actor/NonExistentPersonName1234")
    assert response.status_code == 404


def test_market_trends(client):
    response = client.get("/api/v1/analytics/market")
    assert response.status_code == 200
    data = response.json()
    assert data["total_films_analyzed"] > 0
    assert len(data["segments"]) >= 4
    for seg in data["segments"]:
        assert seg["film_count"] >= 0
        assert 0.0 <= seg["market_share_pct"] <= 100.0
