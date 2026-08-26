"""
backend_api/core/inference_adapter.py
========================================
Thin adapter over the FROZEN ventora_app/backend/inference package. This
module does not reimplement, wrap-with-logic-changes, or duplicate any
model/formula -- it only makes the existing, unmodified
`backend.inference` package importable from backend_api by adding
ventora_app/ to sys.path, exactly the way app.py already imports it
(`from backend.inference import RiskEngine, ModelUnavailableError,
generate_recommendation`).

No file under ventora_app/ is copied, edited, or executed differently here.
"""
import sys

from backend_api.core.config import VENTORA_APP_DIR

if str(VENTORA_APP_DIR) not in sys.path:
    sys.path.insert(0, str(VENTORA_APP_DIR))

from backend.inference import (  # noqa: E402  (path must be set up first)
    DemandPredictor,
    ModelUnavailableError,
    RiskEngine,
    SpoilagePredictor,
    generate_recommendation,
)

__all__ = [
    "RiskEngine",
    "SpoilagePredictor",
    "DemandPredictor",
    "ModelUnavailableError",
    "generate_recommendation",
]


def get_risk_engine() -> RiskEngine:
    """Construct a RiskEngine pointed at the frozen deployment_artifacts/
    directory (RiskEngine's own default), fresh per call -- cheap, since
    RiskEngine lazily loads and caches its own model/lookup state on first
    use within that instance.
    """
    from backend_api.core.config import DEPLOYMENT_ARTIFACTS_DIR

    return RiskEngine(artifacts_dir=DEPLOYMENT_ARTIFACTS_DIR)
