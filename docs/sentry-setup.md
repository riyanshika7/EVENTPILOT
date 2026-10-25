# Sentry Agent Tracing — Setup & Verification Guide

EventPilot AI integrates official Sentry Python SDK agent tracing (`sentry-sdk[fastapi]>=2.7.0`) to provide granular visibility into every step of the AI planning workflow.

---

## 1. Trace Hierarchy & Instrumented Spans

Every event plan generation (`POST /api/events/generate`) produces an end-to-end trace with child spans:

```
event_plan.generate [Root Transaction]
  ├── event_plan.validate_input       (validates guest count, budget bounds, required fields)
  ├── event_plan.model_inference      (records AI model tag, character length, latency, tokens)
  ├── event_plan.parse_output         (validates structured JSON against Pydantic schema)
  ├── event_plan.calculate_budget     (deterministic budget allocations and reconciliation)
  └── event_plan.build_timeline       (deterministic milestone scheduling and overdue check)
```

Persistence operations (`POST /api/events`) trigger:
```
event_plan.persist                   (SQLite database transaction recording plan)
```

---

## 2. Configuration Walkthrough

### Step 1: Create a Sentry Project
1. Go to [sentry.io](https://sentry.io) and create a free account.
2. Create a new project and select **Python / FastAPI**.
3. Copy your project DSN: `https://<public-key>@<org>.ingest.sentry.io/<project-id>`

### Step 2: Set Environment Variables
Add your DSN to your local `.env` or Render environment variables:
```ini
SENTRY_DSN="https://examplePublicKey@o0.ingest.sentry.io/1234567"
SENTRY_ENVIRONMENT="production"
SENTRY_TRACES_SAMPLE_RATE=1.0
```

### Step 3: Trigger a Trace
1. Start the server: `python -m uvicorn backend.main:app --port 8000`
2. Open `http://localhost:8000`, click **"Plan an event ↗"**, fill out the form, and submit.
3. Open your Sentry Dashboard under **Performance -> Traces**.
4. Locate the transaction for `POST /api/events/generate` and observe the connected child spans.

---

## 3. Local In-Memory Diagnostics (Zero-Account Verification)

For local development without an active internet connection or Sentry DSN, EventPilot AI automatically records all workflow measurements into a rolling in-memory buffer accessible at:
```
GET http://localhost:8000/api/diagnostics
```

**Example Output:**
```json
{
  "total_runs": 3,
  "success_rate_percent": 100.0,
  "avg_duration_ms": 420.5,
  "min_duration_ms": 380.1,
  "max_duration_ms": 460.9,
  "recent_events": [
    {
      "timestamp": 1729860000.0,
      "event_name": "Maya & Kabir's Sunset Sangeet",
      "outcome": "success",
      "duration_ms": 420.5,
      "model": "gemma2:2b",
      "provider": "ollama",
      "tokens": { "prompt_tokens": 320, "completion_tokens": 480, "total_tokens": 800 }
    }
  ],
  "sentry_enabled": false,
  "sentry_environment": "development"
}
```
