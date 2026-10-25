import pytest
from datetime import date, timedelta
from backend.models import EventCreateRequest, EventPlan, BudgetItem, TaskItem
from backend.planner import construct_event_plan, recalculate_event_plan

@pytest.mark.parametrize("budget, guest_count, expected_items", [
    (100.0, 5, 6),
    (50000.0, 100, 6),
    (1000000.0, 500, 6),
])
def test_budget_scales_correctly(budget, guest_count, expected_items):
    req = EventCreateRequest(
        name="Param Test Event",
        event_type="community",
        event_date=(date.today() + timedelta(days=30)).isoformat(),
        guest_count=guest_count,
        budget=budget,
        currency="INR"
    )
    raw_data = {
        "budget_breakdown": [
            {"category": "Food", "percentage": 35},
            {"category": "Venue", "percentage": 25},
            {"category": "Decor", "percentage": 15},
            {"category": "Music", "percentage": 10},
            {"category": "Photo", "percentage": 8},
            {"category": "Contingency", "percentage": 7}
        ]
    }
    plan = construct_event_plan(req, raw_data)
    assert len(plan.budget_items) == expected_items
    total_est = sum(item.estimated_cost for item in plan.budget_items)
    assert abs(total_est - budget) < 0.05
    assert plan.remaining_balance >= 0

def test_single_day_preparation_window():
    """Verify that events happening tomorrow do not crash and mark early tasks as overdue."""
    today = date.today()
    req = EventCreateRequest(
        name="Emergency Gathering",
        event_type="community",
        event_date=(today + timedelta(days=1)).isoformat(),
        guest_count=10,
        budget=2000.0,
        currency="INR"
    )
    raw_data = {
        "timeline_tasks": [
            {"title": "1-Month Booking", "days_before": 30, "priority": "high"},
            {"title": "Day-of Prep", "days_before": 0, "priority": "high"}
        ]
    }
    plan = construct_event_plan(req, raw_data)
    t_early = next(t for t in plan.tasks if t.title == "1-Month Booking")
    t_dayof = next(t for t in plan.tasks if t.title == "Day-of Prep")
    assert t_early.is_overdue is True
    assert t_dayof.is_overdue is False

def test_currency_rounding_reconciliation():
    """Verify odd budgets with fractional division are reconciled deterministically."""
    req = EventCreateRequest(
        name="Odd Budget Birthday",
        event_type="birthday",
        event_date=(date.today() + timedelta(days=20)).isoformat(),
        guest_count=17,
        budget=3333.33,
        currency="INR"
    )
    raw_data = {
        "budget_breakdown": [
            {"category": "Item 1", "percentage": 33.33},
            {"category": "Item 2", "percentage": 33.33},
            {"category": "Item 3", "percentage": 33.34}
        ]
    }
    plan = construct_event_plan(req, raw_data)
    total_est = sum(item.estimated_cost for item in plan.budget_items)
    assert abs(total_est - 3333.33) < 0.05
