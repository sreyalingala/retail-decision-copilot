# API (FastAPI)

Backend for Retail Decision Copilot.

Core endpoints:
- `GET /healthz`
- `GET /analytics`
- `POST /analytics/run`
- `POST /query` (AI-assisted routing to cataloged analyses)

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000}
```

## Seeding the retail dataset

After running Alembic migrations, seed deterministic synthetic data with:
- `make seed`

This uses `scripts/seed_db.py`, which calls the backend seed module in:
- `apps/api/app/db/seed_retail_analytics.py`

## Analytics API (SQL-first)

The backend exposes analyst-grade SQL analyses via:
- `GET /analytics` (lists supported analyses + expected parameters)
- `POST /analytics/run` (runs an analysis and returns `sql`, `columns`, `rows`, plus metadata)

This layer is deterministic and parameter-driven; SQL comes from the vetted catalog.

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


