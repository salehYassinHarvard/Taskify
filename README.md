# Taskify

**The one hub for everything a college student has to do.**

Taskify pulls assignments out of Canvas, reads due dates out of syllabus PDFs with Gemini, pushes them into Google Calendar, and keeps it all behind Google sign-in with per-user row-level security.

---

## Why

The average student juggles Canvas, three different professor websites, a couple of Google Docs syllabi, and a calendar app. Due dates fall through the cracks. Taskify is a single dashboard that *actually* knows what you owe and when.

---

## Features

| | |
| --- | --- |
| **Google sign-in** | Supabase-managed OAuth. No passwords to remember or leak. |
| **Canvas sync** | Paste your personal access token once; every course + assignment is pulled in and auto-refreshed every 6 hours. |
| **Syllabus PDF parser** | Upload a syllabus. Google Gemini (2.5 Flash Lite, free tier) extracts assignments, due dates, and point values as strict JSON. |
| **Google Calendar push** | Every assignment becomes a calendar event with the right due time. |
| **Status tracking** | Toggle each task `to do → in progress → done`. Filter the dashboard by status. |
| **Encrypted tokens** | Canvas and Google tokens are Fernet-encrypted at rest. The database alone is useless without the app's key. |
| **Row-level security** | Supabase RLS policies enforce `auth.uid() = user_id` on every table. One user literally cannot read another's data — enforced by Postgres, not application code. |

---

## Tech stack

- **Frontend + backend**: [Reflex](https://reflex.dev) (pure Python → compiled Next.js)
- **Database + auth**: [Supabase](https://supabase.com) (Postgres 17 + RLS + Google OAuth)
- **LLM**: [Google Gemini](https://ai.google.dev) (2.5 Flash Lite, free tier via AI Studio)
- **External APIs**: Canvas LMS REST, Google Calendar
- **PDF**: [PyMuPDF](https://pymupdf.readthedocs.io)
- **Scheduler**: APScheduler (in-process, 6h cadence)
- **Deploy**: Railway

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│  Browser (Next.js compiled from Reflex components)          │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐                 │
│  │  /login  │  │ /dashboard │  │ /settings│                 │
│  └──────────┘  └────────────┘  └──────────┘                 │
└───────────────────────┬────────────────────────────────────┘
                        │ websocket (Reflex) + HTTPS (FastAPI)
┌───────────────────────┴────────────────────────────────────┐
│  Reflex backend (one process, one port)                     │
│                                                              │
│  ┌────────────────────────┐  ┌────────────────────────────┐ │
│  │  State                 │  │  FastAPI routers           │ │
│  │  - AuthState           │  │  (mounted via              │ │
│  │  - AppState            │  │   api_transformer)         │ │
│  └────────────────────────┘  │  /api/canvas/*             │ │
│                               │  /api/syllabus/*           │ │
│  ┌────────────────────────┐  │  /api/calendar/*           │ │
│  │  Services              │  │  /api/assignments/*        │ │
│  │  - CanvasClient (httpx)│  └────────────────────────────┘ │
│  │  - llm_parser (Gemini) │                                  │
│  │  - gcal_client         │  ┌────────────────────────────┐ │
│  │  - pdf_extractor       │  │  APScheduler               │ │
│  │  - crypto (Fernet)     │  │  every 6h → re-sync Canvas │ │
│  └────────────────────────┘  └────────────────────────────┘ │
└───────────────────────┬────────────────────────────────────┘
                        │
     ┌──────────────────┼─────────────────┬─────────────────┐
     ▼                  ▼                 ▼                 ▼
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ Supabase │      │  Canvas  │      │  Google  │      │  Google  │
│ Postgres │      │   LMS    │      │ Calendar │      │  Gemini  │
│  + RLS   │      │          │      │          │      │          │
└──────────┘      └──────────┘      └──────────┘      └──────────┘
```

### Database (5 tables, all RLS-protected)

| Table | Purpose |
| --- | --- |
| `profiles` | Mirrors `auth.users`, populated on first sign-in. |
| `courses` | Cached Canvas courses, keyed by `user_id`. |
| `assignments` | Canvas assignments + syllabus-extracted tasks. Has `status` (`todo` / `in_progress` / `done`). |
| `calendar_events` | Cached Google Calendar events for conflict display. |
| `user_tokens` | Fernet-encrypted Canvas / Google refresh tokens. |

Every policy is `auth.uid() = user_id`. Full schema in [`supabase/schema.sql`](supabase/schema.sql).

---

## Project layout

```
Taskify/
├── taskify/                 # Reflex app
│   ├── taskify.py           # entry point, mounts FastAPI via api_transformer
│   ├── pages/               # login, dashboard, settings
│   ├── components/          # navbar, assignment_card, calendar, sync_status
│   └── state/               # AuthState, AppState
├── api/                     # FastAPI routers
│   ├── canvas.py            # POST /api/canvas/sync, save-token, disconnect
│   ├── syllabus.py          # POST /api/syllabus/parse
│   ├── calendar_routes.py   # GET/POST /api/calendar/*
│   └── assignments.py       # CRUD + status updates
├── services/                # integration clients
│   ├── canvas_client.py
│   ├── llm_parser.py       # Gemini client
│   ├── gcal_client.py
│   ├── pdf_extractor.py
│   └── crypto.py
├── db/supabase.py           # Supabase client factory
├── scheduler.py             # APScheduler 6h Canvas re-sync
├── supabase/schema.sql      # tables + RLS policies
├── requirements.txt
├── rxconfig.py
├── Procfile                 # Railway entry
└── DEPLOY.md                # full deployment runbook
```

---

## Local development

### 1. Clone + install

```bash
git clone <this repo>
cd Taskify
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example .env
```

Fill in:
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` — Supabase dashboard → Project Settings → API
- `GEMINI_API_KEY` — https://aistudio.google.com/app/apikey (free tier)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — Google Cloud Console → OAuth 2.0 Client (Web)
- `FERNET_KEY` — generate once with:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```

### 3. Apply the Supabase schema

Open [Supabase SQL editor](https://supabase.com/dashboard) → paste [`supabase/schema.sql`](supabase/schema.sql) → Run.

### 4. Configure Supabase Auth

- **Authentication → Providers → Google**: enable, paste your Google Client ID / Secret, scopes `openid email profile https://www.googleapis.com/auth/calendar`
- **Authentication → URL Configuration**: add `http://localhost:3000/auth/callback` to Redirect URLs
- On the **Google Cloud Console** side, add `https://<your-project-ref>.supabase.co/auth/v1/callback` to Authorized redirect URIs

### 5. Run

```bash
reflex init   # first time only
reflex run
```

Visit http://localhost:3000.

---

## First-time user flow

1. Click **Continue with Google** on `/login`
2. Land on `/dashboard` (empty state)
3. Open **Settings** → paste your Canvas base URL + personal access token (Canvas → Account → Settings → New Access Token)
4. Click **Save & validate** — should show "Connected as <your name>"
5. Back on **Dashboard** → **Sync Canvas** pulls every course and assignment
6. (Optional) Upload a syllabus PDF on the Syllabus tab — Gemini parses it, new assignments appear
7. Toggle status on each assignment. Every change persists and mirrors to Google Calendar.

After the first sync, APScheduler re-pulls Canvas every 6 hours automatically.

---

## Deployment

See [`DEPLOY.md`](DEPLOY.md) for the complete Railway runbook, including env vars, redirect URI setup, and a post-launch QA checklist.

TL;DR:

```bash
# Railway auto-detects Python, runs the Procfile:
web: reflex run --env prod --backend-host 0.0.0.0 --backend-port $PORT
```

Paste all `.env` values into Railway → Service → Variables, generate a domain, update `AUTH_REDIRECT_URL` + Supabase redirect URLs to the prod domain, redeploy.

---

## Security

- **No passwords stored.** Authentication is delegated entirely to Google via Supabase.
- **Tokens are encrypted at rest.** Canvas and Google refresh tokens are Fernet-encrypted before they touch the database. The `FERNET_KEY` is held only in process env.
- **RLS is the last line of defense.** If an API handler ever forgets to filter by user, the database refuses the row. Verified by querying `assignments` with an anon key — returns zero rows.
- **Service-role key is server-only.** Never shipped to the browser.

---

## Roadmap

- [ ] Mobile PWA shell
- [ ] Push notifications for due-date reminders
- [ ] Grade tracker (pull from Canvas, project GPA)
- [ ] Study-group invites via calendar event sharing
- [ ] Per-course color customization
- [ ] Offline mode (service worker cache of assignments)

---

## License

MIT — see [`LICENSE`](LICENSE) if present, otherwise assume MIT.

---

## Author

Built by **Saleh Sultan Yassin** as a CS final project. Questions / PRs welcome.
