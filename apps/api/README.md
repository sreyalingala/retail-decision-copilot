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


