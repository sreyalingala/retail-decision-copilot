from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)

    # Optional future context (timezone, filters, etc.)
    context: Optional[Dict[str, Any]] = None
    max_rows: Optional[int] = None


class QueryResponse(BaseModel):
    question: str
    sql: str
    rows: list[list[Any]]
    columns: list[str]
    business_explanation: str
    recommended_actions: list[str]
    status: str

