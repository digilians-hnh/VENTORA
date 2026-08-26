from backend_api.core.scoring_schema import (
    CATEGORY_VALUES,
    FOOD_CATEGORY_VALUES,
    RAW_BATCH_FEATURES,
    RAW_CATEGORY_DEMAND_FEATURES,
    WEEKDAY_VALUES,
)


def test_input_schema_ok(client):
    resp = client.get("/api/input-schema")
    assert resp.status_code == 200
    body = resp.json()

    batch_field_names = {f["name"] for f in body["batch_fields"]}
    demand_field_names = {f["name"] for f in body["category_demand_fields"]}

    for f in RAW_BATCH_FEATURES:
        assert f in batch_field_names
    for f in RAW_CATEGORY_DEMAND_FEATURES:
        assert f in demand_field_names

    category_field = next(f for f in body["batch_fields"] if f["name"] == "category")
    assert category_field["allowed_values"] == CATEGORY_VALUES

    food_category_field = next(f for f in body["batch_fields"] if f["name"] == "food_category")
    assert set(food_category_field["allowed_values"]) == set(FOOD_CATEGORY_VALUES)

    weekday_field = next(f for f in body["batch_fields"] if f["name"] == "weekday_received")
    assert set(weekday_field["allowed_values"]) == set(WEEKDAY_VALUES)

    assert len(body["notes"]) > 0
