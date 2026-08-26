import json

from backend_api.core.config import MODEL_METADATA_PATH


def test_metadata_matches_frozen_json(client, frozen_risk_df):
    with open(MODEL_METADATA_PATH) as f:
        expected = json.load(f)

    resp = client.get("/api/metadata")
    assert resp.status_code == 200
    body = resp.json()

    assert body["export_timestamp_utc"] == expected["export_timestamp_utc"]
    assert body["chronological_split_cutoff"] == expected["chronological_split_cutoff"]
    assert body["spoilage_model"]["algorithm"] == expected["spoilage_model"]["algorithm"]
    assert body["spoilage_model"]["training_rows"] == expected["spoilage_model"]["training_rows"]
    assert body["spoilage_model"]["test_rows"] == expected["spoilage_model"]["test_rows"]
    assert body["demand_model"]["algorithm"] == expected["demand_model"]["algorithm"]
    assert body["demand_model"]["training_rows"] == expected["demand_model"]["training_rows"]
    assert body["demand_model"]["test_rows"] == expected["demand_model"]["test_rows"]
    assert body["total_evaluation_batches"] == len(frozen_risk_df)
    assert body["training_data_assumptions"] == expected["training_data_assumptions"]


def test_metadata_does_not_leak_filesystem_paths(client):
    resp = client.get("/api/metadata")
    body_text = resp.text
    assert "/home/" not in body_text
    assert "/mnt/" not in body_text
    assert "deployment_artifacts" not in body_text
