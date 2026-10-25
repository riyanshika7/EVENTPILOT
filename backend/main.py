"""
FastAPI application for EventPilot AI.
Provides REST endpoints, Sentry agent tracing, Gemma inference, and static asset serving.
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.models import EventCreateRequest, EventPlan, EventSummary
from backend.database import (
    init_db, save_event, get_all_events, get_event_by_id, delete_event_by_id
)
from backend.ai_service import check_gemma_status, generate_gemma_plan
from backend.planner import (
    build_gemma_event_prompt, generate_deterministic_demo_plan, construct_event_plan, recalculate_event_plan
)
from backend.observability import (
    init_sentry, AISpanContext, record_diagnostics_event, get_diagnostics_summary
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("eventpilot.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Sentry
    sentry_active = init_sentry()
    # Initialize Database
    init_db()
    logger.info(f"EventPilot AI started. Gemma Model: {settings.GEMMA_MODEL} | Sentry Active: {sentry_active}")
    yield
    logger.info("EventPilot AI shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GenAI-powered event planning assistant for the Hacktoberfest challenge.",
    lifespan=lifespan
)

# CORS middleware for local frontend dev & Render hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforces essential security headers across all API and static responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.get("/api/health")
async def health_check():
    """Render-compatible health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.SENTRY_ENVIRONMENT,
        "sentry_enabled": bool(settings.SENTRY_DSN)
    }

@app.get("/api/model/status")
async def model_status():
    """Live connectivity check to configured Gemma endpoint."""
    return await check_gemma_status()

from backend.demo_lab import (
    parse_and_validate_budget_csv, get_sample_college_event_data, DemoLabParseResult
)
from pydantic import BaseModel, Field

class CsvImportRequest(BaseModel):
    csv_content: str = Field(..., max_length=102400)

@app.get("/api/diagnostics")
async def diagnostics():
    """In-memory telemetry summary of recent event runs."""
    return get_diagnostics_summary()

@app.get("/api/demo-lab/sample")
async def demo_lab_sample():
    """Returns sample college event data for judge evaluation."""
    return get_sample_college_event_data()

@app.post("/api/demo-lab/import-budget-csv", response_model=DemoLabParseResult)
async def demo_lab_import_budget(payload: CsvImportRequest):
    """Safely parses and validates an uploaded budget CSV without modifying production databases."""
    return parse_and_validate_budget_csv(payload.csv_content)

@app.post("/api/events/generate", response_model=EventPlan)
async def generate_event(req: EventCreateRequest, force_demo: bool = Query(False)):
    """
    Generate a full structured event plan using the configured Gemma model.
    Instrumented with Sentry agent tracing spans.
    """
    start_time = time.perf_counter()
    logger.info(f"Plan request received for '{req.name}' ({req.event_type})")

    with AISpanContext(
        op="event_plan.generate",
        description=f"Generate plan for {req.name}",
        data={"event.name": req.name, "event.type": req.event_type, "event.guests": req.guest_count}
    ):
        # 1. Validation Span
        with AISpanContext("event_plan.validate_input", "Validate event specifications"):
            if req.guest_count <= 0:
                raise HTTPException(status_code=400, detail="Guest count must be greater than zero")
            if req.budget < 0:
                raise HTTPException(status_code=400, detail="Budget cannot be negative")

        # 2. Demo mode branch
        if force_demo or settings.AI_PROVIDER.lower() == "demo":
            demo_data = generate_deterministic_demo_plan(req)
            plan = construct_event_plan(
                req, demo_data, ai_generated=False, model_name="Rule-based Demo Generator"
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            record_diagnostics_event(
                event_name=req.name,
                outcome="demo_mode",
                duration_ms=elapsed_ms,
                model_identifier="demo",
                provider="demo"
            )
            return plan

        # 3. Model Inference Span
        prompt = build_gemma_event_prompt(req)
        success, parsed_data, token_usage, err_msg = await generate_gemma_plan(prompt)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        active_model = settings.MODEL_NAME or settings.GEMMA_MODEL
        if success and parsed_data:
            with AISpanContext("event_plan.parse_output", "Parse and validate model structured output"):
                plan = construct_event_plan(
                    req, parsed_data, ai_generated=True, model_name=active_model
                )
            
            record_diagnostics_event(
                event_name=req.name,
                outcome="success",
                duration_ms=elapsed_ms,
                model_identifier=active_model,
                provider=settings.AI_PROVIDER,
                token_usage=token_usage
            )
            return plan
        else:
            # When live inference fails, return a clear actionable error rather than silently fabricating output
            logger.warning(f"AI model call failed or timed out: {err_msg}")
            record_diagnostics_event(
                event_name=req.name,
                outcome="failed",
                duration_ms=elapsed_ms,
                model_identifier=active_model,
                provider=settings.AI_PROVIDER,
                error=err_msg
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "ModelInferenceFailed",
                    "message": f"Inference failed via provider '{settings.AI_PROVIDER}' for model '{active_model}'.",
                    "cause": err_msg,
                    "suggestion": "Verify that your model service is active or enable 'Instant Demo Mode' to test deterministic planning without live AI inference."
                }
            )

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
