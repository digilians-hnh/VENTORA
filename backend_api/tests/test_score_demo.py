import pandas as pd

from backend_api.core.config import DEMO_BATCHES_PATH


def test_get_demo_preview(client):
    resp = client.get("/api/score/demo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is True
    assert body["n_invalid_rows"] == 0
    assert len(body["preview"]) == len(pd.read_csv(DEMO_BATCHES_PATH))


def test_post_demo_scores_packaged_data(client):
    resp = client.post("/api/score/demo")
    assert resp.status_code == 200
    body = resp.json()
    n_expected = len(pd.read_csv(DEMO_BATCHES_PATH))
    assert body["summary"]["total_records_scored"] == n_expected
    assert body["summary"]["unresolved_count"] == 0
    # Demo data is designed to show variation across risk levels.
    nonzero_levels = [d["risk_level"] for d in body["summary"]["risk_distribution"] if d["count"] > 0]
    assert len(nonzero_levels) > 1
