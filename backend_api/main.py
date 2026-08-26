"""
backend_api/main.py
======================
VENTORA API -- a thin FastAPI wrapper around the existing, frozen VENTORA
analytics pipeline (ventora_app/). This service performs NO model
inference, NO retraining, and NO recomputation of any analytical result. It
loads the same verified files app.py already loads
(data/risk_df_recommendations_FINAL.pkl, data/business_value_comparison.csv,
deployment_artifacts/model_metadata.json) and serves them over HTTP with
server-side filtering/pagination.

At startup, every frozen artifact listed in FROZEN_ARTIFACT_HASHES.txt is
hash-verified. If any artifact has drifted from its recorded hash, or a
listed artifact is missing, startup fails loudly (raises) rather than
serving data that might not match the verified state.

Run:
    uvicorn backend_api.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_api.core.config import CORS_ALLOW_ORIGINS
from backend_api.core.data_access import (
    DataIntegrityError,
    DataUnavailableError,
    verify_frozen_hashes,
)
from backend_api.routers import analytics, health, recommendations

logger = logging.getLogger("ventora_api")

# The scoring router depends on ventora_app/backend/inference (frozen live-
# scoring layer, not included in every delivery/environment of this repo,
# and known to have a pre-existing XGBoost/scikit-learn compatibility issue
# on some machines -- see HANDOFF.md). Live Scoring is already intentionally
# removed from the user-facing frontend (see App.tsx), so a missing/broken
# scoring import here must NOT take down the read-only analytics API that
# Overview / Risk Explorer / Recommendations / Business Impact depend on.
# This is purely an import guard -- no scoring logic, model, or frozen
# artifact is touched or modified.
try:
    from backend_api.routers import scoring

    _SCORING_AVAILABLE = True
except ImportError:
    logger.warning(
        "Scoring router unavailable (ventora_app/backend/inference not importable "
        "in this environment) -- starting API WITHOUT scoring endpoints. This is "
        "expected/harmless: Live Scoring is already disabled in the frontend UI.",
        exc_info=True,
    )
    scoring = None
    _SCORING_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Fail loudly at startup if any frozen artifact has drifted from
    FROZEN_ARTIFACT_HASHES.txt, or is missing. Never silently regenerates
    or substitutes data.
    """
    try:
        verified = verify_frozen_hashes()
    except (DataIntegrityError, DataUnavailableError):
        logger.exception("Frozen artifact integrity check FAILED at startup.")
        raise
    logger.info("Frozen artifact integrity verified for %d file(s).", len(verified))
    yield


app = FastAPI(
    title="VENTORA API",
    description=(
        "Read-only API wrapper over the frozen, verified VENTORA analytics "
        "pipeline. No inference, retraining, or recomputation happens here."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(analytics.router)
app.include_router(recommendations.router)
if _SCORING_AVAILABLE:
    app.include_router(scoring.router)
