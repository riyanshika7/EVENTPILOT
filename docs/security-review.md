# EventPilot AI — Security Review & Risk Assessment

This review documents the security postures, mitigations, and verification tests implemented in EventPilot AI.

---

## 1. Threat Analysis & Mitigations

| Threat Category | Identified Risk | Mitigation Implemented | Verification Evidence |
|---|---|---|---|
| **Injection (SQLi)** | Malicious SQL syntax in event fields | All SQLite operations use parameterized SQL (`?` placeholders) with strictly typed bindings in `backend/database.py`. No string concatenations. | `test_save_and_retrieve_event_lifecycle` passed |
| **Cross-Site Scripting (XSS)** | Injection of script tags via user-generated or LLM-generated strings | HTML responses are served statically. Client-side DOM creation uses `escapeHtml()` and safe assignment properties (`textContent`) before inserting strings into the DOM. | Code audited in `frontend/app.js` |
| **Model Hallucination / Silent Fabrication** | Failed AI calls masquerading as successful generations | Removed silent fallbacks. Failed inference returns a clear HTTP 502 with actionable cause. Demo mode is explicitly labeled. | `test_generate_live_inference_failure_returns_bad_gateway_no_silent_fallback` passed |
| **Clickjacking / MIME Sniffing** | Framing or content sniffing attacks | Middleware injects `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`. | Verified in `test_health_endpoint` header check |
| **Credential & Privacy Leakage** | API keys or user PII leaked to logs or external tracing | Sentry initialized with `send_default_pii=False`. Spans capture only operation metadata (duration, token counts, model tags). `.env` is strictly Git-ignored. | Verified in `backend/observability.py` and `.gitignore` |
| **Denial of Service / Unbounded Input** | Excessively large budgets, negative guests, or unbounded strings | Strict Pydantic validations (`Field(gt=0, le=50000)`, `Field(ge=0)`), HTTP client timeouts (60s default). | `test_generate_validation_failure` passed |

---

## 2. Limitations & Disclosures

1. **Single-User Workspace:** EventPilot AI is architected as an event planner workspace for a single organizer or household. It currently does not enforce multi-tenant authentication or login sessions.
2. **Ephemeral Production Storage on Free Tier:** When deployed to Render's free tier, `eventpilot.db` resides on an ephemeral container filesystem that resets on inactivity sleep. For production durability, an external database connection string should be provided via `DATABASE_URL`.
