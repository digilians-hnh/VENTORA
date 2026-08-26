from backend_api.core import data_access
from backend_api.tests.scoring_fixtures import load_demo_records


def test_frozen_hashes_unchanged_after_scoring_calls(client):
    before = data_access.verify_frozen_hashes()

    batches, demand = load_demo_records()
    client.post("/api/score", json={"batches": batches, "category_demand": demand})
    client.post("/api/score/demo")

    after = data_access.verify_frozen_hashes()
    assert before == after
