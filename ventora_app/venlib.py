"""
venlib.py — VENTORA data-validation logic.

Kept separate from app.py (the Streamlit UI layer) so it can be unit-tested
without a Streamlit runtime. Pure functions only: no st.* calls here.
"""
import io
import pandas as pd

REQUIRED_RAW_FIELDS = ["batch_id", "item_id", "category", "received_date", "expiry_date", "qty_received"]
OPTIONAL_RAW_FIELDS = ["food_category", "selling_price", "is_promoted", "is_holiday", "shelf_life_days"]
MODEL_ONLY_FIELDS = [
    "trailing_mean_7", "trailing_mean_28", "demand_cv_28", "snap_days_in_life",
    "event_days_in_life", "price_rel_52w",
]


def validate_company_csv(raw_bytes, filename):
    """Validate an uploaded CSV/Excel file against the documented required schema.

    Returns (status, report):
      status: 'ok' | 'error'
      report: dict with either {'message': ...} on parse failure, or
              {'n_rows', 'n_cols', 'columns', 'missing_required',
               'present_optional', 'missing_values', 'preview'} on success/validation-fail.
    """
    try:
        if filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(raw_bytes))
        else:
            df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as e:
        return "error", {"message": f"Could not parse file: {e}"}

    if len(df) == 0:
        return "error", {"message": "The uploaded file contains no rows."}

    missing_required = [c for c in REQUIRED_RAW_FIELDS if c not in df.columns]
    present_optional = [c for c in OPTIONAL_RAW_FIELDS if c in df.columns]
    missing_values = df[[c for c in REQUIRED_RAW_FIELDS if c in df.columns]].isna().sum()
    missing_values = missing_values[missing_values > 0]

    report = {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": list(df.columns),
        "missing_required": missing_required,
        "present_optional": present_optional,
        "missing_values": missing_values,
        "preview": df.head(20),
    }
    status = "error" if missing_required else "ok"
    return status, report
