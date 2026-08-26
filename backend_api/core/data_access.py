"""
backend_api/core/data_access.py
==================================
Read-only access to the frozen VENTORA artifacts, with in-memory caching so
the pickle/CSV are loaded once per process rather than once per request
(the FastAPI equivalent of app.py's @st.cache_data).

This module does not compute anything new. It loads exactly the files
app.py already loads (data/risk_df_recommendations_FINAL.pkl,
data/business_value_comparison.csv, deployment_artifacts/model_metadata.json,
deployment_artifacts/feature_config.json) and verifies their SHA-256 hashes
against FROZEN_ARTIFACT_HASHES.txt before serving them.

If a hash mismatch is detected, this module raises rather than silently
serving data that may have drifted from the verified/frozen state -- the
API is designed to fail loudly at startup in that case (see main.py).
"""
import hashlib
import json
import logging
from functools import lru_cache
from pathlib import Path

import pandas as pd

from backend_api.core.config import (
    RISK_DF_PATH,
    BUSINESS_VALUE_PATH,
    MODEL_METADATA_PATH,
    FEATURE_CONFIG_PATH,
    FROZEN_HASHES_FILE,
    VENTORA_APP_DIR,
    RISK_LEVELS_ORDER,
)


class DataIntegrityError(RuntimeError):
    """Raised when a frozen artifact's hash does not match FROZEN_ARTIFACT_HASHES.txt."""


class DataUnavailableError(RuntimeError):
    """Raised when a required frozen artifact/file cannot be found or read."""


def _sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file, matching test_app.py's sha256()."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_frozen_hashes() -> dict[str, str]:
    """Parse FROZEN_ARTIFACT_HASHES.txt into {relative_path: hex_digest}.

    Format matches test_app.py's load_frozen_hashes(): one "<hash>  <rel_path>"
    line per file, relative to the ventora_app/ directory.
    """
    if not FROZEN_HASHES_FILE.exists():
        raise DataUnavailableError(
            f"FROZEN_ARTIFACT_HASHES.txt not found at {FROZEN_HASHES_FILE}"
        )
    hashes: dict[str, str] = {}
    for line in FROZEN_HASHES_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel_path = line.split(None, 1)
        hashes[rel_path.strip()] = digest.strip()
    return hashes



# Artifacts listed in FROZEN_ARTIFACT_HASHES.txt that belong ONLY to the
# live-scoring inference layer (ventora_app/backend/inference), which is
# already intentionally disabled in the user-facing frontend (see
# frontend/src/App.tsx and HANDOFF.md). If ONLY these are missing, the
# read-only analytics API (Overview / Risk Explorer / Recommendations /
# Business Impact) must still be able to start and serve verified data --
# it does not read these files at all (see load_risk_df / load_business_value
# / load_metadata / load_feature_config below, none of which touch these
# two paths). This does NOT weaken verification for any artifact the
# analytics API actually serves: those remain hard-required and
# hash-checked exactly as before. If a file in this set IS present on
# disk, it is still hash-checked like any other -- a present-but-corrupted
# scoring artifact still fails loudly.
_SCORING_ONLY_ARTIFACTS = {
    "deployment_artifacts/spoilage_model.joblib",
    "deployment_artifacts/demand_model.joblib",
}


def verify_frozen_hashes() -> dict[str, str]:
    """Verify every frozen artifact listed in FROZEN_ARTIFACT_HASHES.txt still
    matches its recorded hash. Only checks files that actually exist on disk
    AND are listed in the hash file -- both must be true for a given file to
    be checked (a listed-but-missing file is a DataUnavailableError, not a
    silent skip) -- EXCEPT for the live-scoring-only artifacts in
    _SCORING_ONLY_ARTIFACTS, whose absence is downgraded to a logged warning
    because the feature that needs them is already disabled in the UI.

    Returns the verified {relative_path: hex_digest} mapping on success (for
    scoring-only artifacts that are missing, they are simply omitted from
    the returned mapping rather than verified).
    Raises DataIntegrityError on any hash mismatch (including in
    scoring-only artifacts, if present), DataUnavailableError if a
    non-scoring listed file is missing entirely.
    """
    expected = _load_frozen_hashes()
    mismatches = []
    missing = []
    missing_scoring_only = []
    verified: dict[str, str] = {}
    for rel_path, expected_digest in expected.items():
        full_path = VENTORA_APP_DIR / rel_path
        if not full_path.exists():
            if rel_path in _SCORING_ONLY_ARTIFACTS:
                missing_scoring_only.append(rel_path)
            else:
                missing.append(rel_path)
            continue
        actual_digest = _sha256(full_path)
        if actual_digest != expected_digest:
            mismatches.append((rel_path, expected_digest, actual_digest))
        else:
            verified[rel_path] = actual_digest

    if missing_scoring_only:
        logging.getLogger("ventora_api").warning(
            "Live-scoring-only artifact(s) missing (expected, since Live Scoring "
            "is disabled in the frontend): %s",
            ", ".join(missing_scoring_only),
        )

    if missing:
        raise DataUnavailableError(
            "Frozen artifact(s) listed in FROZEN_ARTIFACT_HASHES.txt are missing: "
            + ", ".join(missing)
        )
    if mismatches:
        detail = "; ".join(
            f"{p} (expected {exp[:12]}…, got {act[:12]}…)" for p, exp, act in mismatches
        )
        raise DataIntegrityError(
            "Frozen artifact hash mismatch -- one or more files no longer match "
            f"FROZEN_ARTIFACT_HASHES.txt: {detail}. Refusing to serve data that may "
            "have drifted from the verified state."
        )
    return verified


@lru_cache(maxsize=1)
def load_risk_df() -> pd.DataFrame:
    """Load the frozen, verified risk dataframe (35,165 batches), cached for
    the lifetime of the process. Identical to app.py's load_demo_risk_df():
    same file, same ordered-categorical cast on risk_level, no other change.
    """
    if not RISK_DF_PATH.exists():
        raise DataUnavailableError(f"{RISK_DF_PATH} not found.")
    df = pd.read_pickle(RISK_DF_PATH)
    df["risk_level"] = pd.Categorical(df["risk_level"], categories=RISK_LEVELS_ORDER, ordered=True)
    return df


@lru_cache(maxsize=1)
def load_business_value() -> pd.DataFrame:
    """Load the frozen business-value scenario table, cached. Identical to
    app.py's load_business_value(): same file, index_col=0, no recomputation.
    """
    if not BUSINESS_VALUE_PATH.exists():
        raise DataUnavailableError(f"{BUSINESS_VALUE_PATH} not found.")
    return pd.read_csv(BUSINESS_VALUE_PATH, index_col=0)


@lru_cache(maxsize=1)
def load_model_metadata() -> dict:
    """Load deployment_artifacts/model_metadata.json, cached, verbatim."""
    if not MODEL_METADATA_PATH.exists():
        raise DataUnavailableError(f"{MODEL_METADATA_PATH} not found.")
    with open(MODEL_METADATA_PATH) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_feature_config() -> dict:
    """Load deployment_artifacts/feature_config.json, cached, verbatim."""
    if not FEATURE_CONFIG_PATH.exists():
        raise DataUnavailableError(f"{FEATURE_CONFIG_PATH} not found.")
    with open(FEATURE_CONFIG_PATH) as f:
        return json.load(f)


def clear_all_caches() -> None:
    """Test-only helper: clear all lru_cache'd loaders so tests can reload
    fresh state (e.g. after pointing VENTORA_APP_DIR at a fixture dir).
    """
    load_risk_df.cache_clear()
    load_business_value.cache_clear()
    load_model_metadata.cache_clear()
    load_feature_config.cache_clear()
