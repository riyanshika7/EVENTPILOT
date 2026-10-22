import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from backend.models import (
    EventCreateRequest, EventPlan, BudgetItem, TaskItem, VendorItem, ShoppingItem
)

def build_prompt_for_event(req: EventCreateRequest) -> str:
    """Build a concise, highly structured prompt to produce clean JSON from open-weight models."""
    return f"""You are EventPilot AI, an expert event planner designed for effortless, sloth-friendly event planning.
Plan a complete event with these exact details:
- Event Name: {req.name}
- Type: {req.event_type}
- Date: {req.event_date}
- Guest Count: {req.guest_count} people
- Total Budget: {req.currency} {req.budget}
- Location/City: {req.location or "Not specified"}
- Food Preference: {req.food_preference}
- Theme/Vibe: {req.theme or "Fun, relaxed, memorable"}
- Cultural Preference: {req.cultural_preference or "None specified"}
- Venue Preference: {req.venue_preference}
- Planning Priority: {req.priority}
- Special Notes: {req.additional_notes or "None"}

Generate realistic suggestions tailored to this budget and guest count. Keep item proportions realistic. Do NOT invent real vendor phone numbers or fake company quotes.

OUTPUT ONLY A VALID JSON OBJECT WITH EXACTLY THESE KEYS (do not include markdown ticks, do not include prose):
{{
  "tagline": "short catchy tagline",
  "overview": "2-3 sentences summarizing the event concept and atmosphere",
  "theme_ideas": ["3-5 creative, realistic decoration or style ideas"],
  "activities_schedule": [
    {{"time": "06:00 PM", "activity": "Welcome & Mocktails", "notes": "Casual mingling with background music"}},
    {{"time": "07:30 PM", "activity": "Dinner & Celebrations", "notes": "Buffet style catering"}},
    {{"time": "09:00 PM", "activity": "Games & Cake Cutting", "notes": "Photo moments"}}
  ],
  "budget_breakdown": [
    {{"category": "Venue", "item_name": "Venue space / Hall hire or setup", "percentage": 25, "notes": "Includes basic seating"}},
    {{"category": "Food & Catering", "item_name": "Meals and refreshments for guests", "percentage": 35, "notes": "Portions planned for guest count"}},
    {{"category": "Decor & Theme", "item_name": "Balloons, lighting, centerpieces", "percentage": 15, "notes": "Eco-friendly options"}},
    {{"category": "Entertainment", "item_name": "Music, games, sound system", "percentage": 10, "notes": "Playlist & party host"}},
    {{"category": "Photography", "item_name": "Event photos & memory capture", "percentage": 8, "notes": "Captures highlights"}},
    {{"category": "Contingency", "item_name": "Buffer for unexpected needs", "percentage": 7, "notes": "Emergency cushion"}}
  ],
  "timeline_tasks": [
    {{"title": "Book Venue & Finalize Date", "description": "Confirm reservation and payment deposit", "days_before": 30, "priority": "high", "phase": "1 Month Before"}},
    {{"title": "Send Invitations & Collect RSVPs", "description": "Share digital invites via WhatsApp or email", "days_before": 21, "priority": "high", "phase": "3 Weeks Before"}},
    {{"title": "Confirm Food Menu & Headcount", "description": "Coordinate with caterer on dietary needs", "days_before": 10, "priority": "medium", "phase": "1-2 Weeks Before"}},
    {{"title": "Purchase Decorations & Supplies", "description": "Collect party props, disposables, lighting", "days_before": 5, "priority": "medium", "phase": "Week Of Event"}},
    {{"title": "Setup Venue & Sound Check", "description": "Arrange seating, check playlist and lighting", "days_before": 0, "priority": "high", "phase": "Day Of Event"}}
  ],
  "vendor_categories": [
    {{"category": "Catering", "recommended_scope": "Buffet meal with appetizers and drinks", "key_questions": ["What is minimum guarantee count?", "Do you provide serving staff and cutlery?"]}},
    {{"category": "Venue / Space", "recommended_scope": "Capacity for guest count with sound support", "key_questions": ["Is outside food permitted?", "What is curfew time?"]}},
    {{"category": "Decorations", "recommended_scope": "Backdrop, photo-booth, ambient lighting", "key_questions": ["Is setup and cleanup included?", "Can we use tape/pins?"]}},
    {{"category": "Photography", "recommended_scope": "Coverage of core celebration and candid guest shots", "key_questions": ["How many edited photos are delivered?", "Turnaround time?"]}}
  ],
  "shopping_checklist": [
    {{"category": "Decorations", "item": "Eco-friendly balloons & streamers", "quantity": "1 kit"}},
    {{"category": "Food & Cake", "item": "Custom celebration cake", "quantity": "1 (2-3 kg)"}},
    {{"category": "Supplies", "item": "Plates, cups, napkins", "quantity": "Sets for guests"}},
    {{"category": "Entertainment", "item": "Party games & prop kit", "quantity": "1 set"}}
  ],
  "food_catering_suggestions": [
    "Signature welcome mocktail",
    "Finger-food appetizers before the main meal",
    "Balanced main buffet respecting dietary choices",
    "Dessert counter or celebratory dessert"
  ],
  "contingency_recommendations": [
    "Keep 5-10% budget reserve for last-minute supplies.",
    "Have an indoor backup plan in case of weather changes.",
    "Designate a friend or helper as on-the-day point of contact."
  ],
  "cost_saving_suggestions": [
    "Opt for elegant digital invites instead of printed cards.",
    "Curate a personalized streaming playlist instead of booking a full DJ.",
    "Focus decorations on one photo-worthy focal backdrop rather than the entire room."
  ],
  "potential_risks": [
    "Guests arriving late — build a 30-minute buffer into the schedule.",
    "Dietary restrictions — reconfirm vegan/allergy counts 48 hours prior."
  ]
}}
"""

def generate_fallback_plan_data(req: EventCreateRequest) -> Dict[str, Any]:
    """Provide a reliable, rule-based fallback when Ollama is unavailable or unparseable."""
    return {
        "tagline": f"Effortless {req.name} — Handled with sloth-like ease",
        "overview": f"A thoughtfully orchestrated {req.event_type} designed for {req.guest_count} guests. Planned with a focus on relaxed celebrations, balanced budgeting ({req.currency} {req.budget:,.2f}), and hassle-free coordination.",
        "theme_ideas": [
            f"Signature '{req.theme or 'Warm Earth & Sage'}' aesthetic with ambient fairy lights",
            "Cozy lounge seating area for easy mingling and relaxed conversations",
            "Minimalist photo-ready backdrop with botanical or festive accents",
            "Dedicated personalized welcome station with custom guestbook"
        ],
        "activities_schedule": [
            {"time": "05:30 PM", "activity": "Welcome & Refreshments", "notes": "Chilled drinks & ambient acoustic playlist"},
            {"time": "06:45 PM", "activity": "Opening Ceremony & Remarks", "notes": "Brief toast and group welcome"},
            {"time": "07:30 PM", "activity": "Dinner & Feasting", "notes": f"Main course buffet serving {req.food_preference} options"},
            {"time": "09:00 PM", "activity": "Celebration Highlight & Games", "notes": "Cake cutting, memorable games, and open floor"},
            {"time": "10:30 PM", "activity": "Wrap-up & Parting Favors", "notes": "Guest goodbyes and easy pack-down"}
        ],
        "budget_breakdown": [
            {"category": "Food & Catering", "item_name": f"Buffet meals & drinks ({req.food_preference})", "percentage": 35, "notes": f"Scaled for {req.guest_count} guests"},
            {"category": "Venue & Space", "item_name": "Venue hire or setup & seating", "percentage": 25, "notes": f"Suits {req.venue_preference} venue choice"},
            {"category": "Decor & Styling", "item_name": "Backdrop, floral/lighting accents, tablescapes", "percentage": 15, "notes": "Cohesive thematic styling"},
            {"category": "Entertainment & Audio", "item_name": "Sound equipment, games & celebration host", "percentage": 10, "notes": "Fun social entertainment"},
            {"category": "Photography", "item_name": "Photographer / Memory capture kit", "percentage": 8, "notes": "Candid photos & highlights"},
            {"category": "Contingency Fund", "item_name": "Buffer for last minute supplies & extras", "percentage": 7, "notes": "Guaranteed cushion against overspending"}
        ],
        "timeline_tasks": [
            {"title": "Lock in Venue and Final Date", "description": "Confirm venue booking, payment terms, and access hours", "days_before": 30, "priority": "high", "phase": "1 Month Before"},
            {"title": "Send Out Digital Invitations", "description": "Distribute invites via messaging or email with RSVP deadline", "days_before": 21, "priority": "high", "phase": "3 Weeks Before"},
            {"title": "Finalize Caterer & Food Menu", "description": f"Confirm menu items according to {req.food_preference} preferences", "days_before": 14, "priority": "high", "phase": "2 Weeks Before"},
            {"title": "Order Cake & Party Supplies", "description": "Pre-order celebratory cake, party favors, and disposable tableware", "days_before": 7, "priority": "medium", "phase": "1 Week Before"},
            {"title": "Final RSVP Count & Seating Check", "description": "Verify headcount with venue and catering team", "days_before": 3, "priority": "high", "phase": "Final Days"},
            {"title": "Day-of Setup & Music Check", "description": "Place decor, test audio equipment, and welcome first arrivals", "days_before": 0, "priority": "high", "phase": "Day of Event"}
        ],
        "vendor_categories": [
            {"category": "Food & Catering", "recommended_scope": f"Full service meal for {req.guest_count} guests", "key_questions": ["What is the per-plate pricing?", "Are cleanup and serving staff included?", "What are dietary allergy safeguards?"]},
            {"category": "Venue & Facilities", "recommended_scope": f"Comfortable venue for {req.guest_count} guests", "key_questions": ["What is the power backup availability?", "What is the noise curfew policy?", "Are tables and chairs provided?"]},
            {"category": "Decor & Lighting", "recommended_scope": "Main focal stage, entry arch, and ambient lighting", "key_questions": ["Do you handle setup and teardown?", "Can colors be customized to our palette?"]},
            {"category": "Photography & Video", "recommended_scope": "3 to 4 hours of event coverage", "key_questions": ["When will edited photos be delivered?", "Do you provide RAW or high-res cloud links?"]}
        ],
        "shopping_checklist": [
            {"category": "Decorations", "item": "Fairy lights, welcome banner, and balloons", "quantity": "1 bundle"},
            {"category": "Food & Drink", "item": "Celebratory cake and dessert snacks", "quantity": f"~{max(1, req.guest_count // 15)} kg"},
            {"category": "Dining Supplies", "item": "Plates, cutlery, cups, and napkins", "quantity": f"{req.guest_count + 10} sets"},
            {"category": "Entertainment", "item": "Party game cards, props, and spot prizes", "quantity": "3 sets"},
            {"category": "Emergency Kit", "item": "Scissors, double-sided tape, extension cords", "quantity": "1 box"}
        ],
        "food_catering_suggestions": [
            f"Pre-event welcome coolers & mocktails to greet arriving guests",
            f"Curated {req.food_preference} finger foods during the mingling period",
            "Main course buffet with 2 entrees, salad, bread, and signature rice dish",
            "Dessert bar featuring ice cream or warm traditional sweets"
        ],
        "contingency_recommendations": [
            "Keep the 7% contingency reserve untouched until the day of the event.",
            "Designate one dependable co-host to handle vendor questions on the day.",
            "Prepare a portable Bluetooth speaker and offline playlist in case of audio glitches."
        ],
        "cost_saving_suggestions": [
            "Opt for digital invitations with a Google Form or WhatsApp RSVP tracker.",
            "Create your own photo booth corner with fairy lights and simple greenery.",
            "Buy non-perishable party supplies in bulk or from wholesale local markets."
        ],
        "potential_risks": [
            "Unconfirmed RSVPs leading to catering waste or shortage — lock headcount 72 hours before.",
            "Weather variance for outdoor areas — always confirm rain or shade protection.",
            "Vendor delays — request delivery 90 minutes before guest arrival."
        ]
    }

def construct_event_plan(
    req: EventCreateRequest,
    raw_data: Dict[str, Any],
    ai_generated: bool = True,
    model_name: str = "qwen2.5-coder:1.5b"
) -> EventPlan:
    """
    Deterministically computes budget totals, task due dates, and builds the full validated EventPlan.
    Never trusts LLM for arithmetic or date math.
    """
    event_id = str(uuid.uuid4())
    now_iso = datetime.now().isoformat()
    
    # 1. Date math for tasks
    try:
        event_dt = datetime.strptime(req.event_date, "%Y-%m-%d").date()
    except Exception:
        event_dt = date.today() + timedelta(days=30)
    today = date.today()
    
    # Process tasks
    tasks: List[TaskItem] = []
    raw_tasks = raw_data.get("timeline_tasks", [])
    if not raw_tasks:
        raw_tasks = generate_fallback_plan_data(req)["timeline_tasks"]

    for idx, t in enumerate(raw_tasks):
        days_before = int(t.get("days_before", max(0, 30 - idx * 5)))
        task_due = event_dt - timedelta(days=days_before)
        is_overdue = task_due < today
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

    # Sort tasks chronologically by due date
    tasks.sort(key=lambda x: x.due_date)

    # 2. Deterministic Budget calculations
    raw_budget = raw_data.get("budget_breakdown", [])
    if not raw_budget:
        raw_budget = generate_fallback_plan_data(req)["budget_breakdown"]

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
        # Allocate proportionally to user's specified budget
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

    # Reconcile rounding to match user budget exactly
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
        raw_vendors = generate_fallback_plan_data(req)["vendor_categories"]
    
    vendors: List[VendorItem] = []
    for v in raw_vendors:
        cat = str(v.get("category", "Vendor Service"))
        # Match estimated cost from budget breakdown if available
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
        raw_shopping = generate_fallback_plan_data(req)["shopping_checklist"]
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
        tagline=str(raw_data.get("tagline", "Relax and celebrate")),
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
    """Recalculate budget totals and task overdue statuses after user updates."""
    total_est = sum(round(item.estimated_cost, 2) for item in plan.budget_items)
    plan.total_estimated_budget = round(total_est, 2)
    plan.remaining_balance = round(plan.total_budget - plan.total_estimated_budget, 2)
    plan.is_over_budget = plan.total_estimated_budget > plan.total_budget
    
    # Category totals
    cat_totals: Dict[str, float] = {}
    for item in plan.budget_items:
        cat_totals[item.category] = round(cat_totals.get(item.category, 0.0) + item.estimated_cost, 2)
    plan.budget_breakdown_by_category = cat_totals

    # Recheck task overdue statuses
    today = date.today()
    for task in plan.tasks:
        try:
            task_dt = datetime.strptime(task.due_date, "%Y-%m-%d").date()
            task.is_overdue = (task_dt < today) and (not task.completed)
        except Exception:
            pass

    plan.updated_at = datetime.now().isoformat()
    return plan
