"""
backend_api/routers/analytics.py
===================================
Read-only analytics endpoints. Every number returned here is read directly
from the frozen data/risk_df_recommendations_FINAL.pkl and
data/business_value_comparison.csv -- the exact same source app.py's
Executive Overview, Risk Explorer, and Business Impact pages use. This
router does not fit, retrain, re-score, or introduce any new formula; it
only filters, paginates, and re-shapes columns already present in those
frozen files.
"""
import math
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend_api.core.config import RISK_LEVELS_ORDER
from backend_api.core.data_access import (
    DataUnavailableError,
    load_business_value,
    load_model_metadata,
    load_risk_df,
)
from backend_api.core.serialization import row_to_dict, to_jsonable
from backend_api.schemas.responses import (
    BatchRecord,
    BusinessValueResponse,
    BusinessValueScenario,
    InterventionScopeSummary,
    MetadataResponse,
    ModelSummary,
    RiskDfPageResponse,
    RiskDistributionEntry,
    SpoilageRateEntry,
    SummaryResponse,
)

router = APIRouter(prefix="/api", tags=["analytics"])

RISK_DF_DISPLAY_COLS = [
    "batch_id", "item_id", "category", "food_category", "days_until_expiry",
    "current_inventory", "expected_demand_before_expiry", "potential_excess_inventory",
    "spoilage_probability", "expected_waste_exposure", "risk_score", "risk_level",
    "intervention_scope", "recommendation",
]


def _get_risk_df():
    try:
        return load_risk_df()
    except DataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


def _get_business_value():
    try:
        return load_business_value()
    except DataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.get("/summary", response_model=SummaryResponse)
def get_summary() -> SummaryResponse:
    """Executive Overview KPIs -- identical values to app.py's page 1:
    total batches, HIGH+CRITICAL count/pct, total expected waste exposure,
    base-scenario simulated waste reduction, risk distribution, observed
    spoilage rate by risk level, and the intervention-scope summary.
    """
    df = _get_risk_df()
    bv_df = _get_business_value()
    total = len(df)

    dist = df["risk_level"].value_counts().reindex(RISK_LEVELS_ORDER).fillna(0).astype(int)
    risk_distribution = [
        RiskDistributionEntry(
            risk_level=level,
            count=int(dist[level]),
            pct_of_total=round(float(dist[level]) / total * 100, 2) if total else 0.0,
        )
        for level in RISK_LEVELS_ORDER
    ]

    spoil_by_level = df.groupby("risk_level", observed=True)["was_spoiled"].mean().reindex(RISK_LEVELS_ORDER)
    spoilage_rate_by_risk_level = [
        SpoilageRateEntry(risk_level=level, observed_spoilage_rate=to_jsonable(spoil_by_level[level]))
        for level in RISK_LEVELS_ORDER
    ]

    high_crit_n = int(dist["HIGH"] + dist["CRITICAL"])
    total_exposure = float(df["expected_waste_exposure"].sum())

    if "Base" not in bv_df.index:
        raise HTTPException(status_code=500, detail="business_value_comparison.csv missing 'Base' scenario row.")
    base_reduction = float(bv_df.loc["Base", "Waste Reduction %"])

    scope_counts = df["intervention_scope"].value_counts()
    intervention_scope_summary = InterventionScopeSummary(
        batch_level=int(scope_counts.get("batch-level", 0)),
        replenishment_only=int(scope_counts.get("replenishment-only (future batches)", 0)),
        none=int(scope_counts.get("none", 0)),
    )

    return SummaryResponse(
        total_batches=total,
        high_critical_batches=high_crit_n,
        high_critical_pct_of_total=round(high_crit_n / total * 100, 2) if total else 0.0,
        total_expected_waste_exposure=round(total_exposure, 2),
        base_scenario_waste_reduction_pct=base_reduction,
        risk_distribution=risk_distribution,
        spoilage_rate_by_risk_level=spoilage_rate_by_risk_level,
        intervention_scope_summary=intervention_scope_summary,
    )


@router.get("/risk-df", response_model=RiskDfPageResponse)
def get_risk_df(
    risk_level: Optional[list[str]] = Query(None, description="Filter to one or more risk levels"),
    category: Optional[list[str]] = Query(None, description="Filter to one or more categories"),
    min_days_to_expiry: Optional[int] = Query(None, ge=0),
    max_days_to_expiry: Optional[int] = Query(None, ge=0),
    min_excess: Optional[float] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
) -> RiskDfPageResponse:
    """Risk Explorer table -- same filters as app.py's Risk Explorer page
    (risk level, category, days-until-expiry range, minimum potential
    excess), server-side paginated so the full 35,165-row table is never
    sent to the client by default.
    """
    df = _get_risk_df()

    filtered = df
    if risk_level:
        invalid = [lvl for lvl in risk_level if lvl not in RISK_LEVELS_ORDER]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid risk_level value(s): {invalid}")
        filtered = filtered[filtered["risk_level"].isin(risk_level)]
    if category:
        filtered = filtered[filtered["category"].isin(category)]
    if min_days_to_expiry is not None:
        filtered = filtered[filtered["days_until_expiry"] >= min_days_to_expiry]
    if max_days_to_expiry is not None:
        filtered = filtered[filtered["days_until_expiry"] <= max_days_to_expiry]
    if min_excess is not None:
        filtered = filtered[filtered["potential_excess_inventory"] >= min_excess]

    filtered = filtered.sort_values("risk_score", ascending=False)

    total_rows = len(filtered)
    total_pages = max(1, math.ceil(total_rows / page_size))
    if page > total_pages and total_rows > 0:
        raise HTTPException(status_code=404, detail=f"page {page} exceeds total_pages {total_pages}")

    start = (page - 1) * page_size
    end = start + page_size
    page_df = filtered.iloc[start:end]

    rows = [
        BatchRecord(**row_to_dict(row, RISK_DF_DISPLAY_COLS))
        for _, row in page_df.iterrows()
    ]

    return RiskDfPageResponse(
        rows=rows, total_rows=total_rows, page=page, page_size=page_size, total_pages=total_pages,
    )


@router.get("/business-value", response_model=BusinessValueResponse)
def get_business_value() -> BusinessValueResponse:
    """The 3 simulated scenarios (Conservative/Base/Optimistic) from
    data/business_value_comparison.csv, exactly as app.py's Business Impact
    page presents them -- no recomputation.
    """
    bv_df = _get_business_value()
    scenarios = []
    for scenario_name, row in bv_df.iterrows():
        scenarios.append(
            BusinessValueScenario(
                scenario=str(scenario_name),
                baseline_waste_units=to_jsonable(row["Baseline Waste Units"]),
                ai_assisted_waste_units=to_jsonable(row["AI-Assisted Waste Units"]),
                waste_reduction_pct=to_jsonable(row["Waste Reduction %"]),
                baseline_spoilage_rate=to_jsonable(row["Baseline Spoilage Rate"]),
                ai_assisted_spoilage_rate=to_jsonable(row["AI-Assisted Spoilage Rate"]),
                spoilage_rate_reduction_pp=to_jsonable(row["Spoilage Rate Reduction (pp)"]),
                intervention_count_high_critical=int(row["Intervention Count (HIGH+CRITICAL)"]),
            )
        )
    return BusinessValueResponse(scenarios=scenarios)


@router.get("/metadata", response_model=MetadataResponse)
def get_metadata() -> MetadataResponse:
    """Safe, non-sensitive subset of model_metadata.json -- algorithm names,
    hyperparameter-free summary, training/test row counts, decision
    threshold, chronological split cutoff, and training-data assumptions.
    Deliberately excludes filesystem paths and the full hyperparameter dump.
    """
    try:
        meta = load_model_metadata()
    except DataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    df = _get_risk_df()

    spoilage = meta["spoilage_model"]
    demand = meta["demand_model"]

    return MetadataResponse(
        export_timestamp_utc=meta["export_timestamp_utc"],
        chronological_split_cutoff=meta["chronological_split_cutoff"],
        spoilage_model=ModelSummary(
            algorithm=spoilage["algorithm"],
            training_rows=spoilage["training_rows"],
            test_rows=spoilage["test_rows"],
            decision_threshold=spoilage.get("decision_threshold"),
        ),
        demand_model=ModelSummary(
            algorithm=demand["algorithm"],
            training_rows=demand["training_rows"],
            test_rows=demand["test_rows"],
        ),
        total_evaluation_batches=len(df),
        training_data_assumptions=meta.get("training_data_assumptions", []),
    )
