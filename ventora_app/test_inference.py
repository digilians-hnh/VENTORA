"""
Regression test for backend/inference/*.

Tests the WRAPPER logic (encoding, reindexing, composition, error handling)
against the REAL, verified feature_config.json -- but using fake, importable
model stand-ins instead of the real lightgbm/xgboost models, since those
libraries are not guaranteed to be installed wherever this test runs. This
means: a pass here proves the plumbing is correct; it does NOT re-verify
the actual model predictions (that's validate_deployment_artifacts.py's job,
already run and recorded in deployment_artifacts/validation_report.json).

Run: python3 test_inference.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition), detail))
    print(f"[{'PASS' if condition else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))


# ------------------------------------------------------------------
# Set up a throwaway artifacts dir with the REAL feature_config.json but
# FAKE (importable, picklable) models, so the test doesn't depend on
# lightgbm/xgboost being installed.
# ------------------------------------------------------------------
import tempfile
import joblib


class _FakeSpoilageModel:
    def __init__(self, coef):
        self.coef_ = np.asarray(coef)

    def predict_proba(self, X):
        z = X.values.dot(self.coef_)
        p = 1 / (1 + np.exp(-z))
        return np.column_stack([1 - p, p])


class _FakeDemandModel:
    def __init__(self, coef):
        self.coef_ = np.asarray(coef)

    def predict(self, X):
        return np.abs(X.values.dot(self.coef_)) + 10


tmp_dir = Path(tempfile.mkdtemp(prefix="ventora_inference_test_"))
real_config_path = APP_DIR / "deployment_artifacts" / "feature_config.json"
check("real feature_config.json exists", real_config_path.exists())

with open(real_config_path) as f:
    cfg = json.load(f)
(tmp_dir / "feature_config.json").write_text(json.dumps(cfg))

spoil_cols = cfg["spoilage_model"]["encoded_feature_names_in_order"]
dem_cols = cfg["demand_model"]["encoded_feature_names_in_order"]
rng = np.random.default_rng(42)
joblib.dump(_FakeSpoilageModel(rng.normal(size=len(spoil_cols))), tmp_dir / "spoilage_model.joblib")
joblib.dump(_FakeDemandModel(rng.normal(size=len(dem_cols))), tmp_dir / "demand_model.joblib")

# Small synthetic item_share_lookup (CSV, to avoid a pyarrow dependency in this test)
item_share = pd.DataFrame(
    {
        "item_avg_daily_demand": rng.uniform(1, 10, 5),
        "category": ["FOODS_1"] * 5,
        "category_avg_daily_demand": rng.uniform(50, 100, 5),
        "item_share_of_category": rng.uniform(0.01, 0.2, 5),
    },
    index=pd.Index([f"ITEM_{i}" for i in range(5)], name="item_id"),
)
item_share.to_csv(tmp_dir / "item_share_lookup.csv")

from backend.inference import RiskEngine, ModelUnavailableError, generate_recommendation  # noqa: E402

engine = RiskEngine(artifacts_dir=tmp_dir)

# ------------------------------------------------------------------
# TEST 1 — availability check reflects real readability, not just existence
# ------------------------------------------------------------------
check("engine.is_available is True with valid fake artifacts", engine.is_available)

# ------------------------------------------------------------------
# TEST 2 — end-to-end scoring produces expected columns and no crash
# ------------------------------------------------------------------
n = 12
batches = pd.DataFrame({
    "batch_id": [f"B{i}" for i in range(n)],
    "item_id": [f"ITEM_{i % 5}" for i in range(n)],
    "category": ["FOODS_1"] * n,
    "food_category": ["Dairy_Products_Eggs"] * n,
    "shelf_life_days": rng.integers(3, 15, n),
    "weekday_received": ["Monday"] * n,
    "is_holiday": 0, "is_promoted": 0,
    "qty_received": rng.integers(10, 100, n),
    "trailing_mean_7": rng.uniform(1, 10, n),
    "trailing_mean_28": rng.uniform(1, 10, n),
    "demand_cv_28": rng.uniform(0, 1, n),
    "no_trailing_demand_28": 0,
    "snap_days_in_life": rng.integers(0, 5, n),
    "event_days_in_life": rng.integers(0, 3, n),
    "current_inventory": rng.integers(10, 100, n),
    "days_until_expiry": rng.integers(1, 10, n),
})
cat_demand = pd.DataFrame({
    "category": ["FOODS_1"],
    "lag_1": [5.0], "lag_7": [5.0], "lag_14": [5.0],
    "roll_mean_7": [5.0], "roll_mean_28": [5.0],
    "month": [8], "day_of_week": ["Monday"],
})

scored = engine.score(batches, cat_demand)
expected_cols = {"spoilage_probability", "risk_score", "risk_level", "expected_waste_exposure",
                  "potential_excess_inventory", "expected_demand_before_expiry"}
check("scored output contains all expected columns", expected_cols.issubset(scored.columns),
      f"missing: {expected_cols - set(scored.columns)}")
check("scored output has correct row count", len(scored) == n)
check("risk_level values are all valid categories",
      scored["risk_level"].dropna().isin(["LOW", "MEDIUM", "HIGH", "CRITICAL"]).all())
check("spoilage_probability values are in [0, 1]",
      scored["spoilage_probability"].between(0, 1).all())

# ------------------------------------------------------------------
# TEST 3 — frozen recommendation engine composes cleanly on the output
# ------------------------------------------------------------------
scored[["recommendation", "intervention_scope"]] = scored.apply(generate_recommendation, axis=1)
check("recommendation engine produces non-empty text for every row",
      scored["recommendation"].apply(lambda s: len(str(s)) > 0).all())
check("intervention_scope values are all valid categories",
      scored["intervention_scope"].isin(
          ["batch-level", "batch-level (monitor only)", "replenishment-only (future batches)", "none"]
      ).all())

# ------------------------------------------------------------------
# TEST 4 — unknown item_id is handled gracefully, not a crash
# ------------------------------------------------------------------
batches_unknown = batches.copy()
batches_unknown.loc[0, "item_id"] = "ITEM_NOT_IN_TRAINING_DATA"
scored_unknown = engine.score(batches_unknown, cat_demand)
check("unknown item_id produces NaN risk_score (not a crash, not a fabricated score)",
      pd.isna(scored_unknown.loc[0, "risk_score"]))
check("unknown item_id gets an explanatory note",
      "risk_score_note" in scored_unknown.columns and
      pd.notna(scored_unknown.loc[0].get("risk_score_note")))

# ------------------------------------------------------------------
# TEST 5 — missing artifacts raise ModelUnavailableError, not a raw crash
# ------------------------------------------------------------------
empty_dir = Path(tempfile.mkdtemp(prefix="ventora_inference_empty_"))
engine_missing = RiskEngine(artifacts_dir=empty_dir)
check("engine.is_available is False with no artifacts", not engine_missing.is_available)
raised_correctly = False
try:
    engine_missing.score(batches, cat_demand)
except ModelUnavailableError:
    raised_correctly = True
except Exception as e:
    print(f"  (raised {type(e).__name__} instead of ModelUnavailableError: {e})")
check("scoring with missing artifacts raises ModelUnavailableError specifically", raised_correctly)

# ------------------------------------------------------------------
# TEST 6 — missing required raw feature column is caught with a clear error
# ------------------------------------------------------------------
batches_bad = batches.drop(columns=["trailing_mean_7"])
raised_valueerror = False
try:
    engine.score(batches_bad, cat_demand)
except ValueError as e:
    raised_valueerror = "trailing_mean_7" in str(e)
check("missing raw feature column raises a ValueError naming the missing column", raised_valueerror)

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
n_pass = sum(1 for _, ok, _ in RESULTS if ok)
n_total = len(RESULTS)
print(f"\n{n_pass}/{n_total} checks passed.")
if n_pass != n_total:
    sys.exit(1)
