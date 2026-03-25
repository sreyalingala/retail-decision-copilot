from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import run_ai_routed_query

router = APIRouter(tags=["query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Ask a natural-language question and route to a cataloged SQL analysis",
)
def query(req: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="question must not be empty")

    return run_ai_routed_query(req=req, db=db)

