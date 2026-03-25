from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional


class Settings(BaseSettings):
    # Environment
    APP_ENV: str = "development"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    PORT: Optional[int] = None

    # Database
    # Use psycopg v3 driver explicitly for SQLAlchemy.
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/retail_decision_copilot"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    # SQL execution limits (portfolio safety guardrail; full guardrails later)
    SQL_MAX_ROWS: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def apply_port_fallback(self):
        # Render provides PORT; prefer it when present.
        if self.PORT:
            self.API_PORT = self.PORT
        return self


settings = Settings()

