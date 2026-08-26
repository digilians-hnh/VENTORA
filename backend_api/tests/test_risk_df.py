import math


def test_risk_df_default_is_paginated_not_full_dump(client, frozen_risk_df):
    resp = client.get("/api/risk-df")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_rows"] == len(frozen_risk_df)
    assert body["page"] == 1
    assert body["page_size"] == 50
    assert len(body["rows"]) == 50
    assert len(body["rows"]) < body["total_rows"]


def test_risk_df_pagination_math(client, frozen_risk_df):
    resp = client.get("/api/risk-df", params={"page_size": 1000, "page": 1})
    body = resp.json()
    expected_total_pages = math.ceil(len(frozen_risk_df) / 1000)
    assert body["total_pages"] == expected_total_pages
    assert body["total_rows"] == len(frozen_risk_df)


def test_risk_df_filter_by_risk_level(client, frozen_risk_df):
    resp = client.get("/api/risk-df", params={"risk_level": "CRITICAL", "page_size": 1000})
    body = resp.json()
    expected_count = int((frozen_risk_df["risk_level"] == "CRITICAL").sum())
    assert body["total_rows"] == expected_count
    assert all(row["risk_level"] == "CRITICAL" for row in body["rows"])


def test_risk_df_filter_by_multiple_risk_levels(client, frozen_risk_df):
    resp = client.get("/api/risk-df", params={"risk_level": ["HIGH", "CRITICAL"], "page_size": 1000})
    body = resp.json()
    expected_count = int(frozen_risk_df["risk_level"].isin(["HIGH", "CRITICAL"]).sum())
    assert body["total_rows"] == expected_count


def test_risk_df_filter_by_category(client, frozen_risk_df):
    sample_category = frozen_risk_df["category"].iloc[0]
    resp = client.get("/api/risk-df", params={"category": sample_category, "page_size": 1000})
    body = resp.json()
    expected_count = int((frozen_risk_df["category"] == sample_category).sum())
    assert body["total_rows"] == expected_count
    assert all(row["category"] == sample_category for row in body["rows"])


def test_risk_df_filter_by_days_to_expiry_range(client, frozen_risk_df):
    resp = client.get(
        "/api/risk-df",
        params={"min_days_to_expiry": 0, "max_days_to_expiry": 5, "page_size": 1000},
    )
    body = resp.json()
    expected = frozen_risk_df[
        (frozen_risk_df["days_until_expiry"] >= 0) & (frozen_risk_df["days_until_expiry"] <= 5)
    ]
    assert body["total_rows"] == len(expected)
    assert all(0 <= row["days_until_expiry"] <= 5 for row in body["rows"])


def test_risk_df_filter_by_min_excess(client, frozen_risk_df):
    resp = client.get("/api/risk-df", params={"min_excess": 10, "page_size": 1000})
    body = resp.json()
    expected = frozen_risk_df[frozen_risk_df["potential_excess_inventory"] >= 10]
    assert body["total_rows"] == len(expected)


def test_risk_df_invalid_risk_level_returns_400(client):
    resp = client.get("/api/risk-df", params={"risk_level": "NOT_A_LEVEL"})
    assert resp.status_code == 400


def test_risk_df_page_beyond_range_returns_404(client, frozen_risk_df):
    resp = client.get("/api/risk-df", params={"page": 999999, "page_size": 50})
    assert resp.status_code == 404
