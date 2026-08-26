"""
backend_api/core/scoring_service.py
======================================
Orchestrates a single live-scoring call: validated input dicts ->
pandas DataFrames -> the FROZEN RiskEngine.score() + generate_recommendation()
(imported unmodified via inference_adapter) -> ScoreResponse. This module
does not compute a risk score, spoilage probability, or recommendation
itself -- it only shapes data in and out of the frozen functions.
"""
from typing import Any

import pandas as pd

from backend_api.core.inference_adapter import ModelUnavailableError, generate_recommendation, get_risk_engine
from backend_api.core.serialization import to_jsonable
from backend_api.schemas.responses import (
    RiskDistributionEntry,
    ScoredBatchRecord,
    ScoreResponse,
    ScoreSummary,
)

RISK_LEVELS_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

SCORED_ROW_COLUMNS = [
    "batch_id", "item_id", "category", "food_category", "days_until_expiry",
    "current_inventory", "expected_demand_before_expiry", "potential_excess_inventory",
    "spoilage_probability", "expected_waste_exposure", "risk_score", "risk_level",
    "intervention_scope", "recommendation", "risk_score_note",
]


def missing_category_demand_rows(batches: list[dict[str, Any]], category_demand: list[dict[str, Any]]) -> list[str]:
    """Categories present in `batches` with no matching row in
    `category_demand` -- these rows would silently come back with a NaN
    risk_score from the frozen engine (missing map -> NaN), so we flag it
    as a clear, actionable validation error instead.
    """
    demand_categories = {c["category"] for c in category_demand}
    batch_categories = {b["category"] for b in batches}
    return sorted(batch_categories - demand_categories)


def run_scoring(batches: list[dict[str, Any]], category_demand: list[dict[str, Any]]) -> ScoreResponse:
    """Score `batches` against `category_demand` using the frozen RiskEngine,
    then attach the frozen recommendation engine's output. Raises
    ModelUnavailableError if the deployment models can't be loaded in this
    environment (missing lightgbm/xgboost/pyarrow, or artifacts missing).
    """
    engine = get_risk_engine()
    if not engine.is_available:
        raise ModelUnavailableError(
            "The deployment models are not currently loadable in this environment "
            "(missing lightgbm/xgboost/pyarrow, or the deployment artifacts are missing)."
        )

    batches_df = pd.DataFrame(batches)
    category_demand_df = pd.DataFrame(category_demand)

    scored = engine.score(batches_df, category_demand_df)
    scored[["recommendation", "intervention_scope"]] = scored.apply(generate_recommendation, axis=1)

    for col in SCORED_ROW_COLUMNS:
        if col not in scored.columns:
            scored[col] = None

    rows = [
        ScoredBatchRecord(**{col: to_jsonable(row[col]) for col in SCORED_ROW_COLUMNS})
        for _, row in scored.iterrows()
    ]

    total = len(scored)
    dist_counts = scored["risk_level"].value_counts()
    risk_distribution = [
        RiskDistributionEntry(
            risk_level=level,
            count=int(dist_counts.get(level, 0)),
            pct_of_total=round(int(dist_counts.get(level, 0)) / total * 100, 2) if total else 0.0,
        )
        for level in RISK_LEVELS_ORDER
    ]
    high_critical = int(dist_counts.get("HIGH", 0) + dist_counts.get("CRITICAL", 0))
    unresolved = int(scored["risk_score"].isna().sum())

    summary = ScoreSummary(
        total_records_scored=total,
        risk_distribution=risk_distribution,
        high_critical_count=high_critical,
        average_risk_score=to_jsonable(scored["risk_score"].mean()) if total else None,
        average_spoilage_probability=to_jsonable(scored["spoilage_probability"].mean()) if total else None,
        total_expected_waste_exposure=to_jsonable(scored["expected_waste_exposure"].sum()) if total else None,
        unresolved_count=unresolved,
    )

    return ScoreResponse(rows=rows, summary=summary)
