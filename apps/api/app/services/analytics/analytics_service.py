from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session

from app.sql.analytics.queries import get_analysis_sql


def get_sql_for_analysis(analysis_name: str) -> str:
    return get_analysis_sql(analysis_name)


def run_sql(
    session: Session,
    sql: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a SQL statement and return a portfolio-friendly structure:
    - sql: executed SQL text
    - columns: result column names
    - rows: row arrays
    """

    bound = params or {}
    result: Result = session.execute(text(sql), bound)

    # `result.keys()` are column labels in the order returned by Postgres.
    columns = list(result.keys())
    rows = [list(r) for r in result.fetchall()]
    return {"sql": sql, "columns": columns, "rows": rows}


def run_analysis_sql(
    session: Session,
    analysis_name: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    sql = get_sql_for_analysis(analysis_name)
    payload = run_sql(session, sql, params=params)
    payload["analysis_name"] = analysis_name
    return payload

