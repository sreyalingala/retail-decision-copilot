from __future__ import annotations

import time
import re
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
    sql_to_execute, bound = _normalize_nullable_params(sql, bound)
    effective_max_rows = max_rows if max_rows is not None else settings.SQL_MAX_ROWS

    t0 = time.perf_counter()
    result: Result = session.execute(text(sql_to_execute), bound)
    execution_ms = int((time.perf_counter() - t0) * 1000)

    # `result.keys()` are column labels in the order returned by Postgres.
    columns = list(result.keys())
    rows = [list(r) for r in result.fetchall()]
    if effective_max_rows is not None and effective_max_rows > 0:
        rows = rows[:effective_max_rows]
    return {
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "metadata": {"row_count": len(rows), "execution_time_ms": execution_ms},
    }


def _normalize_nullable_params(
    sql: str, params: Dict[str, Any]
) -> tuple[str, Dict[str, Any]]:
    """
    Replace placeholders bound to None with SQL NULL literals.

    Why:
    psycopg/Postgres can raise AmbiguousParameter for patterns like:
      (:store_id IS NULL OR s.store_id = :store_id)
    when the parameter is None and appears in typed comparisons.

    This keeps query logic intact while avoiding ambiguous parameter typing.
    """
    if not params:
        return sql, params

    new_sql = sql
    new_params = dict(params)
    for key, value in list(new_params.items()):
        if value is None:
            # Replace :param_name with NULL (word boundary to avoid partial matches).
            new_sql = re.sub(rf":{re.escape(key)}\b", "NULL", new_sql)
            del new_params[key]

    return new_sql, new_params


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

