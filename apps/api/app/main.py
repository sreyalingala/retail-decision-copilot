from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel


app = FastAPI(title="Retail Decision Copilot API")


class QueryRequest(BaseModel):
    question: str
    context: dict | None = None
    max_rows: int | None = None


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/query")
def query(req: QueryRequest):
    # Placeholder contract:
    # - Generate safe SELECT-only SQL
    # - Execute against Postgres (read-only)
    # - Return { sql, result, business_explanation, recommended_actions }
    return JSONResponse(
        status_code=501,
        content={"error": "Not implemented yet. Implement NL->SQL generation and safe execution."},
    )

