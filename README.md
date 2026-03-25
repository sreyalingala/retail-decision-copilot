# Retail Decision Copilot

SQL-first, AI-powered retail analytics assistant for business analysts.

## What it does
- Users ask questions in natural language
- The backend generates **safe, read-only SQL** (SELECT-only)
- The system runs SQL on PostgreSQL and returns:
  - the SQL
  - the result
  - a business explanation
  - recommended actions

## Repo structure
- `apps/web`: Next.js chat UI (frontend)
- `apps/api`: FastAPI backend (SQL generation + execution)
- `packages/shared`: shared types/contracts
- `infra/`: local/dev and deployment docs
- `scripts/`: database setup and seed scripts

## Setup
See `infra/deploy/render/README.md` and `infra/deploy/vercel/README.md` for deployment notes.

