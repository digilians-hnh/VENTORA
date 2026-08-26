def test_business_value_matches_frozen_csv(client, frozen_business_value):
    resp = client.get("/api/business-value")
    assert resp.status_code == 200
    body = resp.json()

    scenarios = {s["scenario"]: s for s in body["scenarios"]}
    assert set(scenarios.keys()) == set(frozen_business_value.index)

    for name, row in frozen_business_value.iterrows():
        api_row = scenarios[name]
        assert abs(api_row["baseline_waste_units"] - float(row["Baseline Waste Units"])) < 1e-6
        assert abs(api_row["ai_assisted_waste_units"] - float(row["AI-Assisted Waste Units"])) < 1e-6
        assert abs(api_row["waste_reduction_pct"] - float(row["Waste Reduction %"])) < 1e-6
        assert abs(api_row["baseline_spoilage_rate"] - float(row["Baseline Spoilage Rate"])) < 1e-6
        assert abs(api_row["ai_assisted_spoilage_rate"] - float(row["AI-Assisted Spoilage Rate"])) < 1e-6
        assert abs(api_row["spoilage_rate_reduction_pp"] - float(row["Spoilage Rate Reduction (pp)"])) < 1e-6
        assert api_row["intervention_count_high_critical"] == int(row["Intervention Count (HIGH+CRITICAL)"])
