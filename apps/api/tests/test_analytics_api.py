from fastapi.testclient import TestClient
from unittest.mock import Mock

from app.db.session import get_db
from app.main import app


class FakeResult:
    def __init__(self, keys, rows):
        self._keys = keys
        self._rows = rows

    def keys(self):
        return self._keys

    def fetchall(self):
        return self._rows


def test_list_analytics_returns_catalog():
    with TestClient(app) as client:
        resp = client.get("/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert "analyses" in data
        assert isinstance(data["analyses"], list)
        assert any(a["analysis_name"] == "revenue_by_month" for a in data["analyses"])


def test_run_valid_analysis_returns_sql_and_rows():
    mock_session = Mock()
    mock_session.execute.return_value = FakeResult(
        keys=["period_date", "net_revenue"],
        rows=[("2025-11-01", 12345.67)],
    )

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/analytics/run",
                json={
                    "analysis_name": "revenue_by_month",
                    "parameters": {
                        "start_date": "2025-11-01",
                        "end_date": "2025-11-30",
                        "region_id": None,
                        "store_id": None,
                        "category_id": None,
                    },
                    "max_rows": 10,
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["analysis_name"] == "revenue_by_month"
            assert isinstance(data["sql"], str)
            assert data["columns"] == ["period_date", "net_revenue"]
            assert data["rows"] == [["2025-11-01", 12345.67]]
            assert data["metadata"]["row_count"] == 1
            assert "execution_time_ms" in data["metadata"]
    finally:
        app.dependency_overrides.clear()


def test_run_invalid_analysis_rejects_name():
    mock_session = Mock()

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/analytics/run",
                json={"analysis_name": "not_a_real_analysis", "parameters": {}},
            )
            assert resp.status_code == 400
            data = resp.json()
            assert data["detail"]["error"] == "Invalid analysis_name"
            assert "allowed_analyses" in data["detail"]
    finally:
        app.dependency_overrides.clear()

