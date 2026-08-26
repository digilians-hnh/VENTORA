"""
backend_api/core/serialization.py
====================================
Pure conversion helpers: pandas/numpy values -> JSON-safe Python values, at
the API boundary only. No values are transformed, rounded, or recomputed --
this only changes *type* (e.g. pandas Categorical -> str, numpy.int64 ->
int), never the underlying number.
"""
from typing import Any

import numpy as np
import pandas as pd


def to_jsonable(value: Any) -> Any:
    """Convert a single pandas/numpy scalar to a plain JSON-safe Python value.

    - pandas/numpy NaN -> None
    - numpy integer/float -> Python int/float
    - pandas Categorical value -> str
    - everything else -> returned unchanged
    """
    if value is None:
        return None
    if isinstance(value, (pd.Categorical,)):
        return str(value)
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def row_to_dict(row: pd.Series, columns: list[str]) -> dict:
    """Convert selected columns of a DataFrame row to a JSON-safe dict,
    preserving column names and values exactly (only the Python type of
    each value changes, per to_jsonable()).
    """
    return {col: to_jsonable(row[col]) for col in columns if col in row.index}
