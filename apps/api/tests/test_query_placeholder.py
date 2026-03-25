from collections.abc import Mapping


def test_query_placeholder_returns_contract(client):
    payload = {"question": "Top categories by margin this month"}
    resp = client.post("/query", json=payload)

    assert resp.status_code == 200
    data = resp.json()

    # Required response keys for the portfolio contract.
    assert data["status"] == "placeholder"
    assert data["question"] == payload["question"]
    assert isinstance(data["sql"], str)
    assert isinstance(data["columns"], list)
    assert isinstance(data["rows"], list)
    assert isinstance(data["business_explanation"], str)
    assert isinstance(data["recommended_actions"], list)

    # Basic shape sanity.
    assert len(data["columns"]) >= 1
    assert len(data["rows"]) >= 1

