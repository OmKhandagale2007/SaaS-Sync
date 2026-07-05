"""
CSV parsing lives here, using pandas instead of hand-rolled string splitting.

This is a deliberate choice for anyone using this project to build data/ML
skills: pandas is the tool you'll reach for constantly for tabular data
wrangling, and the patterns here (dtype coercion, column validation, cleaning
messy input) show up in almost every real data pipeline, not just this demo.
"""
import io
import re

import pandas as pd

REQUIRED_COLUMNS = ["Customer Name", "Email", "Phone", "Product", "Amount", "Due Date"]


class CsvValidationError(Exception):
    pass


def _normalize_date(value: str) -> str:
    if not value or pd.isna(value):
        return ""
    value = str(value).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", value)
    if m:
        month, day, year = m.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return value


def parse_csv_text(raw_text: str) -> list[dict]:
    """Parse raw CSV text into a list of clean row dicts. Raises
    CsvValidationError with a human-readable message on bad input."""
    if not raw_text or not raw_text.strip():
        raise CsvValidationError("No CSV data provided.")

    try:
        df = pd.read_csv(io.StringIO(raw_text), dtype=str, keep_default_na=False)
    except Exception as exc:  # pandas raises many different error types
        raise CsvValidationError(f"Could not parse CSV: {exc}") from exc

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise CsvValidationError(
            f"CSV is missing required column(s): {', '.join(missing)}. "
            f"Expected headers: {', '.join(REQUIRED_COLUMNS)}"
        )

    if df.empty:
        raise CsvValidationError("CSV parsed but contained no rows.")

    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "customer_name": (r.get("Customer Name") or "").strip(),
                "email": (r.get("Email") or "").strip().lower(),
                "phone": (r.get("Phone") or "").strip(),
                "product": (r.get("Product") or "").strip(),
                "amount": (r.get("Amount") or "").strip(),
                "due_date": _normalize_date(r.get("Due Date") or ""),
            }
        )
    return rows
