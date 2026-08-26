"""
backend_api/core/config.py
============================
Locates the existing, frozen VENTORA project (ventora_app/) that this API
wraps. Nothing under ventora_app/ is copied or duplicated here -- the API
reads the same files in place, so there is exactly one copy of every frozen
artifact on disk and no risk of the API drifting from it.

The path is resolvable two ways:
  1. VENTORA_APP_DIR environment variable (explicit override, e.g. in a
     Docker image where the layout differs).
  2. Default: "<repo_root>/ventora_app", i.e. a sibling directory of
     backend_api/ -- matches this delivery's actual layout.
"""
import os
from pathlib import Path

BACKEND_API_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VENTORA_APP_DIR = BACKEND_API_DIR.parent / "ventora_app"

VENTORA_APP_DIR = Path(os.environ.get("VENTORA_APP_DIR", str(DEFAULT_VENTORA_APP_DIR))).resolve()

DATA_DIR = VENTORA_APP_DIR / "data"
DEPLOYMENT_ARTIFACTS_DIR = VENTORA_APP_DIR / "deployment_artifacts"
FROZEN_HASHES_FILE = VENTORA_APP_DIR / "FROZEN_ARTIFACT_HASHES.txt"

RISK_DF_PATH = DATA_DIR / "risk_df_recommendations_FINAL.pkl"
BUSINESS_VALUE_PATH = DATA_DIR / "business_value_comparison.csv"
MODEL_METADATA_PATH = DEPLOYMENT_ARTIFACTS_DIR / "model_metadata.json"
FEATURE_CONFIG_PATH = DEPLOYMENT_ARTIFACTS_DIR / "feature_config.json"

# Packaged synthetic demo files for the "Demo/Sample Data" live-scoring path
# on the Data Input page -- same files app.py's "Load Live Inference Demo"
# button already reads. Not real company/sales data.
DEMO_BATCHES_PATH = DATA_DIR / "demo_live_inference_batches.csv"
DEMO_CATEGORY_DEMAND_PATH = DATA_DIR / "demo_live_inference_category_demand.csv"

RISK_LEVELS_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# CORS: local React dev servers only, for now. Widen/lock down per
# environment when the frontend is actually deployed -- not decided here.
CORS_ALLOW_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
