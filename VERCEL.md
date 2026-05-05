# Deploying Taskify to Vercel

Taskify is built for Vercel end-to-end:

- **Frontend** — Next.js 14 (App Router) → Vercel's Next.js runtime
- **API** — FastAPI ASGI app at `api/index.py` → Vercel Python serverless
- **Cron** — `vercel.json` registers `/api/cron/sync-canvas` daily

No second host. No WebSocket worker. Just Vercel.

---

## Prerequisites

- A **Supabase** project (free tier works) — [supabase.com](https://supabase.com)
- A **Google Cloud** OAuth client (Web app) with `https://<your-supabase-ref>.supabase.co/auth/v1/callback` in the redirect URIs
- A **Gemini** API key — [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- A **Vercel** account

---

## 1. Apply the Supabase schema

Open [`supabase/schema.sql`](supabase/schema.sql) in the Supabase SQL editor and Run. Five tables are created with RLS enabled.

## 2. Enable Google in Supabase Auth

- **Authentication → Providers → Google**: enable, paste your Google Client ID + Secret
- **Scopes**: `openid email profile https://www.googleapis.com/auth/calendar`
- **Authentication → URL Configuration → Redirect URLs**: add
  - `http://localhost:3000/auth/callback` (dev)
  - `https://<your-vercel-domain>/auth/callback` (prod — fill in after step 4)

## 3. Push the repo to GitHub

Standard `git push origin main`.

## 4. Import in Vercel

1. Vercel dashboard → Add New → Project → import your repo.
2. Vercel auto-detects Next.js. **Don't change the build command.**
3. **Settings → Environment Variables** — add every value from [`.env.example`](.env.example):

   | Name | Source |
   | --- | --- |
   | `NEXT_PUBLIC_SUPABASE_URL` | Supabase → Project Settings → API |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase → Project Settings → API |
   | `SUPABASE_URL` | (same) |
   | `SUPABASE_ANON_KEY` | (same) |
   | `SUPABASE_SERVICE_KEY` | Supabase → Project Settings → API → `service_role` |
   | `FERNET_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
   | `GEMINI_API_KEY` | aistudio.google.com |
   | `GEMINI_MODEL` | `gemini-2.5-flash-lite` |
   | `CRON_SECRET` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |

4. Hit **Deploy**. First build takes a few minutes (Next.js + Python wheels).
5. After it lands, copy your Vercel domain back into Supabase → URL Configuration → Redirect URLs.

## 5. Verify

- Hit `https://<your-vercel-domain>/api/health` → should return `{"ok": true}`
- Hit `https://<your-vercel-domain>` → redirects to `/login`
- Sign in with Google → land on `/dashboard`
- Settings → paste a Canvas token → Save & validate → Sync

If anything fails, Vercel → Logs (top of the project page) shows both Next.js and Python serverless logs.

---

## How the routing works

```
Browser
  │
  │  GET /api/canvas/sync
  ▼
Vercel edge
  │  vercel.json rewrite: /api/:path* → /api/index
  ▼
api/index.py  (FastAPI ASGI app)
  │  router matches /api/canvas/sync
  ▼
api/canvas.py::sync_canvas()
```

Vercel's Python runtime auto-detects an ASGI `app` at the top level of `api/index.py` and routes traffic to it. The rewrite means a single function handles every `/api/*` route — simpler cold starts, simpler bundle, and FastAPI does internal routing.

## Cron

`vercel.json` includes:

```json
"crons": [
  { "path": "/api/cron/sync-canvas", "schedule": "0 3 * * *" }
]
```

Daily at 03:00 UTC, Vercel sends `GET /api/cron/sync-canvas` with `Authorization: Bearer <CRON_SECRET>`. The handler verifies the secret, reads every saved Canvas token, and runs sync for each user concurrently.

> Vercel's free plan is **daily cron only**. For hourly or 6-hour cadence, upgrade to Pro and change the schedule expression.

## Troubleshooting

- **Build fails on Python deps** — Vercel Python uses pip with a 250MB unzipped function size limit. The current `requirements.txt` fits comfortably (~120MB). If you add packages, watch the limit.
- **Cold starts feel slow** — first hit after idle is slow because it has to spin up the Python runtime. Subsequent calls are fast.
- **Auth redirect loops** — check that the Vercel domain is in Supabase's Redirect URLs *and* that `NEXT_PUBLIC_SUPABASE_URL` matches your Supabase project.
- **Sync 401s** — the JWT cookie is only sent to same-origin requests. If you split frontend/backend onto different domains, you'll need to forward `Authorization` headers explicitly.
