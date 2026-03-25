import os
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client() -> TestClient:
    # Ensure deterministic settings during tests.
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/retail_decision_copilot_test",
    )

    # Ensure `apps/api` is on sys.path so `import app.*` works reliably under pytest.
    api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if api_root not in sys.path:
        sys.path.insert(0, api_root)

    # Import after setting env vars so Settings picks them up.
    from app.main import app

    with TestClient(app) as c:
        yield c

