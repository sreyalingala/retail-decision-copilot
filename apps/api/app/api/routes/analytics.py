from datetime import date, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.analytics import (
    ListAnalysesResponse,
    RunAnalysisRequest,
    RunAnalysisResponse,
)
from app.api.schemas.analytics import AnalysisInfo, AnalysisParameterInfo
from app.db.session import get_db
from app.services.analytics.analytics_service import run_analysis_sql
from app.sql.analytics.registry import ANALYSIS_CATALOG

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _build_default_params(req_params: Dict[str, Any], *, end_default: date) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "start_date": (end_default - timedelta(days=60)).isoformat(),
        "end_date": end_default.isoformat(),
        "as_of_date": end_default.isoformat(),
        "region_id": None,
        "store_id": None,
        "category_id": None,
        "product_id": None,
        "supplier_id": None,
        "top_n": 10,
        "margin_threshold": 0.35,
        "volume_threshold": 100,
        "return_rate_threshold": 0.07,
    }
    defaults.update(req_params or {})
    return defaults


@router.get("", response_model=ListAnalysesResponse, summary="List available analytics analyses")
def list_analyses() -> ListAnalysesResponse:
    analyses = []
    for name in sorted(ANALYSIS_CATALOG.keys()):
        spec = ANALYSIS_CATALOG[name]
        analyses.append(
            AnalysisInfo(
                analysis_name=spec.analysis_name,
                short_description=spec.description,
                parameters=[
                    AnalysisParameterInfo(
                        name=p.name, required=p.required, description=p.description
                    )
                    for p in spec.parameters
                ],
            )
        )
    return ListAnalysesResponse(analyses=analyses)


@router.post(
    "/run",
    response_model=RunAnalysisResponse,
    summary="Run a supported analyst-grade SQL analysis",
)
def run_analysis(
    req: RunAnalysisRequest,
    db: Session = Depends(get_db),
) -> RunAnalysisResponse:
    if req.analysis_name not in ANALYSIS_CATALOG:
        allowed = sorted(ANALYSIS_CATALOG.keys())
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid analysis_name",
                "analysis_name": req.analysis_name,
                "allowed_analyses": allowed,
            },
        )

    end_d = date.today()
    default_params = _build_default_params(req.parameters, end_default=end_d)

    # Extra cap enforced by analytics_service (SQL_MAX_ROWS). Request can override via max_rows.
    out = run_analysis_sql(
        session=db,
        analysis_name=req.analysis_name,
        params=default_params,
        max_rows=req.max_rows,
    )

    return RunAnalysisResponse(
        analysis_name=out["analysis_name"],
        sql=out["sql"],
        columns=out["columns"],
        rows=out["rows"],
        metadata=out["metadata"],
    )

