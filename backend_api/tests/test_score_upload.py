import io

import pandas as pd

from backend_api.core.config import DEMO_BATCHES_PATH, DEMO_CATEGORY_DEMAND_PATH


def _demo_file_bytes():
    return DEMO_BATCHES_PATH.read_bytes(), DEMO_CATEGORY_DEMAND_PATH.read_bytes()


def test_validate_upload_valid_csvs(client):
    batches_bytes, demand_bytes = _demo_file_bytes()
    files = {
        "batches_file": ("batches.csv", batches_bytes, "text/csv"),
        "category_demand_file": ("demand.csv", demand_bytes, "text/csv"),
    }
    resp = client.post("/api/score/validate", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is True
    assert body["n_invalid_rows"] == 0
    assert len(body["preview"]) > 0


def test_upload_and_score_valid_csvs(client):
    batches_bytes, demand_bytes = _demo_file_bytes()
    files = {
        "batches_file": ("batches.csv", batches_bytes, "text/csv"),
        "category_demand_file": ("demand.csv", demand_bytes, "text/csv"),
    }
    resp = client.post("/api/score/upload", files=files)
    assert resp.status_code == 200
    body = resp.json()
    n_expected = len(pd.read_csv(DEMO_BATCHES_PATH))
    assert body["summary"]["total_records_scored"] == n_expected


def test_upload_does_not_score_when_validation_fails(client):
    _batches_bytes, demand_bytes = _demo_file_bytes()
    bad_batches_csv = b"batch_id,item_id,category\nX1,I1,FOODS_1\n"  # missing most required columns
    files = {
        "batches_file": ("bad.csv", bad_batches_csv, "text/csv"),
        "category_demand_file": ("demand.csv", demand_bytes, "text/csv"),
    }
    resp = client.post("/api/score/upload", files=files)
    assert resp.status_code == 400
    body = resp.json()["detail"]
    assert body["valid"] is False
    assert len(body["errors"]) > 0


def test_validate_empty_csv(client):
    _batches_bytes, demand_bytes = _demo_file_bytes()
    files = {
        "batches_file": ("empty.csv", b"", "text/csv"),
        "category_demand_file": ("demand.csv", demand_bytes, "text/csv"),
    }
    resp = client.post("/api/score/validate", files=files)
    assert resp.status_code == 400


def test_validate_malformed_csv(client):
    _batches_bytes, demand_bytes = _demo_file_bytes()
    files = {
        "batches_file": ("bad.csv", b"\x00\x01\xff\xfe garbage \x00", "text/csv"),
        "category_demand_file": ("demand.csv", demand_bytes, "text/csv"),
    }
    resp = client.post("/api/score/validate", files=files)
    assert resp.status_code == 400


def test_validate_missing_columns(client):
    _batches_bytes, demand_bytes = _demo_file_bytes()
    incomplete_csv = b"batch_id,item_id,category\nX1,I1,FOODS_1\n"
    files = {
        "batches_file": ("bad.csv", incomplete_csv, "text/csv"),
        "category_demand_file": ("demand.csv", demand_bytes, "text/csv"),
    }
    resp = client.post("/api/score/validate", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is False
    assert body["n_invalid_rows"] >= 1
    assert len(body["errors"]) > 0


def test_validate_reports_missing_category_demand_row(client):
    batches_bytes, demand_bytes = _demo_file_bytes()
    demand_df = pd.read_csv(io.BytesIO(demand_bytes))
    partial_demand_csv = demand_df[demand_df["category"] != "FOODS_2"].to_csv(index=False).encode()
    files = {
        "batches_file": ("batches.csv", batches_bytes, "text/csv"),
        "category_demand_file": ("demand.csv", partial_demand_csv, "text/csv"),
    }
    resp = client.post("/api/score/validate", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is False
    assert any("FOODS_2" in e["message"] for e in body["errors"])


def test_score_response_never_leaks_filesystem_paths_on_error(client):
    _batches_bytes, demand_bytes = _demo_file_bytes()
    files = {
        "batches_file": ("bad.csv", b"", "text/csv"),
        "category_demand_file": ("demand.csv", demand_bytes, "text/csv"),
    }
    resp = client.post("/api/score/validate", files=files)
    assert "/home/" not in resp.text
    assert "/mnt/" not in resp.text
    assert "Traceback" not in resp.text
