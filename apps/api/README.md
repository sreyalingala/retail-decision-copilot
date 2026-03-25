# API (FastAPI)

Next steps:
- Implement `POST /query` with OpenAI SQL generation + strict SELECT-only guardrails
- Add SQL validation (AST parsing) and allowlisted schema
- Add Alembic migrations + seed data

## Seeding the retail dataset

After running Alembic migrations, seed deterministic synthetic data with:
- `make seed`

This uses `scripts/seed_db.py`, which calls the backend seed module in:
- `apps/api/app/db/seed_retail_analytics.py`

## Analytics API (SQL-first)

The backend exposes analyst-grade SQL analyses via:
- `GET /analytics` (lists supported analyses + expected parameters)
- `POST /analytics/run` (runs an analysis and returns `sql`, `columns`, `rows`, plus metadata)

This is parameter-driven only for now (no AI / no NL-to-SQL yet). Later phases will use AI to choose `analysis_name` and parameters.

## AI Routing Layer (safe catalog selection)

The backend now supports an initial AI routing layer via:
- `POST /query`

Behavior today:
- The model selects an `analysis_name` and `parameters` from the supported analytics catalog.
- It does NOT generate arbitrary SQL.
- The selected analysis is executed through the existing SQL analytics layer.

Future phases will extend this toward stricter NL-to-SQL guardrails, but the system remains SQL-first and SELECT-only.

## Production env vars

Minimum backend env vars for deployment:
- `APP_ENV` (e.g. `production`)
- `API_HOST` (recommend `0.0.0.0`)
- `PORT` (provided by Render) or `API_PORT`
- `FRONTEND_URL` (comma-separated supported)
- `CORS_ORIGINS` (optional additional origins)
- `DATABASE_URL` (Neon/PG, e.g. `postgresql+psycopg://...?...sslmode=require`)
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `LOG_LEVEL`

Example startup command (non-Docker):
- `python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`


