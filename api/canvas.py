"""
Canvas LMS API router.

Endpoints:
  POST /api/canvas/token      — validate + save encrypted token
  DELETE /api/canvas/token    — remove saved token
  GET  /api/canvas/status     — has token? last validated? # courses?
  POST /api/canvas/sync       — trigger a manual full sync
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.deps import current_user_id
from db.supabase import get_supabase_client
from services import canvas_client as cc
from services.crypto import decrypt, encrypt

router = APIRouter(prefix="/api/canvas", tags=["canvas"])


# ---------------------------------------------------------------------------
# Pydantic request bodies
# ---------------------------------------------------------------------------

class CanvasTokenIn(BaseModel):
    base_url: str = Field(..., description="e.g. https://school.instructure.com")
    token: str = Field(..., min_length=20)


class CanvasTokenOut(BaseModel):
    valid: bool
    user_name: str = ""
    user_email: str = ""
    error: str = ""


# ---------------------------------------------------------------------------
# POST /api/canvas/token — validate + save
# ---------------------------------------------------------------------------

@router.post("/token", response_model=CanvasTokenOut)
async def save_canvas_token(
    body: CanvasTokenIn,
    user_id: str = Depends(current_user_id),
) -> CanvasTokenOut:
    # 1. Validate against Canvas
    profile = await cc.validate_token(body.base_url, body.token)
    if profile is None:
        return CanvasTokenOut(valid=False, error="Invalid Canvas token or URL")

    # 2. Encrypt + store the token plus the base URL
    payload = f"{body.base_url}||{body.token}"
    encrypted = encrypt(payload)

    sb = get_supabase_client()
    sb.table("user_tokens").upsert(
        {
            "user_id": user_id,
            "provider": "canvas",
            "encrypted_token": encrypted,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="user_id,provider",
    ).execute()

    return CanvasTokenOut(
        valid=True,
        user_name=profile.get("name", ""),
        user_email=profile.get("primary_email", ""),
    )


# ---------------------------------------------------------------------------
# DELETE /api/canvas/token
# ---------------------------------------------------------------------------

@router.delete("/token", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canvas_token(user_id: str = Depends(current_user_id)):
    sb = get_supabase_client()
    sb.table("user_tokens").delete().eq("user_id", user_id).eq(
        "provider", "canvas"
    ).execute()
    return None


# ---------------------------------------------------------------------------
# GET /api/canvas/status
# ---------------------------------------------------------------------------

@router.get("/status")
async def canvas_status(user_id: str = Depends(current_user_id)):
    sb = get_supabase_client()
    row = (
        sb.table("user_tokens")
        .select("updated_at")
        .eq("user_id", user_id)
        .eq("provider", "canvas")
        .maybe_single()
        .execute()
    )
    has_token = row is not None and row.data is not None

    courses_count = (
        sb.table("courses")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    return {
        "has_token": has_token,
        "connected_at": row.data.get("updated_at") if has_token else None,
        "courses_count": courses_count.count or 0,
    }


# ---------------------------------------------------------------------------
# POST /api/canvas/sync — pull courses + assignments, upsert to Supabase
# ---------------------------------------------------------------------------

async def _sync_user_canvas(user_id: str) -> dict[str, int]:
    """Core sync logic — also called by the scheduler."""
    sb = get_supabase_client()
    row = (
        sb.table("user_tokens")
        .select("encrypted_token")
        .eq("user_id", user_id)
        .eq("provider", "canvas")
        .maybe_single()
        .execute()
    )
    if row is None or row.data is None:
        raise HTTPException(400, "No Canvas token saved")

    base_url, token = decrypt(row.data["encrypted_token"]).split("||", 1)

    async with cc.CanvasClient(base_url, token) as client:
        courses = await client.list_courses()
        if not courses:
            return {"courses": 0, "assignments": 0}

        # Upsert courses
        sb.table("courses").upsert(
            [
                {
                    "user_id": user_id,
                    "canvas_course_id": c.id,
                    "name": c.name,
                    "course_code": c.course_code,
                }
                for c in courses
            ],
        ).execute()

        # Fetch updated course rows so we have local ids
        course_rows = (
            sb.table("courses")
            .select("id, canvas_course_id")
            .eq("user_id", user_id)
            .execute()
            .data
        )
        canvas_to_local = {
            r["canvas_course_id"]: r["id"] for r in course_rows
        }

        assignments = await client.list_all_assignments([c.id for c in courses])
        if not assignments:
            return {"courses": len(courses), "assignments": 0}

        sb.table("assignments").upsert(
            [
                {
                    "user_id": user_id,
                    "course_id": canvas_to_local.get(a.course_id),
                    "canvas_assignment_id": a.id,
                    "title": a.name,
                    "description": a.description[:2000],
                    "due_at": a.due_at.isoformat() if a.due_at else None,
                    "points_possible": a.points_possible,
                }
                for a in assignments
            ],
        ).execute()

    return {"courses": len(courses), "assignments": len(assignments)}


@router.post("/sync")
async def sync_canvas(user_id: str = Depends(current_user_id)):
    try:
        result = await _sync_user_canvas(user_id)
        return {"ok": True, **result}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Sync failed: {e}")
