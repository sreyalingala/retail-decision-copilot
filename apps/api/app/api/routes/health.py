from fastapi import APIRouter

from app.api.schemas.health import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(status="healthy", app_env=settings.APP_ENV)

