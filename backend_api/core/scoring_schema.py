"""
backend_api/core/scoring_schema.py
=====================================
Single source of truth for the live-scoring input schema. Every value set
here is DERIVED, not invented:

- CATEGORY_VALUES / FOOD_CATEGORY_VALUES / WEEKDAY_VALUES come from
  deployment_artifacts/feature_config.json's `encoded_feature_names_in_order`
  lists (one-hot encoding with drop_first=True -- so the dropped/baseline
  level for each categorical column is reconstructed by diffing the encoded
  column suffixes against the frozen dataset's real, observed values for
  that field in data/risk_df_recommendations_FINAL.pkl).
- RAW_BATCH_FEATURES / RAW_CATEGORY_DEMAND_FEATURES mirror
  feature_config.json's `raw_input_features` for each model exactly.

Both backend_api/schemas/requests.py (Pydantic validation) and the
GET /api/input-schema endpoint import from here, so the two can never
silently drift apart.
"""

# --- Categorical value sets -------------------------------------------
# category: encoded columns are category_FOODS_2, category_FOODS_3 ->
# FOODS_1 is the dropped baseline level. All three are real, observed
# values in the frozen dataset.
CATEGORY_VALUES = ["FOODS_1", "FOODS_2", "FOODS_3"]

# food_category: encoded columns cover 9 of the 10 real values observed in
# the frozen dataset; Baked_Goods is the dropped baseline (it's the only
# one of the 10 real food_category values with no corresponding one-hot
# column in feature_config.json).
FOOD_CATEGORY_VALUES = [
    "Baked_Goods",
    "Beverages",
    "Condiments_Sauces_Canned_Goods",
    "Dairy_Products_Eggs",
    "Deli_Prepared_Foods",
    "Meat",
    "Poultry",
    "Produce",
    "Seafood",
    "Shelf_Stable_Foods",
]

# weekday_received / day_of_week: encoded columns cover 6 of 7 weekdays;
# Friday is the dropped baseline.
WEEKDAY_VALUES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --- Raw (pre-encoding) feature lists, from feature_config.json --------
RAW_BATCH_FEATURES = [
    "category", "food_category", "shelf_life_days", "weekday_received",
    "is_holiday", "is_promoted", "qty_received", "trailing_mean_7",
    "trailing_mean_28", "demand_cv_28", "no_trailing_demand_28",
    "snap_days_in_life", "event_days_in_life",
]
BATCH_IDENTIFIER_FIELDS = ["batch_id", "item_id", "current_inventory", "days_until_expiry"]

RAW_CATEGORY_DEMAND_FEATURES = [
    "category", "lag_1", "lag_7", "lag_14", "roll_mean_7", "roll_mean_28",
    "month", "day_of_week",
]

FIELD_DESCRIPTIONS = {
    "batch_id": "Identifier for this batch. Not used by the models -- for tracking only.",
    "item_id": "Item identifier. Must match an item present in the frozen item_share_lookup "
               "(training-period items) or risk_score/risk_level come back null for that row.",
    "category": "Top-level product category.",
    "food_category": "Finer-grained food category.",
    "shelf_life_days": "Total shelf life of this item, in days.",
    "weekday_received": "Day of week the batch was received.",
    "is_holiday": "1 if received on a holiday, else 0.",
    "is_promoted": "1 if this batch is under an active promotion, else 0.",
    "qty_received": "Quantity received in this batch.",
    "trailing_mean_7": "7-day trailing mean of historical demand for this item.",
    "trailing_mean_28": "28-day trailing mean of historical demand for this item.",
    "demand_cv_28": "28-day coefficient of variation of historical demand for this item.",
    "no_trailing_demand_28": "1 if there was no recorded demand in the trailing 28 days, else 0.",
    "snap_days_in_life": "Number of SNAP (benefits) days that fall within this batch's shelf life.",
    "event_days_in_life": "Number of calendar event days that fall within this batch's shelf life.",
    "current_inventory": "Units of this batch currently in inventory.",
    "days_until_expiry": "Days remaining until this batch expires.",
    "lag_1": "Category-level total demand, 1 day prior.",
    "lag_7": "Category-level total demand, 7 days prior.",
    "lag_14": "Category-level total demand, 14 days prior.",
    "roll_mean_7": "7-day rolling mean of category-level total demand (shifted 1 day).",
    "roll_mean_28": "28-day rolling mean of category-level total demand (shifted 1 day).",
    "month": "Calendar month (1-12) for the demand forecast date.",
    "day_of_week": "Day of week for the demand forecast date.",
}
