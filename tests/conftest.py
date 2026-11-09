"""
CineMetrics — Pytest Configuration & Test Fixtures
"""

import sys
from pathlib import Path

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.init_db import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensures database tables are initialized and seeded before test execution."""
    init_db(force_reseed=False)


@pytest.fixture(scope="module")
def client():
    """Provides reusable TestClient instance for API integration testing."""
    with TestClient(app) as c:
        yield c
