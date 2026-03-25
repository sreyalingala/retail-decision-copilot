from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.ai.client import AnalysisRouteAIOutput
from app.api.schemas.query import QueryResponse
from app.services.analytics.analytics_service import run_analysis_sql


class FakeResult:
    def __init__(self, keys, rows):
        self._keys = keys
        self._rows = rows

    def keys(self):
        return self._keys

    def fetchall(self):
        return self._rows


def _mock_analytics_run():
    return {
        "analysis_name": "revenue_by_month",
        "sql": "SELECT date_trunc('month', sale_date)::date AS period_date, SUM(net_revenue) AS net_revenue FROM sales WHERE sale_date BETWEEN :start_date AND :end_date GROUP BY 1 ORDER BY 1;",
        "columns": ["period_date", "net_revenue"],
        "rows": [["2025-11-01", 12345.67]],
        "metadata": {"row_count": 1, "execution_time_ms": 12},
    }


def test_query_ai_routed_valid_flow(client: TestClient):
    routing_output = AnalysisRouteAIOutput(
        analysis_name="revenue_by_month",
        parameters={
            "start_date": "2025-11-01",
            "end_date": "2025-11-30",
            "region_id": None,
            "store_id": None,
            "category_id": None,
        },
        reasoning_short="Revenue trend question maps to monthly revenue.",
    )

    with patch(
        "app.ai.router.OpenAIRoutingClient.select_analysis",
        return_value=routing_output,
    ), patch(
        "app.services.query_service.run_analysis_sql",
        return_value=_mock_analytics_run(),
    ):
        payload = {"question": "Show revenue trend by month for Nov 2025"}
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["question"] == payload["question"]
        assert data["selected_analysis_name"] == "revenue_by_month"
        assert isinstance(data["selected_parameters"], dict)
        assert "reasoning_short" in data
        assert isinstance(data["sql"], str)
        assert data["columns"] == ["period_date", "net_revenue"]
        assert data["rows"] == [["2025-11-01", 12345.67]]
        assert isinstance(data["business_explanation"], str)
        assert isinstance(data["recommended_actions"], list)
        assert data["status"] == "ok" or data["status"] == "fallback"


def test_query_ai_invalid_output_fallback(client: TestClient):
    # Invalid start_date causes router to fallback.
    routing_output = AnalysisRouteAIOutput(
        analysis_name="revenue_by_month",
        parameters={
            "start_date": "not-a-date",
            "end_date": "2025-11-30",
            "unknown_param": "should be removed",
        },
        reasoning_short="Bad parameters test.",
    )

    with patch(
        "app.ai.router.OpenAIRoutingClient.select_analysis",
        return_value=routing_output,
    ), patch(
        "app.services.query_service.run_analysis_sql",
        return_value=_mock_analytics_run(),
    ):
        payload = {"question": "Revenue by month (invalid params case)"}
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["selected_analysis_name"] == "revenue_by_month"
        assert data["status"] == "fallback"
        assert "unknown_param" not in data["selected_parameters"]
        assert "business_explanation" in data


def test_query_ai_unsupported_analysis_name_fallback(client: TestClient):
    routing_output = AnalysisRouteAIOutput(
        analysis_name="not_in_catalog",
        parameters={},
        reasoning_short="Should be rejected by catalog validation.",
    )

    with patch(
        "app.ai.router.OpenAIRoutingClient.select_analysis",
        return_value=routing_output,
    ), patch(
        "app.services.query_service.run_analysis_sql",
        return_value=_mock_analytics_run(),
    ):
        payload = {"question": "Try something unsupported analysis"}
        resp = client.post("/query", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["selected_analysis_name"] == "revenue_by_month"
        assert data["status"] == "fallback"

