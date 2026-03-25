#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for Postgres to become available..."
echo "Tip: for local Docker, run: docker compose -f infra/docker/docker-compose.yml up -d"
echo "Then use /healthz and alembic upgrade head to validate readiness."

