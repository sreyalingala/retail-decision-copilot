from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment
    APP_ENV: str = "development"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database
    # Use psycopg v3 driver explicitly for SQLAlchemy.
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/retail_decision_copilot"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()

