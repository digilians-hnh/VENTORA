"""Shared helpers for the Phase 3 scoring test suite."""
import pandas as pd

from backend_api.core.config import DEMO_BATCHES_PATH, DEMO_CATEGORY_DEMAND_PATH


def load_demo_records() -> tuple[list[dict], list[dict]]:
    batches_df = pd.read_csv(DEMO_BATCHES_PATH)
    demand_df = pd.read_csv(DEMO_CATEGORY_DEMAND_PATH)
    return batches_df.to_dict(orient="records"), demand_df.to_dict(orient="records")
