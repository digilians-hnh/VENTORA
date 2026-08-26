def test_recommendations_all_levels_total_matches_frozen(client, frozen_risk_df):
    resp = client.get("/api/recommendations", params={"page_size": 1000})
    body = resp.json()
    assert body["total_rows"] == len(frozen_risk_df)


def test_recommendations_filtered_by_level_matches_frozen(client, frozen_risk_df):
    for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        resp = client.get("/api/recommendations", params={"level": level, "page_size": 1000})
        body = resp.json()
        expected_count = int((frozen_risk_df["risk_level"] == level).sum())
        assert body["total_rows"] == expected_count, f"level={level}"
        assert all(row["risk_level"] == level for row in body["rows"])


def test_recommendations_records_are_non_empty_strings(client, frozen_risk_df):
    resp = client.get("/api/recommendations", params={"level": "CRITICAL", "page_size": 1000})
    body = resp.json()
    assert len(body["rows"]) > 0
    assert all(len(row["recommendation"]) > 0 for row in body["rows"])


def test_recommendations_invalid_level_returns_400(client):
    resp = client.get("/api/recommendations", params={"level": "BOGUS"})
    assert resp.status_code == 400


def test_recommendations_content_matches_frozen_dataset_for_a_sample_batch(client, frozen_risk_df):
    # Pick a real batch from the frozen data, work out which page it lands
    # on under the API's documented sort order (expected_waste_exposure
    # descending, matching app.py's Recommendations tabs), and confirm the
    # API returns the exact same recommendation text/scope for it -- rather
    # than any newly generated value. page_size is capped at 1000 by the
    # API, so this walks pages instead of requesting the whole level at once.
    sample = frozen_risk_df.iloc[0]
    level = str(sample["risk_level"])
    page_size = 1000

    subset_sorted = (
        frozen_risk_df[frozen_risk_df["risk_level"] == level]
        .sort_values("expected_waste_exposure", ascending=False)
        .reset_index(drop=True)
    )
    position = subset_sorted.index[subset_sorted["batch_id"] == sample["batch_id"]][0]
    page = position // page_size + 1

    resp = client.get(
        "/api/recommendations",
        params={"level": level, "page": int(page), "page_size": page_size},
    )
    body = resp.json()
    match = next((r for r in body["rows"] if r["batch_id"] == sample["batch_id"]), None)
    assert match is not None
    assert match["recommendation"] == sample["recommendation"]
    assert match["intervention_scope"] == sample["intervention_scope"]
