from app.api.schemas.query import QueryResponse, QueryRequest


def run_query_placeholder(req: QueryRequest) -> QueryResponse:
    # Placeholder contract:
    # - No NL->SQL generation yet
    # - No DB execution yet
    return QueryResponse(
        question=req.question,
        sql="SELECT 1 AS placeholder",
        rows=[[1]],
        columns=["placeholder"],
        business_explanation="Placeholder: implement NL->SQL generation with strict SELECT-only guardrails.",
        recommended_actions=[],
        status="placeholder",
    )

