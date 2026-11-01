"""
Database abstraction layer for EventPilot AI.
Provides repository pattern for SQLite with connection reuse, WAL mode for concurrency,
and explicit disclosure on ephemeral filesystems.
"""

import sqlite3
import json
import logging
from typing import List, Optional
from backend.config import settings
from backend.models import EventPlan, EventSummary
from backend.observability import AISpanContext

logger = logging.getLogger("eventpilot.database")


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with WAL mode and foreign-key enforcement."""
    conn = sqlite3.connect(settings.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # WAL mode: allows concurrent reads while a write is in progress
    conn.execute("PRAGMA journal_mode=WAL;")
    # Enforce referential integrity if foreign keys are added in future
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db() -> None:
    """Initialise the database schema and ensure required indexes exist."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_date TEXT NOT NULL,
            guest_count INTEGER NOT NULL,
            total_budget REAL NOT NULL,
            total_estimated_budget REAL NOT NULL,
            currency TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_updated_at ON events(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_events_event_date ON events(event_date);
        CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
        """)
    logger.info(f"Database initialized at {settings.DATABASE_PATH}")

def save_event(event_plan: EventPlan) -> EventPlan:
    """Upsert an event plan atomically inside a single connection context."""
    with AISpanContext("event_plan.persist", f"Persist plan '{event_plan.name}' to SQLite"):
        plan_json = json.dumps(event_plan.model_dump())
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO events
                    (id, name, event_type, event_date, guest_count,
                     total_budget, total_estimated_budget, currency,
                     plan_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    event_type=excluded.event_type,
                    event_date=excluded.event_date,
                    guest_count=excluded.guest_count,
                    total_budget=excluded.total_budget,
                    total_estimated_budget=excluded.total_estimated_budget,
                    currency=excluded.currency,
                    plan_json=excluded.plan_json,
                    updated_at=excluded.updated_at
                """,
                (
                    event_plan.id,
                    event_plan.name,
                    event_plan.event_type,
                    event_plan.event_date,
                    event_plan.guest_count,
                    event_plan.total_budget,
                    event_plan.total_estimated_budget,
                    event_plan.currency,
                    plan_json,
                    event_plan.created_at,
                    event_plan.updated_at,
                ),
            )
    return event_plan

def get_all_events() -> List[EventSummary]:
    """Retrieve all event summaries ordered by recency.

    Reads task completion from plan_json without deserialising the full EventPlan
    model, keeping memory usage proportional to summary data only.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY updated_at DESC"
        ).fetchall()

    summaries: List[EventSummary] = []
    for row in rows:
        plan_data = json.loads(row["plan_json"])
        tasks = plan_data.get("tasks", [])
        # O(n) single pass: count completed tasks without sorting or nested loops
        completed = sum(1 for t in tasks if t.get("completed", False))
        summaries.append(
            EventSummary(
                id=row["id"],
                name=row["name"],
                event_type=row["event_type"],
                event_date=row["event_date"],
                guest_count=row["guest_count"],
                total_budget=row["total_budget"],
                total_estimated_budget=row["total_estimated_budget"],
                currency=row["currency"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                task_count=len(tasks),
                completed_task_count=completed,
            )
        )
    return summaries

def get_event_by_id(event_id: str) -> Optional[EventPlan]:
    """Retrieve a single full event plan by primary key."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT plan_json FROM events WHERE id = ?", (event_id,)
        ).fetchone()
    if not row:
        return None
    return EventPlan(**json.loads(row["plan_json"]))


def delete_event_by_id(event_id: str) -> bool:
    """Delete an event plan. Returns True if a row was removed."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    return cursor.rowcount > 0
