"""
backend_api/core/scoring_validation.py
=========================================
Parses and validates uploaded batch-level / category-demand CSVs against
the exact same Pydantic models POST /api/score uses (BatchScoreInput,
CategoryDemandScoreInput) -- so "valid" means "the frozen RiskEngine can
actually score this", not a separate, looser notion of validity.
"""
import io
from typing import Any

import pandas as pd
from pydantic import ValidationError

from backend_api.schemas.requests import BatchScoreInput, CategoryDemandScoreInput
from backend_api.schemas.responses import FieldValidationError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB -- generous for a few thousand engineered rows
MAX_PREVIEW_ROWS = 20


class FileTooLargeError(ValueError):
    pass


class EmptyFileError(ValueError):
    pass


class MalformedCsvError(ValueError):
    pass


def read_csv_safely(raw_bytes: bytes, label: str) -> pd.DataFrame:
    if len(raw_bytes) == 0:
        raise EmptyFileError(f"{label} file is empty.")
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise FileTooLargeError(
            f"{label} file is {len(raw_bytes) / 1_000_000:.1f} MB, which exceeds the "
            f"{MAX_UPLOAD_BYTES / 1_000_000:.0f} MB limit."
        )
    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as e:
        raise MalformedCsvError(f"Could not parse {label} as CSV: {e}") from e
    if len(df) == 0:
        raise EmptyFileError(f"{label} file has a header but no data rows.")
    if len(df.columns) == 0 or all(str(c).startswith("Unnamed") for c in df.columns):
        raise MalformedCsvError(f"{label} file does not look like a valid CSV (no usable columns found).")
    return df


def _row_to_native(row: pd.Series) -> dict[str, Any]:
    """Convert a pandas row to plain Python values for both Pydantic
    validation and JSON preview -- NaN -> None, numpy scalars -> Python.
    """
    out: dict[str, Any] = {}
    for k, v in row.items():
        if pd.isna(v):
            out[k] = None
        elif hasattr(v, "item"):
            out[k] = v.item()
        else:
            out[k] = v
    return out


def validate_dataframe(
    df: pd.DataFrame, model_cls: type[BatchScoreInput] | type[CategoryDemandScoreInput]
) -> tuple[list[dict], list[FieldValidationError], int, int]:
    """Validate every row of df against model_cls.

    Returns (valid_rows_as_dicts, errors, n_valid, n_invalid).
    """
    valid_rows: list[dict] = []
    errors: list[FieldValidationError] = []

    for idx, row in df.iterrows():
        native = _row_to_native(row)
        try:
            validated = model_cls.model_validate(native)
        except ValidationError as e:
            for err in e.errors():
                field = ".".join(str(p) for p in err["loc"]) if err["loc"] else "(row)"
                errors.append(FieldValidationError(row=int(idx), field=field, message=err["msg"]))
        else:
            valid_rows.append(validated.model_dump())

    return valid_rows, errors, len(valid_rows), len(df) - len(valid_rows)


def build_preview(df: pd.DataFrame, n: int = MAX_PREVIEW_ROWS) -> list[dict]:
    return [_row_to_native(row) for _, row in df.head(n).iterrows()]
