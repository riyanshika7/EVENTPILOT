from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

class EventCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    event_type: str = Field(..., description="birthday, wedding, college, community, or custom")
    event_date: str = Field(..., description="YYYY-MM-DD")
    location: Optional[str] = Field(default="", max_length=120)
    guest_count: int = Field(..., gt=0, le=50000)
    budget: float = Field(..., ge=0)
    currency: str = Field(default="INR", max_length=6)
    theme: Optional[str] = Field(default="", max_length=200)
    food_preference: Optional[str] = Field(default="vegetarian", description="vegetarian, vegan, non_veg, custom")
    cultural_preference: Optional[str] = Field(default="", max_length=200)
    venue_preference: Optional[str] = Field(default="undecided", description="home, outdoor, banquet, campus, undecided")
    priority: Optional[str] = Field(default="balanced", description="cost_saving, balanced, premium")
    additional_notes: Optional[str] = Field(default="", max_length=1000)

class BudgetItem(BaseModel):
    id: str
    category: str
    item_name: str
    estimated_cost: float
    actual_cost: Optional[float] = 0.0
    notes: Optional[str] = ""

class TaskItem(BaseModel):
    id: str
    title: str
    description: str
    phase: str  # e.g., "1 Month Before", "2 Weeks Before", "Week Of", "Day Of", "Post Event"
    due_date: str  # YYYY-MM-DD
    days_before_event: int
    priority: str  # high, medium, low
    completed: bool = False
    is_overdue: Optional[bool] = False

class VendorItem(BaseModel):
    id: str
    category: str  # catering, decoration, venue, photography, invitations, music, supplies, etc.
    recommended_scope: str
    key_questions: List[str] = []
    vendor_name: Optional[str] = ""
    quoted_cost: Optional[float] = 0.0
    estimated_cost: float = 0.0
    status: str = "pending"  # pending, contacted, booked

class ShoppingItem(BaseModel):
    id: str
    category: str
    item: str
    quantity: str
    purchased: bool = False

class EventPlan(BaseModel):
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Input metadata
    name: str
    event_type: str
    event_date: str
    location: str = ""
    guest_count: int
    total_budget: float
    currency: str = "INR"
    theme: str = ""
    food_preference: str = ""
    cultural_preference: str = ""
    venue_preference: str = ""
    priority: str = "balanced"
    additional_notes: str = ""
    
    # AI structured content
    tagline: str = "Relax and celebrate"
    overview: str
    theme_ideas: List[str] = []
    activities_schedule: List[Dict[str, str]] = []  # time, activity, notes
    budget_items: List[BudgetItem] = []
    total_estimated_budget: float = 0.0
    remaining_balance: float = 0.0
    is_over_budget: bool = False
    budget_breakdown_by_category: Dict[str, float] = {}
    tasks: List[TaskItem] = []
    vendors: List[VendorItem] = []
    shopping_list: List[ShoppingItem] = []
    food_catering_suggestions: List[str] = []
    contingency_recommendations: List[str] = []
    cost_saving_suggestions: List[str] = []
    potential_risks: List[str] = []
    ai_generated: bool = True
    model_used: str = "qwen2.5-coder:1.5b"

class EventSummary(BaseModel):
    id: str
    name: str
    event_type: str
    event_date: str
    guest_count: int
    total_budget: float
    total_estimated_budget: float
    currency: str
    created_at: str
    updated_at: str
    task_count: int
    completed_task_count: int
