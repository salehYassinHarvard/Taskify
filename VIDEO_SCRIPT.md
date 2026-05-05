# Taskify — Final Project Video Script

**Target length:** 10:00 (read at a normal pace; trim filler if you go over).
**Format:** Screen recording with voiceover. Suggested tabs to have open before you press Record:
1. https://taskify-eight-red-98.vercel.app/login
2. The repo on GitHub: `app/dashboard/page.tsx`, `api/syllabus.py`, `services/llm_parser.py`, `supabase/schema.sql`
3. The Vercel dashboard for the project
4. (Optional) A short PDF syllabus to drag in for the demo

Each section heading shows the **target end time** so you can pace yourself. The bracketed `[CUE: ...]` notes are what to show on screen while you say the line.

---

## 0:00 — 0:30 · Intro and the problem

[CUE: Live login page on the Vercel URL]

> Hi, I'm Saleh. This is Taskify — a single hub for everything a college student has to do. Today, the average student juggles Canvas, two or three professor websites, a stack of Google Doc and PDF syllabi, and a calendar app — and due dates fall through the cracks because none of those things talk to each other.
>
> Taskify pulls assignments out of Canvas automatically, reads due dates out of syllabus PDFs using Google Gemini, mirrors everything into Google Calendar, and gives you one dashboard that actually knows what you owe and when.

---

## 0:30 — 2:00 · High-level design (inputs, outputs, components)

[CUE: Switch to a window with the architecture diagram from the README, OR draw a quick whiteboard]

> Here's the architecture in two sentences. The frontend is a Next.js app with TypeScript and Tailwind, deployed to Vercel. The backend is a single FastAPI Python serverless function — also on Vercel — and it's the only thing that holds the encryption key and talks to Canvas, Google Calendar, and Gemini. Everything in between — auth, the database, and row-level security — lives on Supabase.
>
> **Inputs:** a Google sign-in, an optional Canvas token, an optional syllabus PDF, and the user's Google Calendar.
>
> **Outputs:** a unified dashboard of assignments with statuses, real Google Calendar events for each due date, and a daily background sync that re-pulls Canvas via Vercel Cron.
>
> **Components:**
> - The Next.js app handles UI and reads the database directly with the Supabase JS client. Row-level security guarantees a user only sees their own rows.
> - The FastAPI layer handles anything that needs the service-role key or external APIs: Canvas sync, syllabus parsing, calendar sync.
> - Vercel Cron hits the same FastAPI app on a schedule.
>
> One important architectural choice — I deliberately do not have the browser talk to Canvas, Calendar, or Gemini directly. Tokens never enter the browser. The frontend only ever holds the user's own Supabase JWT.

---

## 2:00 — 7:30 · Three key sections of code, in detail

### Section 1 — the database schema (RLS) · 2:00 to 3:30

[CUE: Open `supabase/schema.sql` in the editor. Highlight the `assignments` table and the policy below it.]

> The most important file in the entire project is the database schema. Every table has Row-Level Security enabled, and every policy is `auth.uid() = user_id`.
>
> What that means in practice — say a hypothetical bug in my API code forgets to filter by user. Postgres itself refuses to return the row. The database is the last line of defense, not just my application code. I verified this by querying the assignments table with a different user's JWT — it returns zero rows.
>
> This is the difference between writing multi-tenant code that "feels" safe and code that's mathematically safe. RLS is something I had not used in a class project before.

### Section 2 — the syllabus parser · 3:30 to 5:30

[CUE: Open `services/llm_parser.py`, then `api/syllabus.py`.]

> The most ambitious feature in Taskify is the syllabus parser. The user drops a PDF on the settings page; in a few seconds, every assignment in that syllabus appears on their dashboard.
>
> Here's how it works. PyMuPDF extracts the text from the PDF — that's the easy part. The hard part is turning unstructured natural-language text into structured data the database can use.
>
> I'm using Google Gemini 2.5 Flash Lite — the free tier — and the trick is that I'm passing `response_mime_type="application/json"` plus a strict system prompt that defines the schema I want. That forces Gemini to return clean JSON without any markdown fences or explanation prose. Then I parse it, sanity-check the dates, and insert.
>
> [CUE: Switch to `api/syllabus.py`, highlight the `parse_syllabus` function and the JSON parse + insert.]
>
> Notice the date sanity check — I try to parse each `due_at` with `datetime.fromisoformat`, and if it's malformed, I drop just that field rather than dropping the whole assignment. LLMs hallucinate dates pretty regularly, so failing gracefully matters.

### Section 3 — the OAuth callback · 5:30 to 7:30

[CUE: Open `app/auth/callback/route.ts`.]

> The third section I want to walk through is the auth callback. This is the route Supabase redirects to after Google sign-in.
>
> I'm using Supabase's PKCE flow — that's *Proof Key for Code Exchange* — which is the modern OAuth pattern. The browser gets a `code` query param; this server-side route exchanges that code for a real session and stores it as HTTP-only cookies. That means the access token is never visible to JavaScript on the page, which mitigates XSS attacks.
>
> [CUE: Highlight the `supabase.auth.exchangeCodeForSession(code)` call.]
>
> Right after the code exchange, I do a `profiles` upsert with the user's email, name, and avatar. The `profiles` row mirrors `auth.users` but is what the rest of my schema foreign-keys against — that gives me a clean place to attach `display_name` and `avatar_url` without touching the auth schema.

---

## 7:30 — 8:30 · New things I learned

> A few things I learned that we didn't cover in class:
>
> **Postgres Row-Level Security.** Defining authorization in SQL instead of in application code. It feels strange the first time, but once you've done it, you don't trust application-level checks the same way again.
>
> **Vercel's serverless Python runtime.** I learned that Vercel auto-detects an ASGI `app` at the top level of `api/index.py`, and that you can use a single `vercel.json` rewrite — `/api/:path*` to `/api/index` — to funnel every API route through the same FastAPI process. That gave me a single cold start and a single bundle instead of a fan-out of separate functions.
>
> **OAuth PKCE flow with HTTP-only cookies.** I had used implicit-flow OAuth before — that's the one where tokens land in the URL fragment — but moving to PKCE with cookies handled by `@supabase/ssr` is the modern, more secure approach.
>
> **Forcing JSON output from an LLM** with `response_mime_type` is something I'd never tried before. It's much more reliable than asking nicely in the prompt.

---

## 8:30 — 9:30 · Live demo

[CUE: Switch to the live site, click Continue with Google, complete sign-in, land on /dashboard.]

> Let me show it running. I'm on the live site at `taskify-eight-red-98.vercel.app`. I click Continue with Google. The OAuth flow goes through Supabase, then Google, and lands me on the dashboard.
>
> [CUE: Dashboard showing 0/0/0 stats, "All clear" empty state]
>
> First-time user — empty state. I'll head into Settings, paste my Canvas URL and personal access token, and click Save & validate.
>
> [CUE: Settings page → enter Canvas URL `https://canvas.harvard.edu` and a token → Save & validate → Connected badge appears]
>
> Connected. Back to the dashboard, I click Sync, and Canvas pulls in. [CUE: Stats update, assignments populate.]
>
> Now the syllabus parser. I drag this PDF onto the dropzone. [CUE: Drop a syllabus PDF.] Gemini parses it — about three seconds — and the new assignments appear on the dashboard with their due dates.
>
> [CUE: Click a status disc to cycle todo → in progress → done.]
>
> One click cycles the status. The change is persisted to Supabase immediately, so if I refresh — [CUE: refresh page] — it's still done.
>
> Why this demonstrates correctness: I started from zero assignments, pulled real data from a third-party API, parsed unstructured PDF text into structured JSON, and round-tripped state changes through the database. Every layer of the architecture is exercised.

---

## 9:30 — 10:00 · Course corrections + next steps

> Two course corrections from my status video.
>
> First — I originally built this on **Reflex**, a pure-Python framework, but Reflex needs a long-running WebSocket backend, which doesn't fit Vercel. I rewrote the entire frontend in Next.js + React + TypeScript so the whole stack could deploy on a single host. The Python API is still the same code; I just moved it from the Reflex bundle into a Vercel serverless function.
>
> Second — I originally planned on Anthropic Claude for syllabus parsing, but switched to **Google Gemini's free tier** to keep the running cost at zero, which mattered for a project I'd want to actually use as a student.
>
> **Next steps if I keep building:** a mobile PWA, push notifications for upcoming due dates, a grade tracker with projected GPA, OAuth for Canvas instead of personal tokens, and getting through Google's app verification so the consent screen stops showing the unverified-app warning.
>
> Thanks for watching.

---

## Speaker tips

- **Pace.** This script is around 1,400 words. At a normal speaking rate (140–150 wpm) you'll come out at exactly 10 minutes. If you read fast, slow down by adding pauses at the dashes and the cues.
- **Don't memorize.** Glance at the bullet you're on and say it in your own words. Sounding rehearsed is worse than slightly stumbling.
- **Demo first if nervous.** Some people film the demo first when their hands are warm, then add the voiceover and intro/outro. That's fine.
- **Cut and stitch.** OBS Studio or QuickTime + iMovie can splice clips. Filming each section separately is totally legal.
- **The unverified-app warning.** When you click Continue with Google in the demo, you'll see Google's "Google hasn't verified this app" screen. Click *Advanced → Continue (unsafe)* to proceed — and explain on camera that this is a known thing for unverified OAuth apps that use sensitive scopes like Calendar.

---

## Pre-record checklist

- [ ] Test screen + mic levels with a 30-second test recording.
- [ ] Sign out of the live site once, so the demo starts from the login screen.
- [ ] Have a fresh PDF syllabus on the desktop ready to drag.
- [ ] Open the four tabs listed at the top of this script in the order they appear.
- [ ] Close any unrelated tabs / hide your bookmarks bar / quit Slack.
- [ ] Set system to dark mode so the macOS aesthetic shows through.
- [ ] Disable notifications.
