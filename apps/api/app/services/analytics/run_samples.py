"""
Lightweight local runner for a few analytics queries.

Usage (example):
  cd apps/api
  ./.venv/bin/python -m app.services.analytics.run_samples

This is intentionally simple for portfolio/demo use and does not replace tests.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.analytics.analytics_service import run_analysis_sql


def _default_date_window() -> Dict[str, Any]:
    # Uses a recent window relative to today.
    end = date.today()
    start = end - timedelta(days=60)
    return {"start_date": start, "end_date": end, "top_n": 10, "as_of_date": end}


def run() -> None:
    params = _default_date_window()

    session = SessionLocal()
    try:
        analyses: List[str] = [
            "revenue_by_month",
            "stockout_risk_ranking",
            "promotion_effectiveness",
        ]
        for name in analyses:
            out = run_analysis_sql(session, name, params=params)
            cols = ", ".join(out["columns"][:6])
            print(f"\n=== {name} ===")
            print(f"Columns: {cols} ...")
            print(f"Rows returned: {len(out['rows'])}")
    finally:
        session.close()


if __name__ == "__main__":
    run()

