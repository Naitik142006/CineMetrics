"""
Tests for /movies/search, /movies/{id}, and /movies/{id}/similar endpoints.
"""

def test_search_movies_empty_query(client):
    response = client.get("/api/v1/movies/search?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "movies" in data
    assert len(data["movies"]) <= 10
    assert data["latency_ms"] < 100.0


def test_search_movies_with_query(client):
    response = client.get("/api/v1/movies/search?q=Avatar")
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    assert any("Avatar" in m["primary_title"] for m in data["movies"])


def test_search_movies_filter_status(client):
    resp_released = client.get("/api/v1/movies/search?status=released&limit=5")
    assert resp_released.status_code == 200
    assert all(m["is_released"] is True for m in resp_released.json()["movies"])

    resp_upcoming = client.get("/api/v1/movies/search?status=upcoming&limit=5")
    assert resp_upcoming.status_code == 200
    assert all(m["is_released"] is False for m in resp_upcoming.json()["movies"])


def test_get_movie_detail_by_id(client):
    search_resp = client.get("/api/v1/movies/search?limit=1")
    assert search_resp.status_code == 200
    movies = search_resp.json()["movies"]
    assert len(movies) > 0
    movie_id = movies[0]["id"]

    detail_resp = client.get(f"/api/v1/movies/{movie_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == movie_id
    assert "primary_title" in detail
    assert "genres" in detail


def test_get_movie_detail_not_found(client):
    response = client.get("/api/v1/movies/non_existent_movie_id_9999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_similar_movies(client):
    search_resp = client.get("/api/v1/movies/search?status=released&limit=1")
    movie_id = search_resp.json()["movies"][0]["id"]

    similar_resp = client.get(f"/api/v1/movies/{movie_id}/similar?limit=4")
    assert similar_resp.status_code == 200
    sims = similar_resp.json()
    assert len(sims) <= 4
    for s in sims:
        assert s["similarity_score"] >= 0.0
        assert s["id"] != movie_id

