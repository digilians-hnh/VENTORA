"""
backend_api/schemas/requests.py
==================================
Request models for POST /api/score. Field set matches exactly the raw
input features the frozen SpoilagePredictor / DemandPredictor / RiskEngine
require (see backend_api/core/scoring_schema.py for how each categorical
value set was derived). No field here is invented, and no field the
models need is omitted.
"""
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from backend_api.core.scoring_schema import CATEGORY_VALUES, FOOD_CATEGORY_VALUES, WEEKDAY_VALUES

CategoryLiteral = Literal["FOODS_1", "FOODS_2", "FOODS_3"]
FoodCategoryLiteral = Literal[
    "Baked_Goods", "Beverages", "Condiments_Sauces_Canned_Goods", "Dairy_Products_Eggs",
    "Deli_Prepared_Foods", "Meat", "Poultry", "Produce", "Seafood", "Shelf_Stable_Foods",
]
WeekdayLiteral = Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

assert list(CategoryLiteral.__args__) == CATEGORY_VALUES  # keep in lockstep with scoring_schema.py
assert list(FoodCategoryLiteral.__args__) == FOOD_CATEGORY_VALUES
assert list(WeekdayLiteral.__args__) == WEEKDAY_VALUES


class BatchScoreInput(BaseModel):
    batch_id: str = Field(..., min_length=1, max_length=128)
    item_id: str = Field(..., min_length=1, max_length=128)
    category: CategoryLiteral
    food_category: FoodCategoryLiteral
    shelf_life_days: float = Field(..., gt=0)
    weekday_received: WeekdayLiteral
    is_holiday: int = Field(..., ge=0, le=1)
    is_promoted: int = Field(..., ge=0, le=1)
    qty_received: float = Field(..., ge=0)
    trailing_mean_7: float = Field(..., ge=0)
    trailing_mean_28: float = Field(..., ge=0)
    demand_cv_28: float = Field(..., ge=0)
    no_trailing_demand_28: int = Field(..., ge=0, le=1)
    snap_days_in_life: float = Field(..., ge=0)
    event_days_in_life: float = Field(..., ge=0)
    current_inventory: float = Field(..., ge=0)
    days_until_expiry: float = Field(..., ge=0)

    @field_validator("batch_id", "item_id")
    @classmethod
    def _strip_and_require_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class CategoryDemandScoreInput(BaseModel):
    category: CategoryLiteral
    lag_1: float = Field(..., ge=0)
    lag_7: float = Field(..., ge=0)
    lag_14: float = Field(..., ge=0)
    roll_mean_7: float = Field(..., ge=0)
    roll_mean_28: float = Field(..., ge=0)
    month: int = Field(..., ge=1, le=12)
    day_of_week: WeekdayLiteral


class ScoreRequest(BaseModel):
    batches: list[BatchScoreInput] = Field(..., min_length=1, max_length=5000)
    category_demand: list[CategoryDemandScoreInput] = Field(..., min_length=1, max_length=50)

    @field_validator("batches")
    @classmethod
    def _unique_batch_ids(cls, v: list[BatchScoreInput]) -> list[BatchScoreInput]:
        seen = set()
        dupes = set()
        for b in v:
            if b.batch_id in seen:
                dupes.add(b.batch_id)
            seen.add(b.batch_id)
        if dupes:
            raise ValueError(f"Duplicate batch_id value(s): {sorted(dupes)}")
        return v

    @field_validator("category_demand")
    @classmethod
    def _unique_categories(cls, v: list[CategoryDemandScoreInput]) -> list[CategoryDemandScoreInput]:
        seen = set()
        dupes = set()
        for c in v:
            if c.category in seen:
                dupes.add(c.category)
            seen.add(c.category)
        if dupes:
            raise ValueError(f"Duplicate category value(s) in category_demand: {sorted(dupes)}")
        return v

    @model_validator(mode="after")
    def _every_batch_category_has_demand_row(self) -> "ScoreRequest":
        demand_categories = {c.category for c in self.category_demand}
        missing = sorted({b.category for b in self.batches} - demand_categories)
        if missing:
            raise ValueError(
                "category_demand is missing a row for categor" + ("y" if len(missing) == 1 else "ies")
                + f": {missing}. Every category present in `batches` needs a matching row in "
                "`category_demand`, or demand (and therefore risk) cannot be computed for those batches."
            )
        return self
