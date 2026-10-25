# Demo Data Lab & Judge Sandbox Guide 🦥

The **Demo Data Lab** provides a sandbox for hackathon judges and evaluators to safely test EventPilot AI using representative college event datasets and custom CSV imports without touching or risking production databases.

---

## 1. Features & Safety Architecture

- **Pre-validated College Symposium Dataset:** Accessible via `GET /api/demo-lab/sample`.
- **Safe CSV Budget Import:** Accessible via `POST /api/demo-lab/import-budget-csv`.
- **Strict Row & Size Limits:**
  - Maximum upload size: **100 KB**.
  - Maximum row count: **100 rows**.
- **CSV Formula Injection Sanitization:** All cell inputs beginning with formula triggers (`=`, `+`, `-`, `@`) are stripped or prepended with an apostrophe (`'`) to neutralize spreadsheet command execution.
- **Strict Allowlisted Columns:** Only `category`, `item_name`, `estimated_cost`, and `notes` are accepted. Any unexpected or malicious headers are caught and cleanly rejected.

---

## 2. Testing via the API

### A. Fetch Pre-configured College Symposium Dataset
```bash
curl -X GET http://localhost:8000/api/demo-lab/sample
```

**Response:**
```json
{
  "name": "Nexus 2026: Annual Inter-College AI Symposium",
  "event_type": "college",
  "event_date": "2026-11-20",
  "location": "Main Campus Auditorium & Media Quad",
  "guest_count": 180,
  "budget": 45000.0,
  "currency": "INR",
  "priority": "balanced",
  "venue_preference": "campus",
  "food_preference": "vegetarian"
}
```

### B. Upload a Custom Budget CSV for Validation
```bash
curl -X POST http://localhost:8000/api/demo-lab/import-budget-csv \
  -H "Content-Type: application/json" \
  -d '{
    "csv_content": "category,item_name,estimated_cost,notes\nVenue,Auditorium hire,12000,Includes sound\nCatering,Lunch packets,18000,Veg lunch"
  }'
```

**Response:**
```json
{
  "valid": true,
  "total_rows": 2,
  "parsed_items": [
    {
      "category": "Venue",
      "item_name": "Auditorium hire",
      "estimated_cost": 12000.0,
      "notes": "Includes sound"
    },
    {
      "category": "Catering",
      "item_name": "Lunch packets",
      "estimated_cost": 18000.0,
      "notes": "Veg lunch"
    }
  ],
  "errors": [],
  "total_amount": 30000.0
}
```

---

## 3. Automated Test Verification

This sandbox is covered by unit tests in [`tests/test_demo_lab.py`](tests/test_demo_lab.py):
- `test_demo_lab_sample_endpoint`: Verifies sample data structure.
- `test_demo_lab_import_budget_csv_valid`: Verifies parsing of valid CSV rows.
- `test_demo_lab_import_budget_csv_invalid_header`: Verifies rejection of missing or corrupt column headers.
- `test_demo_lab_import_budget_csv_empty`: Verifies rejection of empty file inputs.
- `test_demo_lab_import_budget_csv_formula_injection_sanitization`: Verifies neutralization of formula injection payloads.
