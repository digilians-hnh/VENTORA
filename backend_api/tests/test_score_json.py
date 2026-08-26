from backend_api.tests.scoring_fixtures import load_demo_records


def test_valid_json_scoring_returns_expected_shape(client):
    batches, demand = load_demo_records()
    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    assert resp.status_code == 200
    body = resp.json()

    assert body["summary"]["total_records_scored"] == len(batches)
    assert len(body["rows"]) == len(batches)
    assert "methodology_note" in body
    assert "relative to the batches submitted" in body["methodology_note"]

    for row in body["rows"]:
        assert row["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL", None)
        if row["risk_score"] is not None:
            assert 0 <= row["risk_score"] <= 100
        if row["spoilage_probability"] is not None:
            assert 0 <= row["spoilage_probability"] <= 1
        assert isinstance(row["recommendation"], str) and len(row["recommendation"]) > 0


def test_recommendation_matches_frozen_engine_for_known_inputs(client):
    """Sanity-check the API's recommendation text against the frozen
    recommendation_engine_3.generate_recommendation() called directly --
    same inputs must produce the exact same text via either path.
    """
    from backend_api.core.inference_adapter import generate_recommendation, get_risk_engine
    import pandas as pd

    batches, demand = load_demo_records()
    engine = get_risk_engine()
    scored_direct = engine.score(pd.DataFrame(batches), pd.DataFrame(demand))
    scored_direct[["recommendation", "intervention_scope"]] = scored_direct.apply(generate_recommendation, axis=1)

    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    api_rows = {r["batch_id"]: r for r in resp.json()["rows"]}

    for _, row in scored_direct.iterrows():
        api_row = api_rows[row["batch_id"]]
        assert api_row["recommendation"] == row["recommendation"]
        assert api_row["intervention_scope"] == row["intervention_scope"]


def test_missing_required_field_returns_422(client):
    batches, demand = load_demo_records()
    del batches[0]["category"]
    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    assert resp.status_code == 422


def test_invalid_categorical_value_returns_422(client):
    batches, demand = load_demo_records()
    batches[0]["category"] = "NOT_A_REAL_CATEGORY"
    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    assert resp.status_code == 422


def test_wrong_data_type_returns_422(client):
    batches, demand = load_demo_records()
    batches[0]["qty_received"] = "not_a_number"
    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    assert resp.status_code == 422


def test_negative_value_returns_422(client):
    batches, demand = load_demo_records()
    batches[0]["current_inventory"] = -5
    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    assert resp.status_code == 422


def test_empty_batches_list_returns_422(client):
    _batches, demand = load_demo_records()
    resp = client.post("/api/score", json={"batches": [], "category_demand": demand})
    assert resp.status_code == 422


def test_duplicate_batch_id_returns_422(client):
    batches, demand = load_demo_records()
    dup = dict(batches[0])
    batches.append(dup)
    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    assert resp.status_code == 422


def test_missing_category_demand_row_returns_422(client):
    batches, demand = load_demo_records()
    demand = [d for d in demand if d["category"] != batches[0]["category"]]
    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    assert resp.status_code == 422


def test_unknown_item_id_does_not_crash_and_returns_null_risk_score(client):
    """Mirrors test_inference.py's frozen-layer test: an unrecognized
    item_id must come back with a null risk_score and an explanatory
    note, never a crash or a fabricated score.
    """
    batches, demand = load_demo_records()
    batches[0]["item_id"] = "TOTALLY_UNKNOWN_ITEM_ID_XYZ"
    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    assert resp.status_code == 200
    row = next(r for r in resp.json()["rows"] if r["batch_id"] == batches[0]["batch_id"])
    assert row["risk_score"] is None
    assert row["risk_level"] is None
    assert row["risk_score_note"] is not None and len(row["risk_score_note"]) > 0
    assert resp.json()["summary"]["unresolved_count"] >= 1


def test_response_is_json_serializable_with_no_nan_literal(client):
    batches, demand = load_demo_records()
    batches[0]["item_id"] = "TOTALLY_UNKNOWN_ITEM_ID_XYZ"
    resp = client.post("/api/score", json={"batches": batches, "category_demand": demand})
    assert "NaN" not in resp.text
