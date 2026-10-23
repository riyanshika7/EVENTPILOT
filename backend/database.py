"""
Database abstraction layer for EventPilot AI.
Provides repository pattern for SQLite locally with explicit disclosure on ephemeral filesystems.
"""

import sqlite3
import json
import logging
from typing import List, Optional
from backend.config import settings
from backend.models import EventPlan, EventSummary
from backend.observability import AISpanContext

logger = logging.getLogger("eventpilot.database")

def get_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
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
    """)
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {settings.DATABASE_PATH}")

def save_event(event_plan: EventPlan) -> EventPlan:
    """Save or update an event plan."""
    with AISpanContext("event_plan.persist", f"Persist plan '{event_plan.name}' to SQLite"):
        conn = get_connection()
        cursor = conn.cursor()
        plan_dict = event_plan.model_dump()
        plan_json = json.dumps(plan_dict)
        
        cursor.execute("""
            INSERT INTO events (id, name, event_type, event_date, guest_count, total_budget, total_estimated_budget, currency, plan_json, created_at, updated_at)
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
        """, (
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
            event_plan.updated_at
        ))
        conn.commit()
        conn.close()
        return event_plan

def get_all_events() -> List[EventSummary]:
    """Retrieve all event summaries ordered by recency."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    summaries = []
    for row in rows:
        plan_data = json.loads(row["plan_json"])
        tasks = plan_data.get("tasks", [])
        completed = sum(1 for t in tasks if t.get("completed", False))
        summaries.append(EventSummary(
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
            completed_task_count=completed
        ))
    conn.close()
    return summaries

def get_event_by_id(event_id: str) -> Optional[EventPlan]:
    """Retrieve single full event plan."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT plan_json FROM events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = json.loads(row["plan_json"])
    return EventPlan(**data)

def delete_event_by_id(event_id: str) -> bool:
    """Delete an event plan."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()
    return rows_deleted > 0
