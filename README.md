# Taskify

**The one hub for everything a college student has to do — built for Vercel.**

Taskify pulls assignments out of Canvas, reads due dates out of syllabus PDFs with Gemini, mirrors them into Google Calendar, and keeps it all behind Google sign-in with per-user row-level security.

---

## Stack

- **Frontend** — Next.js 14 (App Router) + React + TypeScript + Tailwind CSS
- **Auth** — Supabase Auth (Google OAuth, PKCE flow, server-side cookies)
- **Database** — Supabase Postgres + RLS (`auth.uid() = user_id` on every table)
- **API** — FastAPI as a single Vercel Python serverless function under `/api/*`
- **Scheduled jobs** — Vercel Cron (daily Canvas re-sync)
- **LLM** — Google Gemini 2.5 Flash Lite (free tier) for syllabus parsing
- **PDF** — PyMuPDF
- **Hosting** — 100% on Vercel

---

## Project layout

```
.
├── app/                        # Next.js App Router
│   ├── layout.tsx
│   ├── globals.css             # Tailwind + macOS theme tokens
│   ├── page.tsx                # / → redirect
│   ├── login/page.tsx
│   ├── auth/callback/route.ts  # Supabase PKCE handler
│   ├── dashboard/page.tsx
│   └── settings/page.tsx
├── components/                 # React components (macOS-styled)
├── lib/
│   ├── supabase/{client,server}.ts
│   ├── types.ts
│   └── utils.ts
├── api/                        # Vercel Python serverless
│   ├── index.py                # FastAPI ASGI app — all /api/* routes
│   ├── canvas.py               # Canvas LMS routes
│   ├── syllabus.py             # PDF + Gemini parse
│   ├── calendar_routes.py      # Google Calendar
│   ├── assignments.py          # Assignment CRUD
│   └── deps.py                 # FastAPI auth dep (verifies Supabase JWT)
├── services/                   # Pure-Python integrations (Canvas, Gemini, GCal, crypto)
├── db/supabase.py              # Supabase Python client
├── supabase/schema.sql         # Postgres schema + RLS
├── vercel.json                 # Rewrites + crons + function config
├── tailwind.config.ts
├── next.config.mjs
├── package.json
└── requirements.txt
```

---

## Quick start (local dev)

```bash
# 1. Install both stacks
npm install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env.local
# Fill in Supabase + Gemini keys + a generated FERNET_KEY

# 3. Apply Supabase schema
# Open supabase/schema.sql in the Supabase SQL editor and Run.

# 4. Run frontend + Python API in two terminals
npm run dev
# in another terminal:
PYTHON_API_URL=http://localhost:8000 uvicorn api.index:app --reload --port 8000
```

The `PYTHON_API_URL` env triggers `next.config.mjs` to rewrite `/api/*` requests to the Python server during dev. In production on Vercel, `/api/*` is served by the serverless function directly — no rewrite needed.

---

## Deploy to Vercel

1. Push to GitHub.
2. Import the repo in Vercel.
3. Vercel → Settings → Environment Variables — paste every value from [`.env.example`](.env.example).
4. Vercel auto-detects Next.js + Python from the file structure. First build takes a few minutes.
5. After the first deploy, in Supabase → Authentication → URL Configuration, add `https://<your-vercel-domain>/auth/callback` to the Redirect URLs list.

That's it. Full runbook in [VERCEL.md](VERCEL.md).

---

## Database (5 tables, all RLS-protected)

| Table | Purpose |
| --- | --- |
| `profiles` | Mirrors `auth.users`, populated on first sign-in by the auth callback. |
| `courses` | Cached Canvas courses. |
| `assignments` | Canvas assignments + syllabus-extracted tasks. Has `status` (`todo` / `in_progress` / `done`). |
| `calendar_events` | Cached Google Calendar events. |
| `user_tokens` | Fernet-encrypted Canvas / Google refresh tokens. |

Every policy is `auth.uid() = user_id`. Schema: [`supabase/schema.sql`](supabase/schema.sql).

---

## Scheduled syncs

`vercel.json` registers a daily cron at 03:00 UTC that hits `/api/cron/sync-canvas`. The handler iterates every user with a saved Canvas token and re-pulls their courses + assignments. Cron requests are authenticated via the `CRON_SECRET` env var — Vercel sends it as `Authorization: Bearer <CRON_SECRET>` automatically.

To run more frequently than daily, you need a Vercel Pro plan (free tier is daily-only).

---

## Security

- **No passwords stored.** Auth is delegated to Google via Supabase.
- **Tokens encrypted at rest.** Canvas + Google refresh tokens are Fernet-encrypted before they touch the database.
- **RLS is the last line of defense.** Even if an API handler forgets to filter by user, Postgres refuses the row.
- **Service-role key is server-only.** Never shipped to the browser.

---

## License

MIT.
