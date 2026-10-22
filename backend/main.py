import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.models import EventCreateRequest, EventPlan, EventSummary
from backend.database import (
    init_db, save_event, get_all_events, get_event_by_id, delete_event_by_id
)
from backend.ai_service import check_ollama_status, generate_raw_event_plan
from backend.planner import (
    build_prompt_for_event, generate_fallback_plan_data, construct_event_plan, recalculate_event_plan
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("eventpilot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    logger.info(f"Initialized database at {settings.DATABASE_PATH}")
    yield
    # Shutdown logic if needed

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GenAI-powered event planning assistant for the Hacktoberfest challenge.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.get("/api/model/status")
async def model_status():
    status_info = await check_ollama_status()
    return status_info

@app.post("/api/events/generate", response_model=EventPlan)
async def generate_event(req: EventCreateRequest, force_demo: bool = Query(False)):
    """
    Generate a full structured event plan.
    Attempts local Ollama generation first. If Ollama is unavailable or fails,
    returns deterministic fallback data clearly tagged.
    """
    logger.info(f"Received generation request for '{req.name}' ({req.event_type})")
    
    if force_demo:
        fallback_data = generate_fallback_plan_data(req)
        plan = construct_event_plan(req, fallback_data, ai_generated=False, model_name="Rule-based Deterministic Planner (Demo Mode)")
        return plan

    prompt = build_prompt_for_event(req)
    success, parsed_data, err_msg = await generate_raw_event_plan(prompt)

    if success and parsed_data:
        logger.info(f"Successfully generated event plan using {settings.OLLAMA_MODEL}")
        plan = construct_event_plan(req, parsed_data, ai_generated=True, model_name=settings.OLLAMA_MODEL)
    else:
        logger.warning(f"Ollama generation fallback triggered: {err_msg}")
        fallback_data = generate_fallback_plan_data(req)
        plan = construct_event_plan(
            req, 
            fallback_data, 
            ai_generated=False, 
            model_name=f"Deterministic Fallback Planner (Ollama was unavailable: {err_msg[:60]}...)"
        )
    
    return plan

@app.post("/api/events", response_model=EventPlan, status_code=status.HTTP_201_CREATED)
async def create_or_save_event(plan: EventPlan):
    """Save an event plan to SQLite database."""
    plan = recalculate_event_plan(plan)
    saved = save_event(plan)
    return saved

@app.get("/api/events", response_model=List[EventSummary])
async def list_events():
    """List all saved events."""
    return get_all_events()

@app.get("/api/events/{event_id}", response_model=EventPlan)
async def get_event(event_id: str):
    """Fetch an event plan by ID."""
    plan = get_event_by_id(event_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Event not found")
    return plan

@app.put("/api/events/{event_id}", response_model=EventPlan)
async def update_event(event_id: str, updated_plan: EventPlan):
    """Update an existing event plan."""
    existing = get_event_by_id(event_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")
    updated_plan.id = event_id
    recalculated = recalculate_event_plan(updated_plan)
    saved = save_event(recalculated)
    return saved

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: str):
    """Delete an event from SQLite."""
    deleted = delete_event_by_id(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully", "id": event_id}

# Mount frontend directory for static serving
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))
