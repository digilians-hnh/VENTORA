"""
backend_api/routers/scoring.py
=================================
Live-scoring endpoints. Every endpoint here either validates input against
the exact schema the frozen RiskEngine needs (backend_api/schemas/requests.py)
or runs that frozen engine via backend_api/core/scoring_service.py. No
model, threshold, or recommendation logic is implemented in this file.
"""
import logging

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend_api.core.config import DEMO_BATCHES_PATH, DEMO_CATEGORY_DEMAND_PATH
from backend_api.core.inference_adapter import ModelUnavailableError
from backend_api.core.scoring_schema import (
    BATCH_IDENTIFIER_FIELDS,
    CATEGORY_VALUES,
    FIELD_DESCRIPTIONS,
    FOOD_CATEGORY_VALUES,
    RAW_BATCH_FEATURES,
    RAW_CATEGORY_DEMAND_FEATURES,
    WEEKDAY_VALUES,
)
from backend_api.core.scoring_service import missing_category_demand_rows, run_scoring
from backend_api.core.scoring_validation import (
    EmptyFileError,
    FileTooLargeError,
    MalformedCsvError,
    build_preview,
    read_csv_safely,
    validate_dataframe,
)
from backend_api.schemas.requests import BatchScoreInput, CategoryDemandScoreInput, ScoreRequest
from backend_api.schemas.responses import (
    FieldValidationError,
    InputSchemaField,
    InputSchemaResponse,
    ScoreResponse,
    ValidationResponse,
)

logger = logging.getLogger("ventora_api.scoring")

router = APIRouter(prefix="/api", tags=["scoring"])


def _allowed_values_for(field: str) -> list[str] | None:
    if field == "category":
        return CATEGORY_VALUES
    if field == "food_category":
        return FOOD_CATEGORY_VALUES
    if field in ("weekday_received", "day_of_week"):
        return WEEKDAY_VALUES
    return None


def _field_schema(name: str, required: bool) -> InputSchemaField:
    return InputSchemaField(
        name=name,
        type="string" if _allowed_values_for(name) or name in ("batch_id", "item_id") else "number",
        required=required,
        allowed_values=_allowed_values_for(name),
        description=FIELD_DESCRIPTIONS.get(name, ""),
    )


@router.get("/input-schema", response_model=InputSchemaResponse)
def get_input_schema() -> InputSchemaResponse:
    """Describes exactly what POST /api/score (and the CSV upload
    endpoints) require -- derived directly from the frozen models' raw
    input features (see scoring_schema.py), not invented.
    """
    batch_fields = [_field_schema(f, required=True) for f in BATCH_IDENTIFIER_FIELDS + RAW_BATCH_FEATURES]
    demand_fields = [_field_schema(f, required=True) for f in RAW_CATEGORY_DEMAND_FEATURES]
    return InputSchemaResponse(
        batch_fields=batch_fields,
        category_demand_fields=demand_fields,
        notes=[
            "Two separate tables are required: one row per batch, and one row per category "
            "represented in those batches.",
            "Every category present in the batch table must have a matching row in the "
            "category-demand table.",
            "item_id should match an item the models were trained on; unmatched items come back "
            "with a null risk_score and an explanatory note rather than a fabricated value.",
            "Risk scores are computed relative to the batches submitted in a single scoring run, "
            "so results from a small uploaded batch will not exactly reproduce the reference "
            "35,165-batch dataset's score distribution.",
        ],
    )


def _handle_model_unavailable(e: ModelUnavailableError):
    logger.exception("Model unavailable during scoring.")
    raise HTTPException(status_code=503, detail=str(e)) from e


@router.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest) -> ScoreResponse:
    """Score a JSON payload of engineered batch + category-demand records
    through the frozen RiskEngine + recommendation engine.
    """
    try:
        return run_scoring(
            [b.model_dump() for b in request.batches],
            [c.model_dump() for c in request.category_demand],
        )
    except ModelUnavailableError as e:
        _handle_model_unavailable(e)


def _validate_upload(
    batches_file: UploadFile, category_demand_file: UploadFile
) -> tuple[ValidationResponse, list[dict], list[dict]]:
    try:
        batches_raw = batches_file.file.read()
        demand_raw = category_demand_file.file.read()
        batches_df = read_csv_safely(batches_raw, "Batch-level")
        demand_df = read_csv_safely(demand_raw, "Category-demand")
    except (EmptyFileError, FileTooLargeError, MalformedCsvError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    valid_batches, batch_errors, n_valid_b, n_invalid_b = validate_dataframe(batches_df, BatchScoreInput)
    valid_demand, demand_errors, n_valid_d, n_invalid_d = validate_dataframe(demand_df, CategoryDemandScoreInput)

    errors = list(batch_errors) + list(demand_errors)

    # Duplicate batch_id / category checks (row-level Pydantic validation
    # can't see across rows, so these are cross-row checks on the same
    # already-valid rows -- mirrors ScoreRequest's model_validator).
    seen_batch_ids: dict[str, int] = {}
    for i, b in enumerate(valid_batches):
        if b["batch_id"] in seen_batch_ids:
            errors.append(FieldValidationError(row=i, field="batch_id", message=f"Duplicate batch_id: {b['batch_id']!r}"))
        else:
            seen_batch_ids[b["batch_id"]] = i

    seen_categories: dict[str, int] = {}
    for i, c in enumerate(valid_demand):
        if c["category"] in seen_categories:
            errors.append(FieldValidationError(row=i, field="category", message=f"Duplicate category in category_demand: {c['category']!r}"))
        else:
            seen_categories[c["category"]] = i

    if not errors:
        missing = missing_category_demand_rows(valid_batches, valid_demand)
        if missing:
            errors.append(
                FieldValidationError(
                    row=None,
                    field="category",
                    message=(
                        f"category_demand file has no row for categor{'y' if len(missing) == 1 else 'ies'}: "
                        f"{missing}. Every category in the batch file needs a matching row in the "
                        "category-demand file."
                    ),
                )
            )

    return ValidationResponse(
        valid=len(errors) == 0,
        n_rows=len(batches_df) + len(demand_df),
        n_valid_rows=n_valid_b + n_valid_d,
        n_invalid_rows=n_invalid_b + n_invalid_d,
        errors=errors,
        preview=build_preview(batches_df),
    ), valid_batches, valid_demand


@router.post("/score/validate", response_model=ValidationResponse)
def validate_upload(
    batches_file: UploadFile = File(..., description="Batch-level engineered CSV"),
    category_demand_file: UploadFile = File(..., description="Category-demand engineered CSV"),
) -> ValidationResponse:
    """Validate + preview two uploaded CSVs WITHOUT scoring. This is the
    step the Data Input page calls immediately after upload, before the
    person clicks "Score Inventory".
    """
    result, _valid_batches, _valid_demand = _validate_upload(batches_file, category_demand_file)
    return result


@router.post("/score/upload", response_model=ScoreResponse)
def upload_and_score(
    batches_file: UploadFile = File(..., description="Batch-level engineered CSV"),
    category_demand_file: UploadFile = File(..., description="Category-demand engineered CSV"),
) -> ScoreResponse:
    """Validate two uploaded CSVs and, if fully valid, score them. Returns
    400 with structured validation errors if any row is invalid --
    scoring never runs on partially-invalid input.
    """
    validation, valid_batches, valid_demand = _validate_upload(batches_file, category_demand_file)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.model_dump())

    try:
        return run_scoring(valid_batches, valid_demand)
    except ModelUnavailableError as e:
        _handle_model_unavailable(e)


@router.get("/score/demo", response_model=ValidationResponse)
def get_demo_data() -> ValidationResponse:
    """Preview the packaged synthetic demo dataset (NOT real company or
    sales data) -- lets the Data Input page show what will be scored
    before the person clicks "Score Demo Data".
    """
    if not DEMO_BATCHES_PATH.exists() or not DEMO_CATEGORY_DEMAND_PATH.exists():
        raise HTTPException(status_code=503, detail="Demo data files are not available.")
    batches_df = pd.read_csv(DEMO_BATCHES_PATH)
    demand_df = pd.read_csv(DEMO_CATEGORY_DEMAND_PATH)
    return ValidationResponse(
        valid=True,
        n_rows=len(batches_df) + len(demand_df),
        n_valid_rows=len(batches_df) + len(demand_df),
        n_invalid_rows=0,
        errors=[],
        preview=build_preview(batches_df, n=len(batches_df)),
    )


@router.post("/score/demo", response_model=ScoreResponse)
def score_demo_data() -> ScoreResponse:
    """Score the packaged synthetic demo dataset -- demonstrates the live
    scoring workflow without requiring the person to prepare any files.
    """
    if not DEMO_BATCHES_PATH.exists() or not DEMO_CATEGORY_DEMAND_PATH.exists():
        raise HTTPException(status_code=503, detail="Demo data files are not available.")
    batches_df = pd.read_csv(DEMO_BATCHES_PATH)
    demand_df = pd.read_csv(DEMO_CATEGORY_DEMAND_PATH)

    valid_batches, batch_errors, _, _ = validate_dataframe(batches_df, BatchScoreInput)
    valid_demand, demand_errors, _, _ = validate_dataframe(demand_df, CategoryDemandScoreInput)
    if batch_errors or demand_errors:
        # Packaged demo data should always be valid; surface loudly if not.
        raise HTTPException(
            status_code=500,
            detail="Packaged demo data failed validation -- this indicates a bug, not a user input error.",
        )

    try:
        return run_scoring(valid_batches, valid_demand)
    except ModelUnavailableError as e:
        _handle_model_unavailable(e)
