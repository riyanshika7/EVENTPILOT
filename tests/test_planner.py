import pytest
from datetime import date, timedelta
from backend.models import EventCreateRequest, EventPlan, BudgetItem, TaskItem
from backend.planner import (
    construct_event_plan, generate_fallback_plan_data, recalculate_event_plan
)

def test_fallback_plan_generation():
    req = EventCreateRequest(
        name="Aarav's 25th Birthday",
        event_type="birthday",
        event_date=(date.today() + timedelta(days=20)).isoformat(),
        location="Bengaluru",
        guest_count=40,
        budget=15000.0,
        currency="INR",
        food_preference="vegetarian"
    )
    fallback = generate_fallback_plan_data(req)
    assert "overview" in fallback
    assert len(fallback["budget_breakdown"]) >= 5
    assert len(fallback["timeline_tasks"]) >= 5

def test_deterministic_budget_calculation():
    req = EventCreateRequest(
        name="College Fest Hackathon",
        event_type="college",
        event_date=(date.today() + timedelta(days=45)).isoformat(),
        location="Campus Auditorium",
        guest_count=120,
        budget=50000.0,
        currency="INR"
    )
    raw_data = generate_fallback_plan_data(req)
    plan = construct_event_plan(req, raw_data, ai_generated=False, model_name="test-model")
    
    # Total budget items must equal or be within 0.01 of planned budget
    total_est = sum(item.estimated_cost for item in plan.budget_items)
    assert abs(total_est - 50000.0) < 0.05
    assert plan.total_estimated_budget == total_est
    assert plan.is_over_budget is False

def test_over_budget_detection_and_recalculation():
    plan = EventPlan(
        name="Community Picnic",
        event_type="community",
        event_date=(date.today() + timedelta(days=10)).isoformat(),
        guest_count=30,
        total_budget=10000.0,
        currency="INR",
        overview="Fun picnic in the park",
        budget_items=[
            BudgetItem(id="b1", category="Food", item_name="Catering", estimated_cost=8000.0),
            BudgetItem(id="b2", category="Venue", item_name="Park permit", estimated_cost=3000.0),
        ]
    )
    recalculated = recalculate_event_plan(plan)
    assert recalculated.total_estimated_budget == 11000.0
    assert recalculated.remaining_balance == -1000.0
    assert recalculated.is_over_budget is True

def test_date_math_and_overdue_tasks():
    today = date.today()
    req = EventCreateRequest(
        name="Last Minute Gathering",
        event_type="community",
        event_date=(today + timedelta(days=5)).isoformat(),
        guest_count=15,
        budget=5000.0,
        currency="INR"
    )
    raw_data = {
        "tagline": "Quick get-together",
        "overview": "Short notice event",
        "budget_breakdown": [{"category": "Food", "item_name": "Snacks", "percentage": 100}],
        "timeline_tasks": [
            {"title": "Early Task", "days_before": 20, "priority": "high"},
            {"title": "Day Of Task", "days_before": 0, "priority": "low"}
        ]
    }
    plan = construct_event_plan(req, raw_data)
    # The early task (20 days before) is 15 days in the past relative to today, so it should be overdue
    early_task = next(t for t in plan.tasks if t.title == "Early Task")
    assert early_task.is_overdue is True
    day_of_task = next(t for t in plan.tasks if t.title == "Day Of Task")
    assert day_of_task.is_overdue is False
