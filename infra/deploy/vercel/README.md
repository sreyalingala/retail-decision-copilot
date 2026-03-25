# Vercel Deployment (Frontend)

Deploy `apps/web` as a Next.js project on Vercel.

## Project settings
- **Framework Preset**: Next.js
- **Root Directory**: `apps/web`

## Required environment variables
- `NEXT_PUBLIC_API_BASE_URL=https://<your-render-backend-domain>`

## Notes
- In production, the frontend requires `NEXT_PUBLIC_API_BASE_URL` (no localhost fallback).
- Re-deploy after setting/changing environment variables.

