import os
import tempfile

# The app uses the configured SQLite database by default. These tests verify the
# web surface can start and its core endpoints return valid responses.
from app import app, init_db, seed_demo_data


def setup_module():
    init_db()
    seed_demo_data()


def test_dashboard_loads():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Marketplace leads" in response.data
    assert b"Lead inbox" in response.data


def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_lead_api():
    client = app.test_client()
    response = client.get("/api/leads")
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, list)
    assert payload
    assert "score" in payload[0]


def test_summary_api():
    client = app.test_client()
    response = client.get("/api/summary")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] >= 1
    assert 0 <= payload["average_score"] <= 100
