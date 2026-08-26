import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend_api.core.config import BUSINESS_VALUE_PATH, RISK_DF_PATH, RISK_LEVELS_ORDER  # noqa: E402
from backend_api.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def frozen_risk_df() -> pd.DataFrame:
    """Loaded directly from disk, not via backend_api.core.data_access, so
    tests verify the API against ground truth rather than against its own
    cache.
    """
    df = pd.read_pickle(RISK_DF_PATH)
    df["risk_level"] = pd.Categorical(df["risk_level"], categories=RISK_LEVELS_ORDER, ordered=True)
    return df


@pytest.fixture(scope="session")
def frozen_business_value() -> pd.DataFrame:
    return pd.read_csv(BUSINESS_VALUE_PATH, index_col=0)
