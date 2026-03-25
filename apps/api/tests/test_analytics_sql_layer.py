from unittest.mock import Mock

from app.services.analytics.analytics_service import (
    get_sql_for_analysis,
    run_analysis_sql,
    run_sql,
)


class FakeResult:
    def __init__(self, keys, rows):
        self._keys = keys
        self._rows = rows

    def keys(self):
        return self._keys

    def fetchall(self):
        return self._rows


def test_get_sql_for_analysis_includes_expected_patterns():
    sql = get_sql_for_analysis("month_over_month_revenue_change")
    assert "LAG" in sql
    assert "date_trunc('month'" in sql
    assert "FROM sales" in sql

    stock_sql = get_sql_for_analysis("stockout_risk_ranking")
    assert "COUNT(*) FILTER" in stock_sql
    assert "inventory_snapshots" in stock_sql
    assert "RANK() OVER" in stock_sql


def test_run_sql_returns_columns_rows_structure():
    session = Mock()
    session.execute.return_value = FakeResult(
        keys=["period_date", "net_revenue"],
        rows=[("2025-11-01", 12345.67), ("2025-11-02", 8901.23)],
    )

    sql = "SELECT :x AS period_date, 123 AS net_revenue"
    out = run_sql(session, sql, params={"x": "2025-11-01"})

    assert out["sql"] == sql
    assert out["columns"] == ["period_date", "net_revenue"]
    assert out["rows"] == [
        ["2025-11-01", 12345.67],
        ["2025-11-02", 8901.23],
    ]


def test_run_analysis_sql_adds_analysis_name():
    session = Mock()
    session.execute.return_value = FakeResult(
        keys=["store_name", "net_revenue"],
        rows=[("Store 1", 1000.0)],
    )

    out = run_analysis_sql(
        session,
        analysis_name="top_products",
        params={"start_date": "2025-11-01", "end_date": "2025-11-30", "top_n": 10},
    )

    assert out["analysis_name"] == "top_products"
    assert "sql" in out
    assert out["columns"] == ["store_name", "net_revenue"] or len(out["columns"]) == 2

