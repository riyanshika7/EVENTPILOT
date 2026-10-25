import csv
import io
import re
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

class DemoLabBudgetRow(BaseModel):
    category: str = Field(..., max_length=60)
    item_name: str = Field(..., max_length=120)
    estimated_cost: float = Field(..., ge=0, le=10000000)
    notes: str = Field(default="", max_length=250)

class DemoLabVendorRow(BaseModel):
    category: str = Field(..., max_length=60)
    vendor_name: str = Field(default="", max_length=120)
    quoted_cost: float = Field(default=0.0, ge=0, le=10000000)
    status: str = Field(default="pending", max_length=20)

class DemoLabParseResult(BaseModel):
    valid: bool
    total_rows: int
    parsed_items: List[Dict[str, Any]] = []
    errors: List[str] = []
    total_amount: float = 0.0

def sanitize_csv_cell(value: str) -> str:
    """Strip potential formula execution prefixes (=, +, -, @) to prevent CSV injection."""
    cleaned = str(value).strip()
    if cleaned and cleaned[0] in ['=', '+', '-', '@']:
        cleaned = "'" + cleaned
    return cleaned

def parse_and_validate_budget_csv(csv_text: str, max_rows: int = 100) -> DemoLabParseResult:
    """
    Safely parses a CSV containing budget line items with strict allowlist and row caps.
    Expected header: category, item_name, estimated_cost, notes
    """
    errors: List[str] = []
    parsed: List[Dict[str, Any]] = []
    total_amount: float = 0.0

    if not csv_text or not csv_text.strip():
        return DemoLabParseResult(valid=False, total_rows=0, errors=["CSV payload is empty."])

    # Enforce input string size limit (e.g. 100 KB max)
    if len(csv_text.encode('utf-8')) > 102400:
        return DemoLabParseResult(valid=False, total_rows=0, errors=["File exceeds 100 KB size limit."])

    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        if not reader.fieldnames:
            return DemoLabParseResult(valid=False, total_rows=0, errors=["Missing CSV header row."])

        # Normalize headers
        normalized_headers = [h.strip().lower() for h in reader.fieldnames if h]
        required_cols = {"category", "item_name", "estimated_cost"}
        if not required_cols.issubset(set(normalized_headers)):
            return DemoLabParseResult(
                valid=False,
                total_rows=0,
                errors=[f"CSV must contain columns: {', '.join(required_cols)}. Found: {', '.join(normalized_headers)}"]
            )

        row_count = 0
        for idx, row in enumerate(reader, start=2): # 1 is header
            row_count += 1
            if row_count > max_rows:
                errors.append(f"Row limit exceeded. Maximum permitted rows: {max_rows}.")
                break

            # Find matching keys case-insensitively
            row_dict = {k.strip().lower(): v for k, v in row.items() if k}
            cat = sanitize_csv_cell(row_dict.get("category", ""))
            item = sanitize_csv_cell(row_dict.get("item_name", ""))
            cost_str = str(row_dict.get("estimated_cost", "")).strip().replace(",", "")
            notes = sanitize_csv_cell(row_dict.get("notes", ""))

            if not cat or not item:
                errors.append(f"Row {idx}: 'category' and 'item_name' are required.")
                continue

            try:
                cost_val = float(cost_str)
                if cost_val < 0 or cost_val > 10000000:
                    errors.append(f"Row {idx}: cost {cost_val} is out of permitted range (0 to 10,000,000).")
                    continue
            except ValueError:
                errors.append(f"Row {idx}: invalid numerical cost value '{cost_str}'.")
                continue

            total_amount += cost_val
            parsed.append({
                "category": cat,
                "item_name": item,
                "estimated_cost": round(cost_val, 2),
                "notes": notes
            })

    except Exception as e:
        return DemoLabParseResult(valid=False, total_rows=0, errors=[f"Malformed CSV: {str(e)}"])

    return DemoLabParseResult(
        valid=(len(errors) == 0 and len(parsed) > 0),
        total_rows=len(parsed),
        parsed_items=parsed,
        errors=errors,
        total_amount=round(total_amount, 2)
    )

def get_sample_college_event_data() -> Dict[str, Any]:
    """Returns a realistic, pre-validated college club symposium event dataset for judges."""
    return {
        "name": "Nexus 2026: Annual Inter-College AI Symposium",
        "event_type": "college",
        "event_date": "2026-11-20",
        "location": "Main Campus Auditorium & Media Quad",
        "guest_count": 180,
        "budget": 45000.0,
        "currency": "INR",
        "priority": "balanced",
        "venue_preference": "campus",
        "food_preference": "vegetarian",
        "theme": "Retro-Futuristic Tech & Botanical Greenery",
        "cultural_preference": "Acoustic student band opening & regional street food stalls",
        "additional_notes": "Sound curfew at 9:30 PM. Needs 10 lapel mics and 3 extension boxes. Certifications for hackathon participants."
    }
