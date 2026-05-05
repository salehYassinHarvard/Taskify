# Taskify

**The one hub for everything a college student has to do.**

Live at: **https://taskify-eight-red-98.vercel.app**

Repo: **https://github.com/salehYassinHarvard/Taskify**

---

## Table of contents
1. [What problem does this solve?](#what-problem-does-this-solve)
2. [How it works (high-level design)](#how-it-works-high-level-design)
3. [Tech stack](#tech-stack)
4. [Project layout](#project-layout)
5. [Database schema](#database-schema)
6. [Running locally](#running-locally)
7. [Deploying to Vercel from scratch](#deploying-to-vercel-from-scratch)
8. [Security model](#security-model)
9. [Attribution: AI tools and external sources](#attribution-ai-tools-and-external-sources)
10. [What I'd do next](#what-id-do-next)

---

## What problem does this solve?

Most college students juggle Canvas, two or three professor websites, a stack of Google Doc / PDF syllabi, and a calendar app. Due dates fall through the cracks because the information lives in five places that don't talk to each other.

**Taskify pulls everything into one dashboard:**
- Canvas assignments and quizzes are pulled in automatically every day.
- A syllabus PDF can be dropped onto the page; Google Gemini extracts the assignments and due dates as structured JSON and they appear on the dashboard.
- Every assignment becomes a Google Calendar event so the student's existing calendar workflow keeps working.
- Statuses (`to do → in progress → done`) are tracked per assignment with a single click.

Sign-in is one click via Google. Tokens for third-party services (Canvas access tokens, Google refresh tokens) are encrypted at rest. Per-user row-level security means one student literally cannot read another's data — Postgres rejects the row.

---

## How it works (high-level design)

**Inputs**
- A Google identity (sign-in)
- (Optional) A Canvas LMS personal access token + base URL
- (Optional) A syllabus PDF
- (Implicit) The user's Google Calendar via the OAuth `calendar` scope

**Outputs**
- A dashboard of unified assignments with status, course, due date, and points
- Calendar events created for each assignment
- A daily background sync that re-pulls Canvas

**Logical flow**

```
┌────────────────────────────────────────────────────────────────────┐
│  Browser (Next.js + React)                                         │
│  ┌────────┐  ┌──────────┐  ┌────────────┐                          │
│  │ /login │  │/dashboard│  │ /settings  │                          │
│  └────────┘  └──────────┘  └────────────┘                          │
│       │            │              │                                │
│       ▼            ▼              ▼                                │
│  Supabase JS client (auth + RLS-protected queries)                 │
└────────────┬───────────────────────────────┬───────────────────────┘
             │ HTTPS                         │ HTTPS
             ▼                               ▼
┌────────────────────────────┐    ┌────────────────────────────────┐
│ FastAPI Vercel serverless  │    │ Supabase                       │
│ /api/canvas/sync           │◄──►│  • Postgres (5 tables, all RLS)│
│ /api/syllabus/parse        │    │  • Auth (Google OAuth, PKCE)   │
│ /api/calendar/*            │    │  • Service-role API for server │
│ /api/cron/sync-canvas ◄──┐ │    │    routes                      │
└────────────────────────────┘    └────────────────────────────────┘
                            │
                            │ daily 03:00 UTC
                  ┌─────────┴────────┐
                  │ Vercel Cron      │
                  └──────────────────┘

External integrations:
   • Canvas LMS REST API (course + assignment list)
   • Google Calendar API (event create / list)
   • Google Gemini 2.5 Flash Lite (syllabus → JSON)
```

The frontend never talks to Canvas, Calendar, or Gemini directly — it goes through the FastAPI layer, which holds the encryption key and the service-role Supabase key. The browser only ever sees the user's own Supabase session JWT.

---

## Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | **Next.js 14** (App Router) + **React 18** + **TypeScript** | Static-friendly, fits Vercel perfectly, type-safe |
| Styling | **Tailwind CSS** + custom macOS-flavored theme | Fast iteration, dark/light modes, glass surfaces |
| Auth | **Supabase Auth** (Google OAuth, PKCE flow) | OAuth offload, server-side cookies, no passwords |
| Database | **Supabase Postgres** + **Row-Level Security** | RLS is the only way to make multi-tenant safe |
| API | **FastAPI** (single Vercel Python serverless) | Async, type-validated bodies via Pydantic |
| LLM | **Google Gemini 2.5 Flash Lite** (free tier) | Fast, cheap, JSON-mode output is reliable |
| PDF | **PyMuPDF** | Fast, handles most syllabus layouts cleanly |
| Cron | **Vercel Cron** | Replaces APScheduler — no long-running worker needed |
| Hosting | **Vercel** end-to-end | One host, instant deploys, edge-cached |

---

## Project layout

```
.
├── app/                              # Next.js App Router (frontend pages)
│   ├── layout.tsx                    # Root layout, fonts, theme class
│   ├── globals.css                   # Tailwind + macOS theme tokens
│   ├── page.tsx                      # / → redirect based on auth
│   ├── login/page.tsx                # Sign-in screen with traffic-light window
│   ├── auth/callback/route.ts        # PKCE handler (cookie-based session)
│   ├── dashboard/page.tsx            # Stats, assignments, calendar sidebar
│   └── settings/page.tsx             # Canvas config, syllabus upload, account
├── components/                       # React components (macOS-styled)
│   ├── Navbar.tsx                    # Title bar with traffic lights
│   ├── AssignmentCard.tsx            # Apple Reminders-style row
│   ├── StatCard.tsx                  # Gradient stat tile
│   ├── CalendarWidget.tsx            # Upcoming events sidebar
│   ├── SyncStatus.tsx                # Sync banner with timestamp
│   ├── SyllabusUpload.tsx            # Drag-and-drop PDF dropzone
│   └── TrafficLights.tsx             # Decorative red/yellow/green dots
├── lib/                              # Frontend helpers
│   ├── supabase/{client,server}.ts   # Browser + server-side Supabase clients
│   ├── types.ts                      # Domain types (Assignment, Course, etc.)
│   └── utils.ts                      # cn(), formatDue(), formatRelative()
│
├── api/                              # Vercel Python serverless
│   ├── index.py                      # FastAPI ASGI entrypoint (all routes)
│   ├── canvas.py                     # Canvas LMS routes (token, status, sync)
│   ├── syllabus.py                   # PDF + Gemini parse route
│   ├── calendar_routes.py            # Google Calendar list/sync routes
│   ├── assignments.py                # Assignment CRUD
│   └── deps.py                       # Auth dep (verifies Supabase JWT)
├── services/                         # Pure-Python integrations
│   ├── canvas_client.py              # Async httpx client for Canvas REST
│   ├── llm_parser.py                 # Gemini call with strict JSON schema
│   ├── gcal_client.py                # Google Calendar wrapper
│   ├── pdf_extractor.py              # PyMuPDF text extraction
│   └── crypto.py                     # Fernet encrypt/decrypt
├── db/supabase.py                    # Supabase service-role client factory
├── supabase/schema.sql               # 5 tables + RLS policies
│
├── vercel.json                       # Rewrites, crons, function memory
├── tailwind.config.ts                # Theme tokens
├── next.config.mjs                   # Local-dev API rewrite
├── package.json                      # Frontend deps
├── requirements.txt                  # Python deps
├── .env.example                      # Env-var checklist
├── VERCEL.md                         # Deploy runbook
└── README.md                         # this file
```

---

## Database schema

Five tables, all with Row-Level Security enabled. Every policy is `auth.uid() = user_id`. Full schema in [`supabase/schema.sql`](supabase/schema.sql).

| Table | Purpose |
| --- | --- |
| `profiles` | Mirrors `auth.users`. Populated by the auth callback on first sign-in. |
| `courses` | Cached Canvas courses, keyed by `user_id`. |
| `assignments` | Canvas assignments + syllabus-extracted tasks. Has a `status` column. |
| `calendar_events` | Cached Google Calendar events for the dashboard's Upcoming widget. |
| `user_tokens` | Fernet-encrypted Canvas (and Google) refresh tokens. |

RLS is the single most important piece of the database design. If a server-side handler ever forgets to filter by user, **Postgres refuses the row** instead of leaking data. I verified this by querying `assignments` with the anon key and a different user's JWT — it returns zero rows.

---

## Running locally

You need:
- **Node.js 18+**
- **Python 3.11+**
- A free **Supabase** project ([supabase.com](https://supabase.com))
- A **Google Cloud** OAuth client (Web app type) — for sign-in + Calendar
- A **Gemini API key** — free tier at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### 1. Clone and install

```bash
git clone https://github.com/salehYassinHarvard/Taskify.git
cd Taskify
npm install
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env.local
```

Fill in every value in `.env.local`. The two values you have to *generate* are:

```bash
# Encryption key for storing third-party tokens
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Cron secret (any long random string)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

The Supabase keys (URL, anon, service-role) come from your Supabase project → Settings → API.

### 3. Apply the database schema

Open [`supabase/schema.sql`](supabase/schema.sql) in the Supabase SQL editor and click *Run*. Five tables are created, RLS is enabled.

### 4. Configure Supabase Auth

In Supabase → Authentication → Providers → Google: enable, paste your Google OAuth client ID and secret, and add the scopes:

```
openid email profile https://www.googleapis.com/auth/calendar
```

In Supabase → Authentication → URL Configuration → Redirect URLs, add:

```
http://localhost:3000/auth/callback
https://<your-vercel-domain>/auth/callback
```

In Google Cloud Console → APIs & Services → Credentials → your OAuth client → Authorized redirect URIs, add:

```
https://<your-supabase-ref>.supabase.co/auth/v1/callback
```

### 5. Run

Two terminals:

```bash
# Terminal 1 — Python API
uvicorn api.index:app --reload --port 8000
```

```bash
# Terminal 2 — Next.js frontend
PYTHON_API_URL=http://localhost:8000 npm run dev
```

Open http://localhost:3000.

---

## Deploying to Vercel from scratch

Full runbook in [`VERCEL.md`](VERCEL.md). Short version:

1. Push the repo to GitHub.
2. Vercel → Import project → pick the repo.
3. Settings → Environment Variables → paste every value from `.env.example`.
4. Deploy. Vercel auto-detects Next.js for the frontend and the FastAPI ASGI app at `api/index.py` for the Python serverless function.
5. After the first deploy, copy the generated Vercel domain back into Supabase's Site URL + Redirect URLs.

The daily Canvas re-sync runs automatically via the cron entry in `vercel.json`.

---

## Security model

- **No passwords stored.** Authentication is delegated entirely to Google via Supabase. Only Supabase ever sees the OAuth handshake.
- **Tokens encrypted at rest.** Canvas access tokens and Google refresh tokens are Fernet-encrypted before being written to `user_tokens.encrypted_token`. The `FERNET_KEY` lives only in the serverless function's env — the database alone is useless without it.
- **RLS is the last line of defense.** Even if an API handler forgets to filter by `user_id`, Postgres refuses the row.
- **Service-role key is server-only.** It's set as a Vercel function-only env var; the browser never sees it. Browser-side queries use the anon key, which is safe to ship because RLS makes it useless without a valid JWT.
- **Cron auth.** The cron route requires `Authorization: Bearer <CRON_SECRET>`. Vercel sends this automatically; an unauthenticated request gets a 401.

---

## Attribution: AI tools and external sources

This project was built in close collaboration with **Claude (Anthropic)** acting as a pair-programming partner via [Claude Code](https://claude.com/claude-code). I want to be specific about what that meant in practice, because "I used AI" can mean many different things.

### What I designed and decided
- Choosing the problem domain (the unified-due-dates pain point), the feature set, the tech stack (Next.js + Supabase + Vercel + Gemini), and the product flow (Google sign-in, Canvas token, syllabus drop, calendar mirror, status toggles).
- The database schema and the decision to lean on Postgres RLS instead of application-level access checks.
- The macOS aesthetic (traffic-light window chrome, glass surfaces, Sonoma wallpaper, SF Pro typography).
- The deployment topology (frontend + Python serverless + cron all on Vercel, no separate backend host).
- The UX details — segmented filter, Apple-Reminders-style status discs, gradient stat cards.

### What Claude generated under my direction
- The bulk of the React + TypeScript component code and the FastAPI router code, written iteratively. I described the intent and reviewed/adjusted the output rather than copying tutorials.
- The Tailwind CSS theme tokens implementing the macOS look.
- The Fernet encryption helper and the Supabase client factory.
- Initial drafts of `vercel.json`, `tailwind.config.ts`, and the schema.

### What Claude did beyond writing code
- Audited the original Reflex codebase and found two real bugs before the rewrite — an `on_mount` conditional redirect that wasn't a valid event handler, and an `httpx.AsyncClient.get(base_url=...)` misuse that would have raised at runtime.
- Drove the production deploy via browser automation: imported the repo into Vercel, pasted env vars, restored the paused Supabase project, applied auth redirect URL config, enabled the Google provider in Supabase, added the missing redirect URI in Google Cloud Console, and published the OAuth app from "Testing" to "In production" so anyone with a Google account can sign in.

### What I did not get from AI
- Anthropic's Supabase Postgres + RLS docs and the [Supabase + Next.js guide](https://supabase.com/docs/guides/auth/server-side/nextjs) were primary references for the auth flow and PKCE callback.
- The [Vercel Cron docs](https://vercel.com/docs/cron-jobs) were the source for the schedule expression syntax and the `CRON_SECRET` auth pattern.
- The Canvas LMS REST API behavior (pagination, course `enrollment_state` filter, restricted-course handling) came from [Canvas's official API docs](https://canvas.instructure.com/doc/api/).
- The [Google AI Studio docs](https://ai.google.dev/gemini-api/docs) for setting `response_mime_type=application/json` to force JSON output.

### External code from tutorials or Stack Overflow
- None directly copy-pasted. Patterns (e.g., the React-friendly value setter via `Object.getOwnPropertyDescriptor(...).set` for programmatically populating a controlled input on Vercel) are common idioms but were typed fresh.

### Other tools
- `gh` (GitHub CLI) for repo operations.
- Chrome (driven by Claude in Chrome) to perform the live Vercel + Supabase + Google Cloud Console configuration steps.

If you're a mentor evaluating this project: I'd say roughly 70–80% of the lines of code were drafted by Claude under my direction, with the remainder being my edits, deletions, and configuration. Every line was reviewed and tested by me before deploy. The architecture, choices, and final behavior are my responsibility.

---

## What I'd do next

In rough priority order:

1. **Mobile PWA shell.** The macOS aesthetic translates well to mobile if I add an installable manifest and tweak the segmented filter to be touch-first.
2. **Push notifications for upcoming due dates.** Use the [Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API) + a separate cron entry that fans out reminders 24h and 1h before each due date.
3. **Grade tracker + GPA projection.** Pull grades from Canvas (already in the API I'm calling), let users mark predicted grades for upcoming work, and show a projected term GPA.
4. **Per-course color customization** + a calendar-view dashboard alternative.
5. **Canvas OAuth instead of personal access tokens.** Today the user pastes a token; for non-technical users that's a friction point. School-wide OAuth approval is a process, but worth doing.
6. **Get Google verification.** Currently the OAuth consent screen shows an "unverified app" warning because the calendar scope is sensitive. Verification is a multi-week process but removes that warning for new users.
7. **Offline mode.** Service-worker cache of recent assignments so the dashboard works on a flaky train.

---

## License

MIT — feel free to fork.

## Contact

Built by **Saleh Sultan Yassin** as a CS final project.
