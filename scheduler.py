"""
APScheduler background jobs.

Currently one job:
  - Every 6 hours, sync Canvas for every user who has a saved token.

Started as part of the main Reflex app lifespan (see taskify/taskify.py).
"""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db.supabase import get_supabase_client

log = logging.getLogger("taskify.scheduler")


async def sync_all_canvas_users() -> None:
    """Fan-out Canvas sync for every user with a saved Canvas token."""
    # Late import to avoid circular
    from api.canvas import _sync_user_canvas

    sb = get_supabase_client()
    users = (
        sb.table("user_tokens")
        .select("user_id")
        .eq("provider", "canvas")
        .execute()
        .data
    ) or []

    log.info("Scheduler: syncing Canvas for %d users", len(users))

    async def _one(user_id: str) -> None:
        try:
            result = await _sync_user_canvas(user_id)
            log.info("Synced user=%s result=%s", user_id, result)
        except Exception as e:  # noqa: BLE001
            log.warning("Sync failed for user=%s: %s", user_id, e)

    await asyncio.gather(*(_one(u["user_id"]) for u in users))


_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler:
    """Idempotent — safe to call multiple times."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        sync_all_canvas_users,
        trigger=IntervalTrigger(hours=6),
        id="canvas_sync_all_users",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    _scheduler.start()
    log.info("APScheduler started — Canvas sync every 6h")
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
