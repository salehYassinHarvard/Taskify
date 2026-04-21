-- ============================================================
-- Taskify — Supabase Schema + RLS Policies
-- ============================================================
-- Run this via Supabase SQL Editor or apply as a migration.
--
-- Tables:
--   profiles        — synced from auth.users on sign-up
--   courses         — user's Canvas courses (cached)
--   assignments     — tasks / assignments from Canvas or manual
--   calendar_events — synced Google Calendar events
--   user_tokens     — encrypted Canvas / Google refresh tokens
-- ============================================================

-- 0. Enable UUID extension (usually already on)
create extension if not exists "uuid-ossp";

-- ============================================================
-- 1. profiles
-- ============================================================
create table if not exists public.profiles (
    id          uuid primary key references auth.users(id) on delete cascade,
    email       text not null,
    display_name text default '',
    avatar_url  text default '',
    created_at  timestamptz default now(),
    updated_at  timestamptz default now()
);

alter table public.profiles enable row level security;

create policy "Users can read own profile"
    on public.profiles for select
    using (auth.uid() = id);

create policy "Users can update own profile"
    on public.profiles for update
    using (auth.uid() = id);

create policy "Users can insert own profile"
    on public.profiles for insert
    with check (auth.uid() = id);

-- ============================================================
-- 2. courses
-- ============================================================
create table if not exists public.courses (
    id              bigserial primary key,
    user_id         uuid not null references public.profiles(id) on delete cascade,
    canvas_course_id bigint,
    name            text not null,
    course_code     text default '',
    color           text default '#3b82f6',
    created_at      timestamptz default now()
);

alter table public.courses enable row level security;

create policy "Users can CRUD own courses"
    on public.courses for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- ============================================================
-- 3. assignments
-- ============================================================
create table if not exists public.assignments (
    id                  bigserial primary key,
    user_id             uuid not null references public.profiles(id) on delete cascade,
    course_id           bigint references public.courses(id) on delete set null,
    canvas_assignment_id bigint,
    title               text not null,
    description         text default '',
    due_at              timestamptz,
    points_possible     real,
    status              text default 'todo' check (status in ('todo', 'in_progress', 'done')),
    gcal_event_id       text default '',
    created_at          timestamptz default now(),
    updated_at          timestamptz default now()
);

alter table public.assignments enable row level security;

create policy "Users can CRUD own assignments"
    on public.assignments for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- ============================================================
-- 4. calendar_events (cached from Google Calendar)
-- ============================================================
create table if not exists public.calendar_events (
    id              bigserial primary key,
    user_id         uuid not null references public.profiles(id) on delete cascade,
    gcal_event_id   text not null,
    summary         text default '',
    start_at        timestamptz,
    end_at          timestamptz,
    location        text default '',
    is_all_day      boolean default false,
    synced_at       timestamptz default now()
);

alter table public.calendar_events enable row level security;

create policy "Users can CRUD own calendar events"
    on public.calendar_events for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- ============================================================
-- 5. user_tokens (encrypted Canvas / Google refresh tokens)
-- ============================================================
create table if not exists public.user_tokens (
    id          bigserial primary key,
    user_id     uuid not null references public.profiles(id) on delete cascade,
    provider    text not null check (provider in ('canvas', 'google')),
    encrypted_token text not null,
    created_at  timestamptz default now(),
    updated_at  timestamptz default now(),
    unique(user_id, provider)
);

alter table public.user_tokens enable row level security;

create policy "Users can CRUD own tokens"
    on public.user_tokens for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- ============================================================
-- 6. Indexes for common queries
-- ============================================================
create index if not exists idx_assignments_user_due
    on public.assignments(user_id, due_at);

create index if not exists idx_calendar_events_user_start
    on public.calendar_events(user_id, start_at);

create index if not exists idx_courses_user
    on public.courses(user_id);
