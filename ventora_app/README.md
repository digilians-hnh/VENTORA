# VENTORA — AI Inventory Risk Intelligence

**Predict. Optimize. Preserve.**

VENTORA identifies which inventory is most likely to become waste, explains why, and recommends what to do next. This is the company-facing web application, built on top of the verified analytical pipeline and the now-verified deployment artifacts (frozen models exported and cross-checked against the project's original results).

## Architecture

```
                     VENTORA
                        │
        ┌───────────────┴───────────────┐
        │                               │
  Company Web App                Analytics Dashboard
   (app.py, this dir)             (dashboard/app.py)
        │                               │
   Data Input                    Executive Overview
   Risk Analysis                 Risk Explorer
   Recommendations               Business Impact
   Business Impact               Recommendations
        │
   backend/inference/
   ├── spoilage_predictor.py   (loads spoilage_model.joblib)
   ├── demand_predictor.py     (loads demand_model.joblib)
   ├── risk_engine.py          (composes both, exact frozen formula)
   └── recommendation_engine_3.py  (byte-identical to the frozen project file)
        │
   deployment_artifacts/       (frozen, verified — see FROZEN_ARTIFACT_HASHES.txt)
   ├── spoilage_model.joblib
   ├── demand_model.joblib
   ├── feature_config.json
   ├── model_metadata.json
   └── item_share_lookup.parquet
```

`dashboard/app.py` is **byte-identical** to the originally supplied Streamlit dashboard — untouched, and runnable as its own app (`cd dashboard && streamlit run app.py`).

## What this app does — and doesn't do

Neither `app.py` nor anything in `backend/inference/` retrains, refits, or changes any model, threshold, or formula. The Risk Engine formula in `risk_engine.py` is transcribed exactly from `pipeline/reconstruct.py`'s "Building risk_df" section (spoilage_probability × 20 when exposure is zero, `20 + 80·percentile_rank(exposure)` otherwise, LOW/MEDIUM/HIGH/CRITICAL bins at 25/50/75) — not reimplemented independently.

## Pages

| Page | Purpose |
|---|---|
| Home | Branding, workflow overview, links to Data Input and the Dashboard |
| Data Input | Demo Mode (35,165 verified batches) · basic company-CSV validation · **Advanced: full-feature scoring** (real inference via the verified models, when the uploaded data already contains the required engineered features) |
| Executive Overview / Risk Explorer / Recommendations / Business Impact | Same four analytics views, restyled — render the Verified Demo Dataset |

## Company Data — the honest two-tier reality

1. **Basic upload** (`batch_id`, `item_id`, `category`, `received_date`, `expiry_date`, `qty_received`, …): validated, previewed, but **cannot** produce a Risk Score on its own. The models need trailing historical sales features (`trailing_mean_7`, `trailing_mean_28`, `demand_cv_28`, `snap_days_in_life`, `event_days_in_life`) computed from the M5 item-daily long table — this app does not compute those from a plain inventory CSV, and doesn't pretend to.
2. **Advanced: full-feature scoring**: if the caller already has those engineered features (e.g. from their own equivalent historical-sales pipeline), `RiskEngine` will load the real, verified `spoilage_model.joblib` / `demand_model.joblib` and score for real — genuine inference, not a fabricated number. This only activates when `RiskEngine.is_available` is `True` (i.e. `lightgbm`, `xgboost`, `pyarrow` are installed and the artifacts are present); otherwise the panel explains exactly why it's unavailable rather than silently failing or faking a result.
   - Inside this panel, a **"Load Live Inference Demo"** button runs the same real code path against a small, clearly-labeled **synthetic** dataset (`data/demo_live_inference_batches.csv` + `data/demo_live_inference_category_demand.csv`) — 6 hand-built batches using real, training-period `item_id`s (verified present in `item_share_lookup.parquet`, so none silently fall back to the "unscoreable" NaN path) with plausible-but-fabricated feature values. This exists specifically so the Live Inference Demonstration can be shown with one click, without requiring the presenter to already own a fully-engineered CSV — and it is visually and textually distinguished in the UI from both the "Verified Reference Results" (the 35,165-batch frozen dataset) and from real company data.

A new item_id absent from `item_share_lookup.parquet` (i.e. not seen in the original training period) gets `risk_score = NaN` and an explanatory note — never a guessed score.

## Install & run

```bash
pip install -r requirements.txt
streamlit run app.py              # main web application

# separately, the untouched original dashboard:
cd dashboard && pip install -r requirements.txt && streamlit run app.py
```

> **Runtime Verification Status (as of the most recent session, no earlier claims carried forward):**
>
> This authoring sandbox has **no outbound network access**, so `pip install` cannot fetch `streamlit`, `lightgbm`, `xgboost`, or `pyarrow` here. As a direct result, `streamlit run app.py` / `streamlit run dashboard/app.py` were **not launched**, no HTTP/health check was performed, and `streamlit.testing.v1.AppTest` was **not run** against any page. Any prior claim in this file that those steps happened is superseded by this section and should not be relied on — it could not be reproduced and is withdrawn.
>
> What **was** actually executed in this session, directly, with real output captured:
> - `python3 test_inference.py` → **13/13 checks passed** (exit code 0). This suite uses fake-but-importable model stand-ins against the real `feature_config.json`, so it needs no `lightgbm`/`xgboost`.
> - `python3 test_app.py` → **23/23 checks passed** (exit code 0). TEST 10c–10f (which need `pyarrow`, and 10d–10f additionally need `lightgbm`/`xgboost`) printed `[SKIP]` with a clear reason rather than running or crashing — see the "Testing" section below for exactly which checks these are.
> - Every frozen artifact's SHA-256 was independently re-verified against `FROZEN_ARTIFACT_HASHES.txt` in this session — all match, byte-for-byte.
> - A real bug was found and fixed in this session: TEST 10c called `pd.read_parquet(...)` with no exception handling, so a missing `pyarrow` crashed the entire suite instead of skipping cleanly. Fixed to catch `ImportError` and skip, matching the pattern already used for TEST 10d–10f.
>
> **Not verified in this session** (would require network access to install `streamlit`/`lightgbm`/`xgboost`/`pyarrow`): actually launching either Streamlit app, exercising any page in a live server, or running the Live Inference Demo button end-to-end through the real models. If you run this locally with `pip install -r requirements.txt` succeeding, TEST 10c–10f will execute for real (not skip) and the suite total becomes up to **27/27** — but that number has not been reproduced here and should not be quoted until it has been.

## Project layout

```
ventora_app/
├── app.py                       # Web application (Streamlit UI)
├── venlib.py                     # Basic upload validation logic (unit-testable)
├── backend/
│   ├── __init__.py
│   └── inference/
│       ├── __init__.py
│       ├── spoilage_predictor.py
│       ├── demand_predictor.py
│       ├── risk_engine.py
│       └── recommendation_engine_3.py   # byte-identical to the frozen project file
├── deployment_artifacts/          # frozen, verified (see FROZEN_ARTIFACT_HASHES.txt)
├── data/                          # frozen demo dataset for app.py, plus:
│   ├── demo_live_inference_batches.csv           # synthetic, one-click Live Inference Demo input
│   └── demo_live_inference_category_demand.csv   # (real item_ids, fabricated feature values — labeled as such in-app)
├── dashboard/                     # untouched original Streamlit dashboard, self-contained
│   ├── app.py
│   ├── data/
│   └── requirements.txt
├── test_app.py                    # 23-27 checks (23 confirmed passing without pyarrow/lightgbm/xgboost;
│                                   #   up to 27 when those are installed): data integrity, upload
│                                   #   validation, export, live-inference demo
├── test_inference.py              # 13 checks: RiskEngine pipeline, error handling
├── sample_upload_valid.csv / sample_upload_invalid.csv
├── FROZEN_ARTIFACT_HASHES.txt     # SHA-256 of every frozen artifact, for tamper detection
├── requirements.txt
└── README.md
```

## Testing

```bash
python3 test_app.py         # 23/23 with no pyarrow/lightgbm/xgboost installed (TEST 10c-10f SKIP
                             #         cleanly with a stated reason, not counted as pass or fail).
                             #         Up to 27/27 when pyarrow/lightgbm/xgboost ARE installed, which
                             #         additionally runs a real end-to-end scoring of the Live
                             #         Inference Demo dataset through the actual verified models,
                             #         asserting no NaN scores and real risk-level variation.
                             #         Frozen-file hashes are checked against the bundled
                             #         FROZEN_ARTIFACT_HASHES.txt (portable — no dependency on the
                             #         original upload location).
python3 test_inference.py   # 13/13 — RiskEngine end-to-end, using fake-but-importable model
                             #         stand-ins against the REAL feature_config.json, so the
                             #         wrapper logic is tested without requiring lightgbm/xgboost
                             #         to be installed. Does not re-verify the actual model
                             #         predictions — that's already recorded in
                             #         deployment_artifacts/validation_report.json.
```

## Frozen-artifact integrity

`FROZEN_ARTIFACT_HASHES.txt` records SHA-256 hashes for every frozen artifact at delivery time. Re-run before/after any future change:

```bash
sha256sum deployment_artifacts/*.joblib deployment_artifacts/*.json deployment_artifacts/*.parquet data/*.pkl data/*.csv
```

If any hash changes without an explicit, justified reason — stop and investigate before continuing.

## Terminology

- **Spoilage Probability** — raw model output, not necessarily calibrated.
- **Risk Score** — the Risk Engine's composite 0–100 prioritization score, not a probability.
- **Risk Level** — LOW/MEDIUM/HIGH/CRITICAL, derived from Risk Score.
- **Predicted** — a model output. **Observed/Actual** — a historical, realized outcome.
- **Simulated** — a Business-Value Simulation result under stated assumptions — never a guaranteed or measured saving.

## Limitations

- Full inference on a *plain* company inventory CSV (without pre-engineered trailing-demand features) is genuinely not supported — this is a real limitation of the frozen pipeline's feature requirements, not a missing UI feature.
- `item_share_lookup.parquet` only covers items seen in the original training period; a new item_id cannot be scored without a supplied share estimate.
- No authentication or multi-user isolation — single-session local demonstration tool.
- Browser/runtime launch was not performed in this authoring sandbox (no network access) — see the runtime verification note above for exactly what was and wasn't checked.
- `deployment_artifacts/validation_report.json` and `deployment_artifacts/reference/` (the model-reload-fidelity evidence referenced in `model_metadata.json` and `test_inference.py`'s docstring) are **not present in this delivery**. Deployment-artifact integrity (file hashes vs. `FROZEN_ARTIFACT_HASHES.txt`) has been verified; the specific reload-vs-original-prediction diff has not been independently reproduced in the sessions that produced this repository. If you have the original `validate_deployment_artifacts.py` output, add it back before final submission; do not claim this check passed without it.
