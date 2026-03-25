# Retail Decision Copilot

Retail Decision Copilot is a SQL-first, AI-assisted retail analytics app built for analyst and business analyst portfolio review.

## Product positioning
- SQL-first transparency: every answer shows the exact SQL and result rows.
- AI-assisted routing: natural-language questions map to vetted analytics analyses (not arbitrary SQL generation).
- Business-facing outputs: includes business explanation and recommended actions.
- Production-style architecture: Next.js frontend + FastAPI backend + PostgreSQL.

## Current capabilities
- Manual analytics mode:
  - List supported analyses (`GET /analytics`)
  - Run analysis with parameters (`POST /analytics/run`)
- AI question mode:
  - Ask a natural-language question (`POST /query`)
  - Backend selects analysis + parameters from catalog and returns:
    - selected analysis/parameters
    - routing reasoning
    - SQL, columns, rows, metadata
    - business explanation
    - recommended actions

## Monorepo structure
- `apps/web` - Next.js App Router frontend
- `apps/api` - FastAPI backend (analytics SQL + AI routing layer)
- `packages/shared` - shared types/contracts
- `infra/deploy` - Render/Vercel deployment docs
- `infra/docker` - local docker compose baseline
- `scripts` - helper scripts (seed/init/wait)

## Local development

### 1) Backend
```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
cd ../..
make seed
npm run dev -w @rdc/api
```

### 2) Frontend
```bash
npm install
npm run dev -w @rdc/web
```

Set env vars from `.env.example` (especially `NEXT_PUBLIC_API_BASE_URL`).

## Deployment
- Backend (Render): see `infra/deploy/render/README.md`
- Frontend (Vercel): see `infra/deploy/vercel/README.md`
- Database (Neon): use a Postgres connection string in `DATABASE_URL` with `sslmode=require`

Health check path for backend:
- `GET /healthz`

### Recommended deployment order
1. Provision Neon database and set backend `DATABASE_URL`.
2. Deploy backend to Render.
3. Run backend migration:
   - `alembic upgrade head`
4. (Optional demo data) seed dataset:
   - `python scripts/seed_db.py`
5. Deploy frontend to Vercel with `NEXT_PUBLIC_API_BASE_URL` pointing to Render backend.

## Production env vars

### Backend (`apps/api`)
- `APP_ENV`
- `API_HOST`
- `PORT` (Render) or `API_PORT`
- `FRONTEND_URL`
- `CORS_ORIGINS` (optional additional origins)
- `DATABASE_URL` (Neon/PG, e.g. `postgresql+psycopg://...?...sslmode=require`)
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `LOG_LEVEL`
- `SQL_MAX_ROWS` (optional)

### Frontend (`apps/web`)
- `NEXT_PUBLIC_API_BASE_URL` (required in production)

