from backend_api.core.config import RISK_LEVELS_ORDER


def test_summary_matches_frozen_data(client, frozen_risk_df, frozen_business_value):
    resp = client.get("/api/summary")
    assert resp.status_code == 200
    body = resp.json()

    assert body["total_batches"] == len(frozen_risk_df)

    dist = frozen_risk_df["risk_level"].value_counts().reindex(RISK_LEVELS_ORDER).fillna(0).astype(int)
    high_crit_n = int(dist["HIGH"] + dist["CRITICAL"])
    assert body["high_critical_batches"] == high_crit_n

    api_dist = {e["risk_level"]: e["count"] for e in body["risk_distribution"]}
    for level in RISK_LEVELS_ORDER:
        assert api_dist[level] == int(dist[level])

    spoil_by_level = frozen_risk_df.groupby("risk_level", observed=True)["was_spoiled"].mean().reindex(RISK_LEVELS_ORDER)
    api_spoil = {e["risk_level"]: e["observed_spoilage_rate"] for e in body["spoilage_rate_by_risk_level"]}
    for level in RISK_LEVELS_ORDER:
        assert abs(api_spoil[level] - float(spoil_by_level[level])) < 1e-9

    total_exposure = float(frozen_risk_df["expected_waste_exposure"].sum())
    assert abs(body["total_expected_waste_exposure"] - round(total_exposure, 2)) < 1e-6

    base_reduction = float(frozen_business_value.loc["Base", "Waste Reduction %"])
    assert abs(body["base_scenario_waste_reduction_pct"] - base_reduction) < 1e-9

    scope_counts = frozen_risk_df["intervention_scope"].value_counts()
    scope_summary = body["intervention_scope_summary"]
    assert scope_summary["batch_level"] == int(scope_counts.get("batch-level", 0))
    assert scope_summary["replenishment_only"] == int(
        scope_counts.get("replenishment-only (future batches)", 0)
    )
    assert scope_summary["none"] == int(scope_counts.get("none", 0))
