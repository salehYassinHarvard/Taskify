# Taskify — Railway Deployment Guide

End-to-end instructions for shipping Taskify to Railway with Supabase + Google OAuth + Canvas + Anthropic + Google Calendar integrations.

---

## 1. Prerequisites — keys you need

| Secret               | Where to get it                                                                                     |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| SUPABASE_URL         | Supabase dashboard → Project Settings → API → URL                                                   |
| SUPABASE_ANON_KEY    | Supabase dashboard → Project Settings → API → anon public key                                       |
| SUPABASE_SERVICE_KEY | Supabase dashboard → Project Settings → API → service_role key (⚠️ server-only)                     |
| FERNET_KEY           | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`         |
| ANTHROPIC_API_KEY    | https://console.anthropic.com/ → API Keys                                                           |
| GOOGLE_CLIENT_ID     | Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client                             |
| GOOGLE_CLIENT_SECRET | Same as above                                                                                       |

The Canvas token is **per-user**, entered on the Settings page — no deploy-time secret needed.

---

## 2. Supabase — one-time configuration

Schema was already applied via SQL migrations. Still TODO in the dashboard:

### 2a. Enable Google OAuth
1. Authentication → Providers → Google → Enable
2. Paste your Google `CLIENT_ID` and `CLIENT_SECRET`
3. Scopes: request `openid email profile https://www.googleapis.com/auth/calendar`
4. Save

### 2b. Configure redirect URLs
Authentication → URL Configuration:
- **Site URL**: `https://<your-railway-domain>.up.railway.app`
- **Redirect URLs**: add both
  - `http://localhost:3000/auth/callback` (dev)
  - `https://<your-railway-domain>.up.railway.app/auth/callback` (prod)

### 2c. Google Cloud Console
Authorized redirect URIs must include the Supabase callback:
```
https://xmyaxmiyimyownpysiwk.supabase.co/auth/v1/callback
```

---

## 3. Railway — project setup

1. Sign in at https://railway.app → New Project → Deploy from GitHub
2. Point it at this repo (branch `main`)
3. It auto-detects Python. Railway will:
   - `pip install -r requirements.txt`
   - Run `Procfile` → `reflex run --env prod --backend-only --backend-host 0.0.0.0 --backend-port $PORT`

### 3a. Environment variables (Service → Variables)

Paste all of these:

```
SUPABASE_URL=https://xmyaxmiyimyownpysiwk.supabase.co
SUPABASE_ANON_KEY=<from Supabase>
SUPABASE_SERVICE_KEY=<from Supabase>
FERNET_KEY=<from the generate command above>
ANTHROPIC_API_KEY=<from Anthropic>
AUTH_REDIRECT_URL=https://<your-railway-domain>.up.railway.app/auth/callback
API_URL=https://<your-railway-domain>.up.railway.app
```

### 3b. Frontend hosting (important)

Railway's Procfile above runs **backend-only**. For the Reflex frontend:

**Option A — same service, full Reflex:** change the Procfile to
```
web: reflex run --env prod --backend-host 0.0.0.0 --backend-port $PORT
```
Reflex will build the Next.js frontend at deploy time and serve everything from one port.

**Option B — split deploy (recommended for scale):** deploy the backend to Railway and export the frontend to Vercel via `reflex export`. See https://reflex.dev/docs/hosting/.

For v1 use Option A.

### 3c. Expose a public domain

Railway → Service → Networking → Generate Domain. Paste it into:
- `AUTH_REDIRECT_URL`
- `API_URL`
- Supabase Site URL + Redirect URLs

Redeploy.

---

## 4. First-time app initialization

After deploy:

1. Visit `https://<domain>/login`
2. Click **Continue with Google** — Supabase OAuth runs
3. You land on `/dashboard` — should show empty state
4. Go to **Settings** → enter Canvas URL + token from Canvas > Account > Settings > New Access Token
5. Click **Save & validate** — you should see "Connected as …"
6. Back on **Dashboard** → **Sync Canvas** — pulls courses + assignments
7. Every 6 hours APScheduler will re-sync for every user who has a saved token

---

## 5. Post-launch QA checklist

- [ ] `GET /dashboard` as unauthenticated user → redirects to `/login`
- [ ] Google OAuth loop completes, `profiles` row inserted
- [ ] Canvas token: invalid URL → clear error in UI
- [ ] Canvas token: valid → courses + assignments appear within ~10s of Sync
- [ ] Assignment status toggle (to-do → in-progress → done) persists on reload
- [ ] Filter buttons (All / To do / In progress / Done) work
- [ ] Settings → Disconnect Canvas removes the token row
- [ ] APScheduler sync runs 6h after deploy (check Railway logs for "Scheduler: syncing Canvas")
- [ ] Railway logs show no tracebacks during normal use
- [ ] Supabase RLS: `SELECT * FROM assignments` with an anon key returns zero rows
- [ ] `POST /api/syllabus/parse` with a PDF creates a course + assignments

---

## 6. Common failure modes

| Symptom                                | Fix                                                                     |
| -------------------------------------- | ----------------------------------------------------------------------- |
| 401 on every API call                  | `SUPABASE_SERVICE_KEY` wrong; anon key used by mistake                   |
| OAuth redirects loop                    | `AUTH_REDIRECT_URL` doesn't match the Supabase "Redirect URLs" list      |
| "FERNET_KEY" KeyError on Canvas save    | Env var missing/empty in Railway                                        |
| Assignments don't sync automatically    | Scheduler hasn't started — make any HTTP request to trigger it once     |
| PDF upload → "PDF extraction failed"   | PyMuPDF didn't install; check build logs for wheel errors               |

---

## 7. Local development

```bash
cp .env.example .env
# fill in all values (use http://localhost:3000/auth/callback for redirect)
pip install -r requirements.txt
reflex init  # first time only
reflex run
```

Visit http://localhost:3000 → login flow.
