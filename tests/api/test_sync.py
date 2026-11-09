"""
CineMetrics — Test Suite for Weekly Data Synchronization Pipeline
Tests status inquiry, manual forced sync triggers, and OMDb integration.
"""

def test_sync_status(client):
    resp = client.get("/api/v1/sync/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "last_sync_timestamp" in data
    assert "next_scheduled_sync" in data
    assert "sync_interval_days" in data
    assert data["sync_interval_days"] == 7
    assert "status" in data


def test_sync_trigger(client):
    # Trigger a fast sync on top 3 candidate movies
    resp = client.post("/api/v1/sync/trigger?force=true&max_titles=3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("SUCCESS", "ALREADY_RUNNING")
    if data["status"] == "SUCCESS":
        assert "summary" in data
        assert data["summary"]["movies_scanned"] >= 1
