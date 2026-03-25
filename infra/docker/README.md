# Local Development (Docker)

The current compose file provides a local PostgreSQL service for development.

Use it with:
```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

Then run backend/frontend from the monorepo workspace:
- backend: `npm run dev -w @rdc/api`
- frontend: `npm run dev -w @rdc/web`

