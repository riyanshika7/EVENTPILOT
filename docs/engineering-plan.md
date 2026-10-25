# EventPilot AI — Engineering Plan & Implementation Strategy

## 1. Baseline Audit Findings
- **Backend Architecture:** Monolithic routing inside `backend/main.py` (215 lines) combining API endpoints, CORS, static mounts, and lifespan.
- **AI Service (`backend/ai_service.py`):** Single file handling status checks and generation for Ollama and OpenAI-compatible hosted endpoints. Statement coverage is 24% because remote paths are unmocked in test suites.
- **Frontend Architecture:** `frontend/app.js` is currently a single large file (908 lines) containing API calls, state management, BudgetGuard logic, timeline handling, and DOM rendering.
- **Accessibility:** Skip-link is missing in `frontend/index.html`; ARIA live regions need explicit roles for dynamic planning status updates.
- **CORS & Portability:** Single hardcoded origin behavior; backend base URL needs clean fallback configuration for separate deployments.
- **Backend Coverage:** Current statement coverage is 74% (493 statements, 127 missed).

## 2. Prioritized Implementation Decisions
1. **Frontend Modularity & Resilience:**
   - Extract API and state logic into dedicated ES modules (`frontend/modules/api.js`, `frontend/modules/budget.js`, `frontend/modules/timeline.js`) while maintaining zero-build vanilla JS compatibility.
   - Add a high-contrast, accessible "Skip to main content" link and ARIA live regions for async generation states.
2. **AI Provider Testing & Robustness:**
   - Add unit tests for `backend/ai_service.py` covering rate limits (HTTP 429), timeouts, malformed JSON envelopes, and token usage extractions.
   - Boost backend coverage to 85%+.
3. **BudgetGuard & LazyTimeline Property-Based / Edge-Case Tests:**
   - Add parameterized tests covering boundary budgets, zero/negative inputs, short 1-day event preparation, and multi-year leap day offsets.
4. **Render Deployment & Sentry Hardening:**
   - Verify health check path and clean initialization when `SENTRY_DSN` is empty.
5. **Documentation & Final Judge Evidence:**
   - Update `docs/verification-report.md` with exact reproducibility logs, coverage metrics, and Hacktoberfest submission evidence.
