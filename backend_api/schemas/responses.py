"""
backend_api/schemas/responses.py
===================================
Pydantic response models. Every field here mirrors a column or metric that
app.py (the existing Streamlit app) already computes and displays -- no new
metrics, thresholds, or derived fields are introduced at this layer.
"""
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


# ----------------------------------------------------------------------
# /api/summary -- the same KPI values shown on app.py's Executive Overview
# page (dist bar, spoilage-rate-by-risk-level bar, intervention-scope
# metrics, total expected waste exposure, base-scenario waste reduction).
# ----------------------------------------------------------------------
class RiskDistributionEntry(BaseModel):
    risk_level: str
    count: int
    pct_of_total: float


class SpoilageRateEntry(BaseModel):
    risk_level: str
    observed_spoilage_rate: float


class InterventionScopeSummary(BaseModel):
    batch_level: int = Field(..., description="HIGH/CRITICAL batches with a batch-level action")
    replenishment_only: int = Field(..., description="MEDIUM batches, action targets future orders")
    none: int = Field(..., description="LOW risk batches, no action needed")


class SummaryResponse(BaseModel):
    total_batches: int
    high_critical_batches: int
    high_critical_pct_of_total: float
    total_expected_waste_exposure: float
    base_scenario_waste_reduction_pct: float
    risk_distribution: list[RiskDistributionEntry]
    spoilage_rate_by_risk_level: list[SpoilageRateEntry]
    intervention_scope_summary: InterventionScopeSummary


# ----------------------------------------------------------------------
# /api/risk-df -- Risk Explorer table, server-side filtered + paginated
# ----------------------------------------------------------------------
class BatchRecord(BaseModel):
    batch_id: str
    item_id: str
    category: str
    food_category: Optional[str] = None
    days_until_expiry: int
    current_inventory: int
    expected_demand_before_expiry: Optional[float] = None
    potential_excess_inventory: Optional[float] = None
    spoilage_probability: Optional[float] = None
    expected_waste_exposure: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: str
    intervention_scope: str
    recommendation: str


class RiskDfPageResponse(BaseModel):
    rows: list[BatchRecord]
    total_rows: int
    page: int
    page_size: int
    total_pages: int


# ----------------------------------------------------------------------
# /api/recommendations -- Recommendations page, per-level tabs
# ----------------------------------------------------------------------
class RecommendationRecord(BaseModel):
    batch_id: str
    item_id: str
    category: str
    risk_level: str
    days_until_expiry: int
    current_inventory: int
    potential_excess_inventory: Optional[float] = None
    expected_waste_exposure: Optional[float] = None
    intervention_scope: str
    recommendation: str


class RecommendationPageResponse(BaseModel):
    rows: list[RecommendationRecord]
    total_rows: int
    page: int
    page_size: int
    total_pages: int


# ----------------------------------------------------------------------
# /api/business-value -- Business Impact page's scenario table
# ----------------------------------------------------------------------
class BusinessValueScenario(BaseModel):
    scenario: str
    baseline_waste_units: float
    ai_assisted_waste_units: float
    waste_reduction_pct: float
    baseline_spoilage_rate: float
    ai_assisted_spoilage_rate: float
    spoilage_rate_reduction_pp: float
    intervention_count_high_critical: int


class BusinessValueResponse(BaseModel):
    scenarios: list[BusinessValueScenario]


# ----------------------------------------------------------------------
# /api/metadata -- safe subset of model_metadata.json / feature_config.json
# ----------------------------------------------------------------------
class ModelSummary(BaseModel):
    algorithm: str
    training_rows: int
    test_rows: int
    decision_threshold: Optional[float] = None


class MetadataResponse(BaseModel):
    export_timestamp_utc: str
    chronological_split_cutoff: str
    spoilage_model: ModelSummary
    demand_model: ModelSummary
    total_evaluation_batches: int
    training_data_assumptions: list[str]


# ----------------------------------------------------------------------
# POST /api/score, /api/score/upload -- live scoring through the frozen
# RiskEngine + generate_recommendation()
# ----------------------------------------------------------------------
class ScoredBatchRecord(BaseModel):
    batch_id: str
    item_id: str
    category: str
    food_category: Optional[str] = None
    days_until_expiry: float
    current_inventory: float
    expected_demand_before_expiry: Optional[float] = None
    potential_excess_inventory: Optional[float] = None
    spoilage_probability: Optional[float] = None
    expected_waste_exposure: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    intervention_scope: str
    recommendation: str
    risk_score_note: Optional[str] = Field(
        None, description="Present when risk_score/risk_level could not be computed for this row "
                           "(e.g. item_id not found in the training-period item_share_lookup)."
    )


class ScoreSummary(BaseModel):
    total_records_scored: int
    risk_distribution: list[RiskDistributionEntry]
    high_critical_count: int
    average_risk_score: Optional[float] = None
    average_spoilage_probability: Optional[float] = None
    total_expected_waste_exposure: Optional[float] = None
    unresolved_count: int = Field(
        0, description="Rows where risk_score could not be computed (e.g. unknown item_id)."
    )


class ScoreResponse(BaseModel):
    rows: list[ScoredBatchRecord]
    summary: ScoreSummary
    methodology_note: str = Field(
        "Risk scores are relative to the batches submitted in the current scoring run. "
        "Therefore, scores from a smaller uploaded batch may differ from the reference "
        "35,165-batch dataset."
    )


class FieldValidationError(BaseModel):
    row: Optional[int] = Field(None, description="0-indexed row number this error applies to, if row-specific.")
    field: str
    message: str


class ValidationResponse(BaseModel):
    valid: bool
    n_rows: int
    n_valid_rows: int
    n_invalid_rows: int
    errors: list[FieldValidationError]
    preview: list[dict] = Field(default_factory=list, description="First rows of the parsed file, raw (pre-validation) values.")


class InputSchemaField(BaseModel):
    name: str
    type: str
    required: bool
    allowed_values: Optional[list[str]] = None
    description: str


class InputSchemaResponse(BaseModel):
    batch_fields: list[InputSchemaField]
    category_demand_fields: list[InputSchemaField]
    notes: list[str]
