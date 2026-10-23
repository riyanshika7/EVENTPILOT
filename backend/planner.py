"""
Deterministic Event Planner & Validator.
Structures prompt for Gemma instruction-tuned models, deterministically computes all budget allocations,
date offsets, overdue statuses, and wraps execution in Sentry spans.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

from backend.models import (
    EventCreateRequest, EventPlan, BudgetItem, TaskItem, VendorItem, ShoppingItem
)
from backend.observability import AISpanContext

def build_gemma_event_prompt(req: EventCreateRequest) -> str:
    """Build a precise prompt optimized for Gemma instruction-following."""
    return f"""You are EventPilot AI, an expert event architect designed for effortless planning ("Channel Your Inner Sloth").
Plan a complete event with these exact parameters:
- Event: {req.name} ({req.event_type})
- Target Date: {req.event_date}
- Guest Count: {req.guest_count} attendees
- Budget: {req.currency} {req.budget:,.2f}
- Location: {req.location or "Not specified"}
- Food Preference: {req.food_preference}
- Theme: {req.theme or "Warm & Celebratory"}
- Cultural Touches: {req.cultural_preference or "None specified"}
- Venue Preference: {req.venue_preference}
- Priority: {req.priority}
- Special Notes: {req.additional_notes or "None"}

Generate realistic, thoughtful event ideas respecting this exact guest count and budget. Do NOT invent verified business names or fake phone numbers.

OUTPUT ONLY VALID JSON WITH EXACTLY THIS SCHEMA (no markdown, no backticks, no extra text):
{{
  "tagline": "A catchy, warm 4-8 word tagline",
  "overview": "2-3 sentences summarizing the event concept and sloth-friendly approach",
  "theme_ideas": ["3-5 creative theme and styling concepts"],
  "activities_schedule": [
    {{"time": "05:30 PM", "activity": "Welcome & Mocktails", "notes": "Casual mingling"}},
    {{"time": "07:00 PM", "activity": "Main Program / Celebration", "notes": "Core highlight"}},
    {{"time": "08:30 PM", "activity": "Dinner & Feasting", "notes": "Buffet service"}},
    {{"time": "10:00 PM", "activity": "Wrap Up & Farewell", "notes": "Parting favors"}}
  ],
  "budget_breakdown": [
    {{"category": "Food & Catering", "item_name": "Meals and drinks for guests", "percentage": 35, "notes": "Portioned for headcount"}},
    {{"category": "Venue & Facilities", "item_name": "Venue hire or home staging", "percentage": 25, "notes": "Appropriate capacity"}},
    {{"category": "Decor & Styling", "item_name": "Lighting, florals, focal backdrop", "percentage": 15, "notes": "Eco-friendly aesthetics"}},
    {{"category": "Entertainment & Music", "item_name": "Audio equipment & playlist setup", "percentage": 10, "notes": "Engaging vibes"}},
    {{"category": "Photography & Memories", "item_name": "Photo moments and candid capture", "percentage": 8, "notes": "Memory capture"}},
    {{"category": "Contingency Fund", "item_name": "Buffer for unexpected extras", "percentage": 7, "notes": "Safety cushion"}}
  ],
  "timeline_tasks": [
    {{"title": "Lock Venue and Date", "description": "Confirm reservation and access times", "days_before": 30, "priority": "high", "phase": "1 Month Before"}},
    {{"title": "Send Digital Invites", "description": "Share invitations and track RSVPs", "days_before": 21, "priority": "high", "phase": "3 Weeks Before"}},
    {{"title": "Finalize Catering Menu", "description": "Confirm dietary choices and serving style", "days_before": 14, "priority": "high", "phase": "2 Weeks Before"}},
    {{"title": "Order Cake & Party Supplies", "description": "Secure celebration cake and disposable supplies", "days_before": 7, "priority": "medium", "phase": "1 Week Before"}},
    {{"title": "Day-of Setup & Sound Check", "description": "Arrange decor, verify audio, welcome guests", "days_before": 0, "priority": "high", "phase": "Day of Event"}}
  ],
  "vendor_categories": [
    {{"category": "Food & Catering", "recommended_scope": "Full meal service for guest count", "key_questions": ["What is the per-head pricing?", "Are cleanup and servers included?"]}},
    {{"category": "Venue & Space", "recommended_scope": "Space with comfortable capacity and power backup", "key_questions": ["What is the noise curfew?", "Can we bring outside caterers?"]}},
    {{"category": "Decor & Styling", "recommended_scope": "Focal stage and table accents", "key_questions": ["Do you handle setup and takedown?", "Can we customize colors?"]}}
  ],
  "shopping_checklist": [
    {{"category": "Decorations", "item": "Fairy lights & welcome signage", "quantity": "1 kit"}},
    {{"category": "Food & Drink", "item": "Celebration cake & dessert items", "quantity": "1 cake"}},
    {{"category": "Supplies", "item": "Dinnerware sets and napkins", "quantity": "Sufficient for guests"}},
    {{"category": "Emergency Kit", "item": "Scissors, extension cords, tape", "quantity": "1 pack"}}
  ],
  "food_catering_suggestions": [
    "Welcome fruit cooler or specialty iced tea",
    "Finger appetizers during initial guest arrival",
    "Balanced main buffet respecting dietary choices",
    "Celebratory dessert bar"
  ],
  "contingency_recommendations": [
    "Keep the 7% contingency reserve untouched until event day.",
    "Designate a trusted co-host as vendor point-of-contact so you can relax.",
    "Have a bad-weather backup if utilizing any outdoor area."
  ],
  "cost_saving_suggestions": [
    "Send digital video/card invites via WhatsApp instead of paper prints.",
    "Curate a personalized streaming playlist instead of hiring a full sound crew.",
    "Focus decorations on one memorable photo backdrop rather than the entire room."
  ],
  "potential_risks": [
    "Headcount surprises — freeze final numbers 72 hours before.",
    "Audio difficulties — test Bluetooth and aux cables 2 hours before start."
  ]
}}
"""

def generate_deterministic_demo_plan(req: EventCreateRequest) -> Dict[str, Any]:
    """Provides a deterministic event plan for demo mode or fallbacks."""
    return {
        "tagline": f"You celebrate. EventPilot handles {req.name}.",
        "overview": f"A thoughtfully orchestrated {req.event_type} for {req.guest_count} guests. Designed around a total budget of {req.currency} {req.budget:,.2f} prioritizing effortless coordination and relaxed celebrations.",
        "theme_ideas": [
            f"Warm Earth & Botanical Sage ({req.theme or 'Relaxed Modern'} style)",
            "Cozy conversational lounge area with warm ambient string lights",
            "Minimalist photo-ready backdrop with personalized signage",
            "Interactive memory board or digital guestbook station"
        ],
        "activities_schedule": [
            {"time": "05:30 PM", "activity": "Arrival & Welcome Refreshments", "notes": "Chilled coolers and ambient music"},
            {"time": "06:45 PM", "activity": "Opening Welcome & Gathering", "notes": "Brief toast and introductions"},
            {"time": "07:30 PM", "activity": "Dinner & Culinary Highlights", "notes": f"Main course buffet serving {req.food_preference} menu"},
            {"time": "09:00 PM", "activity": "Celebration Highlights & Games", "notes": "Cake cutting, memorable games, and open music"},
            {"time": "10:30 PM", "activity": "Farewell & Parting Favors", "notes": "Warm goodbyes and seamless pack-down"}
        ],
        "budget_breakdown": [
            {"category": "Food & Catering", "item_name": f"Buffet catering & beverages ({req.food_preference})", "percentage": 35, "notes": f"Scaled for {req.guest_count} guests"},
            {"category": "Venue & Facilities", "item_name": f"Venue hiring or home setup ({req.venue_preference})", "percentage": 25, "notes": "Includes basic seating"},
            {"category": "Decor & Styling", "item_name": "Backdrop, fairy lights, floral accents", "percentage": 15, "notes": "Warm botanical aesthetic"},
            {"category": "Entertainment & Audio", "item_name": "Sound system, playlist & party games", "percentage": 10, "notes": "Social entertainment"},
            {"category": "Photography & Memories", "item_name": "Photographer / candid memory capture", "percentage": 8, "notes": "Highlight moments"},
            {"category": "Contingency Fund", "item_name": "Buffer for unexpected supplies", "percentage": 7, "notes": "7% safety cushion"}
        ],
        "timeline_tasks": [
            {"title": "Confirm Venue & Date", "description": "Lock in venue reservation, terms, and timings", "days_before": 30, "priority": "high", "phase": "1 Month Before"},
            {"title": "Send Digital Invitations", "description": "Share digital invites with RSVP deadline", "days_before": 21, "priority": "high", "phase": "3 Weeks Before"},
            {"title": "Finalize Catering & Menu", "description": f"Confirm {req.food_preference} menu selections", "days_before": 14, "priority": "high", "phase": "2 Weeks Before"},
            {"title": "Order Cake & Tableware", "description": "Pre-order celebration cake and party supplies", "days_before": 7, "priority": "medium", "phase": "1 Week Before"},
            {"title": "Final Headcount Confirmation", "description": "Confirm final guest count with caterer", "days_before": 3, "priority": "high", "phase": "Final Days"},
            {"title": "Day-of Setup & Sound Check", "description": "Arrange decor, test audio, welcome first arrivals", "days_before": 0, "priority": "high", "phase": "Day of Event"}
        ],
        "vendor_categories": [
            {"category": "Food & Catering", "recommended_scope": f"Full service meal for {req.guest_count} guests", "key_questions": ["What is the per-plate pricing?", "Are cleanup and servers included?", "What are dietary allergy safeguards?"]},
            {"category": "Venue & Facilities", "recommended_scope": f"Comfortable space for {req.guest_count} guests", "key_questions": ["What is power backup policy?", "What is noise curfew?", "Are chairs and tables included?"]},
            {"category": "Decor & Styling", "recommended_scope": "Main stage and ambient lighting setup", "key_questions": ["Do you handle setup and teardown?", "Can lighting colors be customized?"]},
            {"category": "Photography", "recommended_scope": "3 to 4 hours of event coverage", "key_questions": ["When will edited photos be delivered?", "Do you provide cloud gallery links?"]}
        ],
        "shopping_checklist": [
            {"category": "Decorations", "item": "Fairy lights, welcome banner, balloons", "quantity": "1 kit"},
            {"category": "Food & Drink", "item": "Celebratory cake & sweet treats", "quantity": f"~{max(1, req.guest_count // 15)} kg"},
            {"category": "Dining Supplies", "item": "Plates, cutlery, cups, napkins", "quantity": f"{req.guest_count + 10} sets"},
            {"category": "Entertainment", "item": "Party game props & small prizes", "quantity": "3 sets"},
            {"category": "Emergency Kit", "item": "Tape, extension cords, scissors", "quantity": "1 box"}
        ],
        "food_catering_suggestions": [
            "Welcome fruit cooler or specialty iced tea",
            f"Curated {req.food_preference} finger appetizers during mingling",
            "Main course buffet with 2 entrees, side salads, and signature rice",
            "Celebratory dessert bar"
        ],
        "contingency_recommendations": [
            "Keep the 7% contingency reserve untouched until event day.",
            "Designate one dependable co-host to handle vendor arrivals so you can celebrate.",
            "Prepare a portable Bluetooth speaker and offline playlist in case of audio glitches."
        ],
        "cost_saving_suggestions": [
            "Opt for digital invitations with a Google Form or WhatsApp RSVP tracker.",
            "Create your own photo booth corner with fairy lights and simple greenery.",
            "Buy non-perishable party supplies in bulk or from wholesale local markets."
        ],
        "potential_risks": [
            "Unconfirmed RSVPs leading to catering shortage — lock headcount 72 hours before.",
            "Weather variance for outdoor areas — confirm rain/shade backup.",
            "Vendor delays — request delivery 90 minutes before guest arrival."
        ]
    }

def construct_event_plan(
    req: EventCreateRequest,
    raw_data: Dict[str, Any],
    ai_generated: bool = True,
    model_name: str = "gemma2:2b"
) -> EventPlan:
    """
    Deterministically computes budget totals, task due dates, and builds the full validated EventPlan.
    Never trusts LLM for arithmetic or date math.
    """
    event_id = str(uuid.uuid4())
    now_iso = datetime.now().isoformat()
    
    # 1. Timeline & Date calculations
    with AISpanContext("event_plan.build_timeline", "Calculate deterministic deadlines"):
        try:
            event_dt = datetime.strptime(req.event_date, "%Y-%m-%d").date()
        except Exception:
            event_dt = date.today() + timedelta(days=30)
        today = date.today()
        
        tasks: List[TaskItem] = []
        raw_tasks = raw_data.get("timeline_tasks", [])
        if not raw_tasks:
            raw_tasks = generate_deterministic_demo_plan(req)["timeline_tasks"]

        for idx, t in enumerate(raw_tasks):
            days_before = int(t.get("days_before", max(0, 30 - idx * 5)))
            task_due = event_dt - timedelta(days=days_before)
            is_overdue = (task_due < today)
            phase = t.get("phase") or (
                "Day of Event" if days_before == 0 else
                "Week Of Event" if days_before <= 7 else
                "2 Weeks Before" if days_before <= 14 else
                "1 Month Before"
            )
            tasks.append(TaskItem(
                id=f"task-{uuid.uuid4().hex[:8]}",
                title=str(t.get("title", f"Preparation Task #{idx+1}")),
                description=str(t.get("description", "")),
                phase=phase,
                due_date=task_due.isoformat(),
                days_before_event=days_before,
                priority=str(t.get("priority", "medium")).lower(),
                completed=False,
                is_overdue=is_overdue
            ))
        tasks.sort(key=lambda x: x.due_date)

    # 2. Deterministic Budget calculations
    with AISpanContext("event_plan.calculate_budget", "Deterministic financial allocations"):
        raw_budget = raw_data.get("budget_breakdown", [])
        if not raw_budget:
            raw_budget = generate_deterministic_demo_plan(req)["budget_breakdown"]

        budget_items: List[BudgetItem] = []
        category_totals: Dict[str, float] = {}
        total_percentage = sum(float(b.get("percentage", 0)) for b in raw_budget)
        if total_percentage <= 0:
            total_percentage = 100.0

        accumulated_estimated = 0.0
        for idx, b in enumerate(raw_budget):
            cat = str(b.get("category", "General Expense"))
            item_name = str(b.get("item_name", cat))
            pct = float(b.get("percentage", 10))
            est_cost = round((pct / total_percentage) * req.budget, 2)
            accumulated_estimated += est_cost
            
            category_totals[cat] = round(category_totals.get(cat, 0.0) + est_cost, 2)
            budget_items.append(BudgetItem(
                id=f"budget-{uuid.uuid4().hex[:8]}",
                category=cat,
                item_name=item_name,
                estimated_cost=est_cost,
                actual_cost=0.0,
                notes=str(b.get("notes", ""))
            ))

        # Precision reconciliation
        diff = round(req.budget - accumulated_estimated, 2)
        if budget_items and abs(diff) > 0 and abs(diff) < 5:
            budget_items[0].estimated_cost = round(budget_items[0].estimated_cost + diff, 2)
            accumulated_estimated = round(accumulated_estimated + diff, 2)
            first_cat = budget_items[0].category
            category_totals[first_cat] = round(category_totals[first_cat] + diff, 2)

        remaining_balance = round(req.budget - accumulated_estimated, 2)
        is_over_budget = accumulated_estimated > req.budget

    # 3. Vendors
    raw_vendors = raw_data.get("vendor_categories", [])
    if not raw_vendors:
        raw_vendors = generate_deterministic_demo_plan(req)["vendor_categories"]
    
    vendors: List[VendorItem] = []
    for v in raw_vendors:
        cat = str(v.get("category", "Vendor Service"))
        matched_est = category_totals.get(cat, round(req.budget * 0.15, 2))
        questions = v.get("key_questions", [])
        if isinstance(questions, str):
            questions = [questions]
        vendors.append(VendorItem(
            id=f"vendor-{uuid.uuid4().hex[:8]}",
            category=cat,
            recommended_scope=str(v.get("recommended_scope", "")),
            key_questions=[str(q) for q in questions],
            vendor_name="",
            quoted_cost=0.0,
            estimated_cost=matched_est,
            status="pending"
        ))

    # 4. Shopping list
    raw_shopping = raw_data.get("shopping_checklist", [])
    if not raw_shopping:
        raw_shopping = generate_deterministic_demo_plan(req)["shopping_checklist"]
    shopping_list: List[ShoppingItem] = []
    for s in raw_shopping:
        shopping_list.append(ShoppingItem(
            id=f"shop-{uuid.uuid4().hex[:8]}",
            category=str(s.get("category", "General Supplies")),
            item=str(s.get("item", "Supply item")),
            quantity=str(s.get("quantity", "As required")),
            purchased=False
        ))

    return EventPlan(
        id=event_id,
        created_at=now_iso,
        updated_at=now_iso,
        name=req.name,
        event_type=req.event_type,
        event_date=req.event_date,
        location=req.location or "",
        guest_count=req.guest_count,
        total_budget=req.budget,
        currency=req.currency,
        theme=req.theme or "",
        food_preference=req.food_preference or "",
        cultural_preference=req.cultural_preference or "",
        venue_preference=req.venue_preference or "",
        priority=req.priority or "balanced",
        additional_notes=req.additional_notes or "",
        tagline=str(raw_data.get("tagline", "You celebrate. EventPilot handles the planning.")),
        overview=str(raw_data.get("overview", "")),
        theme_ideas=[str(x) for x in raw_data.get("theme_ideas", [])],
        activities_schedule=raw_data.get("activities_schedule", []),
        budget_items=budget_items,
        total_estimated_budget=accumulated_estimated,
        remaining_balance=remaining_balance,
        is_over_budget=is_over_budget,
        budget_breakdown_by_category=category_totals,
        tasks=tasks,
        vendors=vendors,
        shopping_list=shopping_list,
        food_catering_suggestions=[str(x) for x in raw_data.get("food_catering_suggestions", [])],
        contingency_recommendations=[str(x) for x in raw_data.get("contingency_recommendations", [])],
        cost_saving_suggestions=[str(x) for x in raw_data.get("cost_saving_suggestions", [])],
        potential_risks=[str(x) for x in raw_data.get("potential_risks", [])],
        ai_generated=ai_generated,
        model_used=model_name
    )

def recalculate_event_plan(plan: EventPlan) -> EventPlan:
    """Recalculate budget totals and task overdue statuses deterministically."""
    total_est = sum(round(item.estimated_cost, 2) for item in plan.budget_items)
    plan.total_estimated_budget = round(total_est, 2)
    plan.remaining_balance = round(plan.total_budget - plan.total_estimated_budget, 2)
    plan.is_over_budget = plan.total_estimated_budget > plan.total_budget
    
    cat_totals: Dict[str, float] = {}
    for item in plan.budget_items:
        cat_totals[item.category] = round(cat_totals.get(item.category, 0.0) + item.estimated_cost, 2)
    plan.budget_breakdown_by_category = cat_totals

    today = date.today()
    for task in plan.tasks:
        try:
            task_dt = datetime.strptime(task.due_date, "%Y-%m-%d").date()
            task.is_overdue = (task_dt < today) and (not task.completed)
        except Exception:
            pass

    plan.updated_at = datetime.now().isoformat()
    return plan
