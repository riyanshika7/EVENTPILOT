import sqlite3
import json
from typing import List, Optional, Dict, Any
from backend.config import settings
from backend.models import EventPlan, EventSummary

def get_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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

def save_event(event_plan: EventPlan) -> EventPlan:
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()
    return rows_deleted > 0
