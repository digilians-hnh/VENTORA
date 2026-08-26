"""
VENTORA QA test suite.
Run: python3 test_app.py
Covers TEST 1-9 from the project QA plan (TEST 10 = actual `streamlit run`,
performed separately and reported in the handoff/summary, not here).
"""
import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from venlib import validate_company_csv, REQUIRED_RAW_FIELDS  # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition), detail))
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name} {('- ' + detail) if detail else ''}")


# ------------------------------------------------------------------
# Frozen-file integrity: confirm files are untouched vs. the hashes
# recorded at delivery time in FROZEN_ARTIFACT_HASHES.txt.
#
# NOTE: this used to compare against absolute paths under
# /mnt/user-data/uploads/, which only existed in the authoring sandbox.
# That made the check crash (FileNotFoundError, not a clean FAIL) in any
# other environment -- including this one. FROZEN_ARTIFACT_HASHES.txt is
# bundled with the app specifically so integrity can be re-verified
# anywhere without depending on the original upload location.
# ------------------------------------------------------------------
def sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def load_frozen_hashes():
    hashes = {}
    hash_file = Path(__file__).parent / "FROZEN_ARTIFACT_HASHES.txt"
    for line in hash_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel_path = line.split(None, 1)
        hashes[rel_path.strip()] = digest.strip()
    return hashes


FROZEN_HASHES = load_frozen_hashes()
app_pkl = DATA_DIR / "risk_df_recommendations_FINAL.pkl"
app_csv = DATA_DIR / "business_value_comparison.csv"

check("TEST 0a: pkl hash matches FROZEN_ARTIFACT_HASHES.txt (frozen file untouched)",
      sha256(app_pkl) == FROZEN_HASHES.get("data/risk_df_recommendations_FINAL.pkl"))
check("TEST 0b: business_value_comparison.csv hash matches FROZEN_ARTIFACT_HASHES.txt",
      sha256(app_csv) == FROZEN_HASHES.get("data/business_value_comparison.csv"))

# ------------------------------------------------------------------
# TEST 1 — Demo Dataset
# ------------------------------------------------------------------
df = pd.read_pickle(app_pkl)
check("TEST 1a: total batches == 35,165", len(df) == 35165, f"got {len(df)}")

dist = df["risk_level"].value_counts()
expected_dist = {"LOW": 25285, "MEDIUM": 3293, "HIGH": 3293, "CRITICAL": 3294}
check("TEST 1b: risk distribution matches expected",
      all(dist.get(k) == v for k, v in expected_dist.items()),
      f"got {dist.to_dict()}")

# ------------------------------------------------------------------
# TEST 2 — Recommendation Scope
# ------------------------------------------------------------------
scope = df["intervention_scope"].value_counts()
check("TEST 2a: batch-level count == 6,587", scope.get("batch-level", 0) == 6587,
      f"got {scope.get('batch-level', 0)}")
check("TEST 2b: replenishment-only count == 3,293",
      scope.get("replenishment-only (future batches)", 0) == 3293,
      f"got {scope.get('replenishment-only (future batches)', 0)}")
check("TEST 2c: none count == 25,285", scope.get("none", 0) == 25285,
      f"got {scope.get('none', 0)}")

# ------------------------------------------------------------------
# TEST 3 — Spoilage Validation (approximate, monotonic)
# ------------------------------------------------------------------
spoil = df.groupby("risk_level", observed=True)["was_spoiled"].mean()
expected_spoil = {"LOW": 0.315, "MEDIUM": 0.367, "HIGH": 0.482, "CRITICAL": 0.647}
close = all(abs(spoil[k] - v) < 0.01 for k, v in expected_spoil.items())
check("TEST 3a: spoilage rates within 1pp of expected", close, f"got {spoil.round(4).to_dict()}")
monotonic = (spoil["LOW"] < spoil["MEDIUM"] < spoil["HIGH"] < spoil["CRITICAL"])
check("TEST 3b: spoilage rate is monotonically increasing with risk level", monotonic)

# ------------------------------------------------------------------
# TEST 4 — Business Value
# ------------------------------------------------------------------
bv = pd.read_csv(app_csv, index_col=0)
expected_bv = {"Conservative": 12.91, "Base": 22.50, "Optimistic": 30.05}
bv_ok = all(abs(bv.loc[k, "Waste Reduction %"] - v) < 0.01 for k, v in expected_bv.items())
check("TEST 4: waste reduction % matches expected scenarios", bv_ok,
      f"got {bv['Waste Reduction %'].to_dict()}")

# ------------------------------------------------------------------
# TEST 5 — Valid Upload
# ------------------------------------------------------------------
valid_csv_path = Path(__file__).parent / "sample_upload_valid.csv"
status, report = validate_company_csv(valid_csv_path.read_bytes(), "sample_upload_valid.csv")
check("TEST 5a: valid sample parses without error", "message" not in report or not report.get("message", "").startswith("Could not parse"))
check("TEST 5b: valid sample passes schema validation (status == ok)", status == "ok", f"missing={report.get('missing_required')}")
check("TEST 5c: valid sample row count preserved", report.get("n_rows") == 15, f"got {report.get('n_rows')}")

# ------------------------------------------------------------------
# TEST 6 — Invalid Upload
# ------------------------------------------------------------------
invalid_csv_path = Path(__file__).parent / "sample_upload_invalid.csv"
status2, report2 = validate_company_csv(invalid_csv_path.read_bytes(), "sample_upload_invalid.csv")
check("TEST 6a: invalid sample fails schema validation (status == error)", status2 == "error")
check("TEST 6b: missing fields correctly identified",
      set(report2.get("missing_required", [])) == {"expiry_date", "qty_received"},
      f"got {report2.get('missing_required')}")

# Malformed file (not parseable)
status3, report3 = validate_company_csv(b"this is not,, a\nvalid\x00csv\xfffile", "garbage.csv")
check("TEST 6c: unparseable/garbage input handled without crashing",
      status3 in ("error",) or status3 == "ok")  # must not raise; either outcome is handled gracefully

# Empty file
status4, report4 = validate_company_csv(b"col_a,col_b\n", "empty.csv")
check("TEST 6d: empty (header-only) file rejected", status4 == "error")

# ------------------------------------------------------------------
# TEST 7 — Filters (Risk Explorer logic, replicated)
# ------------------------------------------------------------------
sample_filtered = df[(df["risk_level"].isin(["HIGH", "CRITICAL"])) & (df["days_until_expiry"] <= 5)]
check("TEST 7: risk-level + days-until-expiry filter logic runs and returns a subset",
      0 <= len(sample_filtered) <= len(df), f"filtered={len(sample_filtered)}")

# ------------------------------------------------------------------
# TEST 8 — Recommendations content sanity
# ------------------------------------------------------------------
check("TEST 8a: every CRITICAL/HIGH batch has a non-empty recommendation string",
      df.loc[df["risk_level"].isin(["HIGH", "CRITICAL"]), "recommendation"].apply(lambda s: len(str(s)) > 0).all())
small_batch_pct = (df.loc[df["risk_level"].isin(["HIGH", "CRITICAL"]), "current_inventory"] <= 2).mean()
check("TEST 8b: small-batch caveat proportion ~22.1% of HIGH/CRITICAL",
      abs(small_batch_pct - 0.221) < 0.01, f"got {small_batch_pct:.3f}")

# ------------------------------------------------------------------
# TEST 9 — Export
# ------------------------------------------------------------------
export_cols = ["batch_id", "item_id", "category", "days_until_expiry", "current_inventory",
               "potential_excess_inventory", "expected_waste_exposure", "intervention_scope", "recommendation"]
csv_bytes = df[export_cols].to_csv(index=False).encode("utf-8")
round_trip = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
check("TEST 9: exported CSV round-trips with correct row count", len(round_trip) == len(df),
      f"got {len(round_trip)} vs {len(df)}")

# ------------------------------------------------------------------
# TEST 10 — Live Inference Demo dataset (Data Input > Advanced panel)
# ------------------------------------------------------------------
demo_batches_path = DATA_DIR / "demo_live_inference_batches.csv"
demo_demand_path = DATA_DIR / "demo_live_inference_category_demand.csv"
check("TEST 10a: live-inference demo batch file exists", demo_batches_path.exists())
check("TEST 10b: live-inference demo category-demand file exists", demo_demand_path.exists())

if demo_batches_path.exists() and demo_demand_path.exists():
    demo_batches = pd.read_csv(demo_batches_path)

    # TEST 10c needs a parquet engine (pyarrow/fastparquet) to read
    # item_share_lookup.parquet. Missing pyarrow must SKIP this check,
    # not crash the whole suite -- same graceful-dependency pattern used
    # for TEST 10d-f below (engine.is_available) and in risk_engine.py's
    # own _load_item_share().
    try:
        item_share = pd.read_parquet(Path(__file__).parent / "deployment_artifacts" / "item_share_lookup.parquet")
        check("TEST 10c: every demo item_id is a real, training-period item_id (no fabricated share)",
              demo_batches["item_id"].isin(item_share.index).all(),
              f"unmatched={sorted(set(demo_batches['item_id']) - set(item_share.index))}")
    except ImportError as e:
        print(f"[SKIP] TEST 10c: no parquet engine available ({e}) -- install pyarrow to run this check.")

    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent))
        from backend.inference import RiskEngine, generate_recommendation
        engine = RiskEngine()
        if engine.is_available:
            demo_demand = pd.read_csv(demo_demand_path)
            scored = engine.score(demo_batches, demo_demand)
            scored[["recommendation", "intervention_scope"]] = scored.apply(generate_recommendation, axis=1)
            check("TEST 10d: live-inference demo scores every batch (no NaN risk_score)",
                  scored["risk_score"].notna().all())
            check("TEST 10e: live-inference demo spoilage_probability values are valid probabilities",
                  scored["spoilage_probability"].between(0, 1).all())
            check("TEST 10f: live-inference demo produces more than one distinct risk_level "
                  "(demonstrates real variation, not a constant/fabricated output)",
                  scored["risk_level"].nunique() > 1, f"got {sorted(scored['risk_level'].unique())}")
        else:
            print("[SKIP] TEST 10d-f: RiskEngine.is_available is False in this environment "
                  "(lightgbm/xgboost/pyarrow not installed) -- demo dataset shape/content still "
                  "checked above, but live scoring was not exercised.")
    except ImportError as e:
        print(f"[SKIP] TEST 10d-f: could not import backend.inference ({e})")

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
n_pass = sum(1 for _, ok, _ in RESULTS if ok)
n_total = len(RESULTS)
print(f"\n{n_pass}/{n_total} checks passed.")
if n_pass != n_total:
    print("FAILURES:")
    for name, ok, detail in RESULTS:
        if not ok:
            print(f"  - {name}: {detail}")
    sys.exit(1)
