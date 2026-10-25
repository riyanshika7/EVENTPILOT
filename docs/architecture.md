# EventPilot AI — Architecture & Data Flow

This document details the actual system architecture, component boundaries, and data flows implemented in EventPilot AI.

---

## 1. System Architecture

```mermaid
graph TD
    Client["Browser (Vanilla HTML5 / CSS3 / ES6)"]
    FastAPI["FastAPI Web Service (backend/main.py)"]
    Obs["Sentry Tracing & Diagnostics (backend/observability.py)"]
    Planner["Deterministic Planner (backend/planner.py)"]
    AIService["AI Inference Adapter (backend/ai_service.py)"]
    DB[(SQLite: eventpilot.db)]
    
    subgraph External Inference
        OllamaLocal["Local Ollama (:11434)<br/>gemma2:2b / qwen2.5-coder:1.5b"]
        HostedGemma["Hosted Gemma API<br/>Groq / Together / OpenRouter (gemma2-9b-it)"]
    end

    Client -->|REST JSON / HTTP| FastAPI
    FastAPI --> Obs
    FastAPI --> Planner
    Planner --> AIService
    AIService -.->|HTTP POST| OllamaLocal
    AIService -.->|HTTPS POST (OpenAI format)| HostedGemma
    Planner -->|SQL Parameterized| DB
    DB -->|Read / Write| FastAPI
    FastAPI -->|JSON Response| Client
```

---

## 2. AI Planning Pipeline & Sentry Tracing Spans

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant API as FastAPI /api/events/generate
    participant Obs as Sentry / Diagnostics
    participant AIService as AI Service
    participant LLM as Gemma Model
    participant Planner as Planner Engine

    User->>API: POST EventCreateRequest
    API->>Obs: Start Span: event_plan.validate_input
    Obs-->>API: Validated Bounds (guests > 0, budget >= 0)
    API->>AIService: Request Gemma Plan (prompt)
    AIService->>Obs: Start Span: event_plan.model_inference
    AIService->>LLM: HTTP JSON Generate Request
    LLM-->>AIService: Structured JSON response + token metadata
    Obs-->>AIService: Close Inference Span (records duration & tokens)
    AIService-->>API: (success, parsed_data)
    API->>Obs: Start Span: event_plan.parse_output
    Obs-->>API: Pydantic Schema Validated
    API->>Planner: Deterministic Budget & Timeline Math
    Planner->>Obs: Spans: event_plan.calculate_budget & event_plan.build_timeline
    Planner-->>API: Full EventPlan object
    API-->>User: Return Validated EventPlan (HTTP 200)
```

---

## 3. SQLite Database Schema

```mermaid
erDiagram
    EVENTS {
        string id PK "UUID string"
        string name "Event Name"
        string event_type "birthday / wedding / college / etc."
        string event_date "YYYY-MM-DD"
        int guest_count "Total expected attendees"
        real total_budget "Target budget"
        real total_estimated_budget "Calculated sum of line items"
        string currency "INR, USD, EUR, GBP"
        string plan_json "Full serialized EventPlan JSON"
        string created_at "ISO 8601 timestamp"
        string updated_at "ISO 8601 timestamp"
    }
```
