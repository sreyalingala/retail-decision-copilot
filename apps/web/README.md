# Web (Next.js)

Business-facing analyst workspace with two modes:
- AI Question mode (`POST /query`)
- Manual Analysis mode (`GET /analytics`, `POST /analytics/run`)

## Environment

Required:
- `NEXT_PUBLIC_API_BASE_URL` (e.g. `https://<render-backend-domain>`)

Development fallback:
- If `NEXT_PUBLIC_API_BASE_URL` is unset and `NODE_ENV` is not `production`,
  the app defaults to `http://localhost:8000`.

