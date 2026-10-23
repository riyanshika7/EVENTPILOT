import pytest
import os
from fastapi.testclient import TestClient
from datetime import date, timedelta
from backend.main import app
from backend.database import init_db
from backend.config import settings
from backend.observability import get_diagnostics_summary

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    test_db = os.path.join(tmp_path, "test_events.db")
    settings.DATABASE_PATH = test_db
    init_db()

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "EventPilot AI"
    assert "environment" in data
    assert "sentry_enabled" in data

def test_model_status_endpoint():
    response = client.get("/api/model/status")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert "model_configured" in data
    assert "provider" in data

def test_diagnostics_endpoint():
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "total_runs" in data
    assert "success_rate_percent" in data
    assert "sentry_enabled" in data

def test_generate_event_demo_mode_records_span():
    payload = {
        "name": "Rohan & Priya Wedding Reception",
        "event_type": "wedding",
        "event_date": (date.today() + timedelta(days=60)).isoformat(),
        "location": "Jaipur",
        "guest_count": 250,
        "budget": 500000.0,
        "currency": "INR",
        "food_preference": "vegetarian",
        "venue_preference": "banquet",
        "priority": "balanced"
    }
    response = client.post("/api/events/generate?force_demo=true", json=payload)
    assert response.status_code == 200
    plan = response.json()
    assert plan["name"] == "Rohan & Priya Wedding Reception"
    assert len(plan["budget_items"]) > 0
    assert len(plan["tasks"]) > 0
    assert len(plan["vendors"]) > 0
    assert plan["ai_generated"] is False
    assert "Demo" in plan["model_used"]

    # Verify recorded diagnostics
    diag = get_diagnostics_summary()
    assert diag["total_runs"] >= 1

def test_generate_validation_failure():
    # Negative budget or 0 guests must return 400
    bad_payload = {
        "name": "Bad Event",
        "event_type": "birthday",
        "event_date": "2026-11-20",
        "guest_count": 0,
        "budget": -100.0
    }
    res = client.post("/api/events/generate", json=bad_payload)
    assert res.status_code == 422 or res.status_code == 400

def test_save_and_retrieve_event_lifecycle():
    # 1. Generate plan in demo mode
    payload = {
        "name": "Annual Hackathon Gala",
        "event_type": "college",
        "event_date": (date.today() + timedelta(days=30)).isoformat(),
        "guest_count": 80,
        "budget": 35000.0,
        "currency": "INR"
    }
    gen_res = client.post("/api/events/generate?force_demo=true", json=payload)
    assert gen_res.status_code == 200
    plan = gen_res.json()
    
    # 2. Save plan to repository
    save_res = client.post("/api/events", json=plan)
    assert save_res.status_code == 201
    saved_plan = save_res.json()
    event_id = saved_plan["id"]

    # 3. Retrieve plan
    get_res = client.get(f"/api/events/{event_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == event_id
    assert retrieved["name"] == "Annual Hackathon Gala"

    # 4. List events
    list_res = client.get("/api/events")
    assert list_res.status_code == 200
    events = list_res.json()
    assert any(e["id"] == event_id for e in events)

    # 5. Delete event
    del_res = client.delete(f"/api/events/{event_id}")
    assert del_res.status_code == 200

    # 6. Verify 404
    get_again = client.get(f"/api/events/{event_id}")
    assert get_again.status_code == 404
