import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_demo_lab_sample_endpoint():
    res = client.get("/api/demo-lab/sample")
    assert res.status_code == 200
    data = res.json()
    assert "Nexus 2026" in data["name"]
    assert data["event_type"] == "college"
    assert data["guest_count"] == 180
    assert data["budget"] == 45000.0

def test_demo_lab_import_budget_csv_valid():
    csv_payload = """category,item_name,estimated_cost,notes
Venue Hire,Auditorium sound and stage,12000,Includes lights
Catering,Lunch boxes and coffee,18000,Veg boxes
Audio,Microphones and mixers,5000,3 lapel mics
Prizes,Hackathon trophies,4000,Top 3 teams
"""
    res = client.post("/api/demo-lab/import-budget-csv", json={"csv_content": csv_payload})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["total_rows"] == 4
    assert data["total_amount"] == 39000.0
    assert len(data["errors"]) == 0

def test_demo_lab_import_budget_csv_invalid_header():
    csv_payload = "wrong_header1,wrong_header2\n10,20\n"
    res = client.post("/api/demo-lab/import-budget-csv", json={"csv_content": csv_payload})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert any("must contain columns" in e for e in data["errors"])

def test_demo_lab_import_budget_csv_empty():
    res = client.post("/api/demo-lab/import-budget-csv", json={"csv_content": ""})
    # Pydantic validates min_length
    assert res.status_code in [200, 422]

def test_demo_lab_import_budget_csv_formula_injection_sanitization():
    csv_payload = """category,item_name,estimated_cost,notes
=cmd|' /C calc'!A0,Dangerous Item,1500,Test
"""
    res = client.post("/api/demo-lab/import-budget-csv", json={"csv_content": csv_payload})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    first_item = data["parsed_items"][0]
    # Sanitized cell must start with quote prefix
    assert first_item["category"].startswith("'")
