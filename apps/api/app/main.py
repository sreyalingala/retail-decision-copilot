import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.routes.query import router as query_router
from app.api.routes.analytics import router as analytics_router
from app.core.config import settings
from app.core.logging import setup_logging


setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("rdc.api")


def parse_cors_origins(frontend_url: str) -> list[str]:
    # Allow either a single URL or a comma-separated list.
    if not frontend_url.strip():
        return []
    return [u.strip() for u in frontend_url.split(",") if u.strip()]


app = FastAPI(
    title="Retail Decision Copilot API",
    description="SQL-first retail analytics assistant backend (guardrails + NL->SQL in later phases).",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

origins = parse_cors_origins(settings.FRONTEND_URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(query_router)
app.include_router(analytics_router)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Request validation failed", extra={"errors": exc.errors()})
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Invalid request payload."},
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception", extra={"error": str(exc)})
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error."},
    )

