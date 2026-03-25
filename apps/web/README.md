# Web (Next.js)

Chat-style analyst UI.

## Environment

Required:
- `NEXT_PUBLIC_API_BASE_URL` (e.g. `https://<render-backend-domain>`)

Development fallback:
- If `NEXT_PUBLIC_API_BASE_URL` is unset and `NODE_ENV` is not `production`,
  the app defaults to `http://localhost:8000`.

