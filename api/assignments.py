"""
Assignments CRUD API.

  GET    /api/assignments           — list (filterable)
  GET    /api/assignments/{id}      — one
  PATCH  /api/assignments/{id}      — partial update (status, title, due_at, etc.)
  DELETE /api/assignments/{id}      — delete
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import current_user_id
from db.supabase import get_supabase_client

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


class AssignmentPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[str] = None
    status: Optional[str] = None
    points_possible: Optional[float] = None


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("")
async def list_assignments(
    status: Optional[str] = Query(None, pattern="^(todo|in_progress|done)$"),
    course_id: Optional[int] = None,
    user_id: str = Depends(current_user_id),
):
    sb = get_supabase_client()
    q = (
        sb.table("assignments")
        .select("*, courses(name, course_code, color)")
        .eq("user_id", user_id)
        .order("due_at", desc=False)
    )
    if status:
        q = q.eq("status", status)
    if course_id is not None:
        q = q.eq("course_id", course_id)

    return {"assignments": q.execute().data}


# ---------------------------------------------------------------------------
# Get one
# ---------------------------------------------------------------------------

@router.get("/{assignment_id}")
async def get_assignment(
    assignment_id: int,
    user_id: str = Depends(current_user_id),
):
    sb = get_supabase_client()
    r = (
        sb.table("assignments")
        .select("*, courses(name, course_code, color)")
        .eq("id", assignment_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if r is None or r.data is None:
        raise HTTPException(404, "Assignment not found")
    return r.data


# ---------------------------------------------------------------------------
# Patch
# ---------------------------------------------------------------------------

@router.patch("/{assignment_id}")
async def patch_assignment(
    assignment_id: int,
    body: AssignmentPatch,
    user_id: str = Depends(current_user_id),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")

    sb = get_supabase_client()
    r = (
        sb.table("assignments")
        .update(updates)
        .eq("id", assignment_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not r.data:
        raise HTTPException(404, "Assignment not found or not owned")
    return r.data[0]


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete("/{assignment_id}", status_code=204)
async def delete_assignment(
    assignment_id: int,
    user_id: str = Depends(current_user_id),
):
    sb = get_supabase_client()
    sb.table("assignments").delete().eq("id", assignment_id).eq(
        "user_id", user_id
    ).execute()
    return None
