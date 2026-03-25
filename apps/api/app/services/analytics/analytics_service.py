from __future__ import annotations

import time
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session

from app.sql.analytics.queries import get_analysis_sql
from app.core.config import settings


def get_sql_for_analysis(analysis_name: str) -> str:
    return get_analysis_sql(analysis_name)


def run_sql(
    session: Session,
    sql: str,
    params: Optional[Dict[str, Any]] = None,
    max_rows: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Execute a SQL statement and return a portfolio-friendly structure:
    - sql: executed SQL text
    - columns: result column names
    - rows: row arrays
    """

    bound = params or {}
    effective_max_rows = max_rows if max_rows is not None else settings.SQL_MAX_ROWS

    # Apply a final row cap to keep responses frontend-friendly.
    # This wrapper is safe for PostgreSQL and keeps the underlying analysis SQL intact.
    if effective_max_rows is not None and effective_max_rows > 0:
        wrapped_sql = "SELECT * FROM (" + sql + ") AS t LIMIT :__max_rows"
        bound = {**bound, "__max_rows": effective_max_rows}
    else:
        wrapped_sql = sql

    t0 = time.perf_counter()
    result: Result = session.execute(text(wrapped_sql), bound)
    execution_ms = int((time.perf_counter() - t0) * 1000)

    # `result.keys()` are column labels in the order returned by Postgres.
    columns = list(result.keys())
    rows = [list(r) for r in result.fetchall()]
    return {
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "metadata": {"row_count": len(rows), "execution_time_ms": execution_ms},
    }


def run_analysis_sql(
    session: Session,
    analysis_name: str,
    params: Optional[Dict[str, Any]] = None,
    max_rows: Optional[int] = None,
) -> Dict[str, Any]:
    sql = get_sql_for_analysis(analysis_name)
    payload = run_sql(session, sql, params=params, max_rows=max_rows)
    payload["analysis_name"] = analysis_name
    return payload

