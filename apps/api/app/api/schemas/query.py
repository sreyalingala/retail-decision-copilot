from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    # No other fields for now (AI routing picks a supported analysis + parameters).


class QueryResponse(BaseModel):
    question: str
    selected_analysis_name: str
    selected_parameters: Dict[str, Any]
    reasoning_short: str

    sql: str
    columns: List[str]
    rows: List[List[Any]]
    metadata: Dict[str, Any]
    business_explanation: str
    recommended_actions: List[str]
    status: str

