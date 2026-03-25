#!/usr/bin/env bash
set -euo pipefail

echo "Applying migrations..."
cd "$(dirname "$0")/../apps/api"

if [[ -x ".venv/bin/alembic" ]]; then
  .venv/bin/alembic upgrade head
else
  alembic upgrade head
fi

echo "Seeding dataset..."
cd ../..
python3 scripts/seed_db.py

echo "Database initialization complete."

