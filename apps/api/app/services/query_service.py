from __future__ import annotations

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.ai.router import route_question_to_analysis
from app.api.schemas.query import QueryRequest, QueryResponse
from app.services.analytics.analytics_service import run_analysis_sql
from app.services.query_explanation_service import (
    generate_business_explanation_and_actions,
)

logger = logging.getLogger("rdc.api.ai")


def run_ai_routed_query(req: QueryRequest, db: Session) -> QueryResponse:
    routing = route_question_to_analysis(req.question)

    selected_analysis_name = routing["analysis_name"]
    selected_parameters = routing["parameters"]
    reasoning_short = routing["reasoning_short"]
    status = routing["status"]

    # Observability: log routing decision without secrets.
    logger.info(
        "ai_routed_query %s",
        {
            "analysis_name": selected_analysis_name,
            "status": status,
            "parameters": selected_parameters,
        },
    )

    try:
        executed = run_analysis_sql(
            session=db,
            analysis_name=selected_analysis_name,
            params=selected_parameters,
        )
    except Exception as exc:
        # Hard fallback: keep response format stable even if DB execution fails.
        status = "error"
        return QueryResponse(
            question=req.question,
            selected_analysis_name=selected_analysis_name,
            selected_parameters=selected_parameters,
            reasoning_short=reasoning_short,
            sql="",
            columns=[],
            rows=[],
            metadata={"row_count": 0, "execution_time_ms": 0, "error": str(exc)},
            business_explanation="The analysis could not be executed.",
            recommended_actions=["Check backend logs and ensure your database is reachable."],
            status=status,
        )

    business_explanation, recommended_actions = (
        generate_business_explanation_and_actions(
            question=req.question,
            selected_analysis_name=selected_analysis_name,
            selected_parameters=selected_parameters,
            columns=executed["columns"],
            rows=executed["rows"],
        )
    )

    return QueryResponse(
        question=req.question,
        selected_analysis_name=selected_analysis_name,
        selected_parameters=selected_parameters,
        reasoning_short=reasoning_short,
        sql=executed["sql"],
        columns=executed["columns"],
        rows=executed["rows"],
        metadata=executed["metadata"],
        business_explanation=business_explanation,
        recommended_actions=recommended_actions,
        status=status,
    )

