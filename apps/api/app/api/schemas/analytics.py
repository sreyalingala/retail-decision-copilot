from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisParameterInfo(BaseModel):
    name: str
    required: bool = False
    description: str


class AnalysisInfo(BaseModel):
    analysis_name: str
    short_description: str
    parameters: List[AnalysisParameterInfo] = []


class ListAnalysesResponse(BaseModel):
    analyses: List[AnalysisInfo]


class RunAnalysisRequest(BaseModel):
    analysis_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    max_rows: Optional[int] = None


class RunAnalysisResponse(BaseModel):
    analysis_name: str
    sql: str
    columns: List[str]
    rows: List[List[Any]]
    metadata: Dict[str, Any]

