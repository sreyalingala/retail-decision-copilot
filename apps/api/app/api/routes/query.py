from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas.query import QueryRequest, QueryResponse
from app.api.schemas.health import HealthResponse
from app.db.session import get_db
from app.services.query_service import run_query_placeholder

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    # `db` is currently unused for placeholder logic, but it wires in the future
    # safe SQL execution layer.
    _ = db
    return run_query_placeholder(req)

