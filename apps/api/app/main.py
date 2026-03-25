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


def parse_cors_origins(frontend_url: str, cors_origins: str) -> list[str]:
    # Support:
    # - FRONTEND_URL as single or comma-separated values
    # - CORS_ORIGINS as explicit override/additional values
    origins: list[str] = []

    def add_many(raw: str) -> None:
        for u in raw.split(","):
            u = u.strip()
            if u and u not in origins:
                origins.append(u)

    if frontend_url.strip():
        add_many(frontend_url)
    if cors_origins.strip():
        add_many(cors_origins)

    # Keep local dev comfortable even when only production URL is configured.
    local_defaults = ["http://localhost:3000", "http://127.0.0.1:3000"]
    for u in local_defaults:
        if u not in origins:
            origins.append(u)

    return origins


app = FastAPI(
    title="Retail Decision Copilot API",
    description="SQL-first retail analytics assistant backend (guardrails + NL->SQL in later phases).",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)

origins = parse_cors_origins(settings.FRONTEND_URL, settings.CORS_ORIGINS)
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

