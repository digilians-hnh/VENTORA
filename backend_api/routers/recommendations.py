"""
backend_api/routers/recommendations.py
=========================================
Serves the recommendation records already present in the frozen
data/risk_df_recommendations_FINAL.pkl (the `recommendation` and
`intervention_scope` columns were produced by the frozen
recommendation_engine_3.generate_recommendation(), upstream of this app --
this router only reads and paginates them, exactly as app.py's
Recommendations page tabs do).
"""
import math
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend_api.core.config import RISK_LEVELS_ORDER
from backend_api.core.data_access import DataUnavailableError, load_risk_df
from backend_api.core.serialization import row_to_dict
from backend_api.schemas.responses import RecommendationPageResponse, RecommendationRecord

router = APIRouter(prefix="/api", tags=["recommendations"])

RECOMMENDATION_DISPLAY_COLS = [
    "batch_id", "item_id", "category", "risk_level", "days_until_expiry",
    "current_inventory", "potential_excess_inventory", "expected_waste_exposure",
    "intervention_scope", "recommendation",
]


@router.get("/recommendations", response_model=RecommendationPageResponse)
def get_recommendations(
    level: Optional[str] = Query(None, description="LOW | MEDIUM | HIGH | CRITICAL"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
) -> RecommendationPageResponse:
    """Recommendation records for one risk level (or all, if `level` is
    omitted), sorted by expected_waste_exposure descending -- the same
    ordering app.py's Recommendations tabs use.
    """
    try:
        df = load_risk_df()
    except DataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    if level is not None:
        if level not in RISK_LEVELS_ORDER:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid level '{level}'. Must be one of {RISK_LEVELS_ORDER}.",
            )
        subset = df[df["risk_level"] == level]
    else:
        subset = df

    subset = subset.sort_values("expected_waste_exposure", ascending=False)

    total_rows = len(subset)
    total_pages = max(1, math.ceil(total_rows / page_size))
    if page > total_pages and total_rows > 0:
        raise HTTPException(status_code=404, detail=f"page {page} exceeds total_pages {total_pages}")

    start = (page - 1) * page_size
    end = start + page_size
    page_df = subset.iloc[start:end]

    rows = [
        RecommendationRecord(**row_to_dict(row, RECOMMENDATION_DISPLAY_COLS))
        for _, row in page_df.iterrows()
    ]

    return RecommendationPageResponse(
        rows=rows, total_rows=total_rows, page=page, page_size=page_size, total_pages=total_pages,
    )
