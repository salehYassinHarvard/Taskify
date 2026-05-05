"""
Vercel Python serverless entry — single ASGI app for ALL /api/* routes.

vercel.json rewrites every /api/(.*) into this file, which exposes a FastAPI
`app`. Vercel autodetects ASGI apps at module top level.

Includes:
  - Canvas / Syllabus / Calendar / Assignments routers
  - /api/cron/sync-canvas — invoked by Vercel Cron (auth via CRON_SECRET)
  - /api/health
"""

from __future__ import annotations

import asyncio
import logging
import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.assignments import router as assignments_router
from api.calendar_routes import router as calendar_router
from api.canvas import router as canvas_router, _sync_user_canvas
from api.syllabus import router as syllabus_router
from db.supabase import get_supabase_client

log = logging.getLogger("taskify.api")

app = FastAPI(
    title="Taskify API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(canvas_router)
app.include_router(syllabus_router)
app.include_router(calendar_router)
app.include_router(assignments_router)


@app.get("/api/health")
def health():
    return {"ok": True}


# ---------------------------------------------------------------------------
# Vercel Cron handler — invoked daily on the schedule defined in vercel.json.
# Replaces what used to be an APScheduler in-process worker.
# ---------------------------------------------------------------------------

@app.get("/api/cron/sync-canvas")
async def cron_sync_canvas(
    authorization: str | None = Header(None, alias="Authorization"),
):
    expected = os.getenv("CRON_SECRET")
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(401, "unauthorized")

    sb = get_supabase_client()
    rows = (
        sb.table("user_tokens")
        .select("user_id")
        .eq("provider", "canvas")
        .execute()
        .data
    ) or []

    log.info("Cron: syncing %d Canvas users", len(rows))

    results: list[dict] = []

    async def _one(user_id: str) -> None:
        try:
            r = await _sync_user_canvas(user_id)
            results.append({"user_id": user_id, **r})
        except Exception as e:  # noqa: BLE001
            log.warning("Sync failed for user=%s: %s", user_id, e)
            results.append({"user_id": user_id, "error": str(e)})

    await asyncio.gather(*(_one(u["user_id"]) for u in rows))
    return {"users": len(rows), "results": results}
