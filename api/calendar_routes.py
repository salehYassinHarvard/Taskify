"""
Google Calendar routes.

The Google access_token lives on the Supabase session as `provider_token`.
The frontend (Reflex state) passes it along via the X-Google-Token header.

Endpoints:
  GET  /api/calendar/events
  POST /api/calendar/sync-assignments  — create gcal events for assignments
"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException

from api.deps import current_user_id
from db.supabase import get_supabase_client
from services import gcal_client

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


def _require_google_token(
    x_google_token: str = Header(..., alias="X-Google-Token"),
) -> str:
    if not x_google_token:
        raise HTTPException(401, "Missing Google provider token")
    return x_google_token


# ---------------------------------------------------------------------------
# GET /api/calendar/events
# ---------------------------------------------------------------------------

@router.get("/events")
async def list_events(
    user_id: str = Depends(current_user_id),
    google_token: str = Depends(_require_google_token),
):
    try:
        events = gcal_client.list_upcoming_events(google_token, max_results=100)
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    # Cache to Supabase for offline display
    sb = get_supabase_client()
    rows = []
    for e in events:
        start = e.get("start", {})
        end = e.get("end", {})
        rows.append(
            {
                "user_id": user_id,
                "gcal_event_id": e["id"],
                "summary": e.get("summary", ""),
                "start_at": start.get("dateTime") or start.get("date"),
                "end_at": end.get("dateTime") or end.get("date"),
                "location": e.get("location", ""),
                "is_all_day": "date" in start and "dateTime" not in start,
            }
        )
    if rows:
        sb.table("calendar_events").upsert(
            rows, on_conflict="gcal_event_id"
        ).execute()

    return {"count": len(events), "events": events}


# ---------------------------------------------------------------------------
# POST /api/calendar/sync-assignments
# ---------------------------------------------------------------------------

@router.post("/sync-assignments")
async def sync_assignments_to_gcal(
    user_id: str = Depends(current_user_id),
    google_token: str = Depends(_require_google_token),
):
    sb = get_supabase_client()
    rows = (
        sb.table("assignments")
        .select("id, title, description, due_at, gcal_event_id")
        .eq("user_id", user_id)
        .neq("due_at", None)
        .eq("gcal_event_id", "")
        .execute()
        .data
    )

    created = 0
    for a in rows:
        try:
            due = datetime.fromisoformat(a["due_at"].replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            continue
        try:
            event = gcal_client.create_event(
                google_token,
                summary=f"📚 {a['title']}",
                description=(a.get("description") or "")[:500],
                start=due - timedelta(minutes=30),
                end=due,
            )
            sb.table("assignments").update(
                {"gcal_event_id": event["id"]}
            ).eq("id", a["id"]).execute()
            created += 1
        except RuntimeError:
            continue

    return {"created": created, "total_scanned": len(rows)}
