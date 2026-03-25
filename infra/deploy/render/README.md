# Render Deployment (Backend)

Deploy `apps/api` as a Docker Web Service on Render.

## Service settings
- **Root Directory**: `apps/api`
- **Environment**: `Docker`
- **Dockerfile Path**: `Dockerfile`
- **Health Check Path**: `/healthz`

The container starts with:
- host: `0.0.0.0`
- port: `PORT` (Render-provided) or `API_PORT` fallback

## Required environment variables
- `APP_ENV=production`
- `API_HOST=0.0.0.0`
- `LOG_LEVEL=INFO`
- `FRONTEND_URL=https://<your-vercel-domain>`
- `CORS_ORIGINS=https://<your-vercel-domain>`
- `DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require`
- `OPENAI_API_KEY=<secret>`
- `OPENAI_MODEL=gpt-4.1-mini` (or your chosen model)

## Optional environment variables
- `SQL_MAX_ROWS=200`
- `DATABASE_READONLY_URL=<optional-readonly-connection-string>`
- `API_PORT=8000` (typically unnecessary on Render because `PORT` is injected)

## Notes
- Neon typically requires TLS; include `?sslmode=require` in `DATABASE_URL`.
- `/healthz` is lightweight and suitable for Render health checks.

## Migrations and seed

Run once after first deploy (or after schema changes):
- `alembic upgrade head`

Seed data (optional for demos):
- `python ../../scripts/seed_db.py`

If you use Render jobs/shell, run these from `apps/api` context with env vars loaded.

