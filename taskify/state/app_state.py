"""
App state — assignments, courses, calendar events.

Directly queries Supabase using the service client (server-side in Reflex,
so it's safe). Filters by the current user id from AuthState.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional, TypedDict

import reflex as rx

from db.supabase import get_supabase_client
from taskify.state.auth_state import AuthState


class CourseInfo(TypedDict, total=False):
    name: str
    course_code: str
    color: str


class Assignment(TypedDict, total=False):
    id: int
    user_id: str
    course_id: Optional[int]
    canvas_assignment_id: Optional[int]
    title: str
    description: str
    due_at: Optional[str]
    points_possible: Optional[float]
    status: str
    gcal_event_id: str
    courses: Optional[CourseInfo]


class Course(TypedDict, total=False):
    id: int
    name: str
    course_code: str
    color: str


class CalendarEvent(TypedDict, total=False):
    id: int
    gcal_event_id: str
    summary: str
    start_at: Optional[str]
    end_at: Optional[str]
    location: str
    is_all_day: bool


class AppState(rx.State):
    # Assignments (list of dicts for template rendering)
    assignments: list[Assignment] = []
    courses: list[Course] = []
    calendar_events: list[CalendarEvent] = []

    # UI state
    is_loading: bool = False
    is_syncing: bool = False
    last_synced_at: str = ""
    sync_message: str = ""
    status_filter: str = "all"  # all | todo | in_progress | done

    # ------------------------------------------------------------------
    # Computed views
    # ------------------------------------------------------------------

    @rx.var
    def filtered_assignments(self) -> list[Assignment]:
        if self.status_filter == "all":
            return self.assignments
        return [a for a in self.assignments if a.get("status") == self.status_filter]

    @rx.var
    def todo_count(self) -> int:
        return sum(1 for a in self.assignments if a.get("status") == "todo")

    @rx.var
    def done_count(self) -> int:
        return sum(1 for a in self.assignments if a.get("status") == "done")

    @rx.var
    def has_assignments(self) -> bool:
        return len(self.assignments) > 0

    # ------------------------------------------------------------------
    # Load from Supabase
    # ------------------------------------------------------------------

    async def load_assignments(self):
        """Fetch all assignments for the current user."""
        auth = await self.get_state(AuthState)
        if not auth.user_id:
            return

        self.is_loading = True
        try:
            sb = get_supabase_client()
            rows = (
                sb.table("assignments")
                .select("*, courses(name, course_code, color)")
                .eq("user_id", auth.user_id)
                .order("due_at", desc=False)
                .execute()
                .data
            ) or []
            self.assignments = rows
        except Exception as e:  # noqa: BLE001
            self.sync_message = f"Load failed: {e}"
        finally:
            self.is_loading = False

    async def load_courses(self):
        auth = await self.get_state(AuthState)
        if not auth.user_id:
            return
        try:
            sb = get_supabase_client()
            self.courses = (
                sb.table("courses")
                .select("*")
                .eq("user_id", auth.user_id)
                .order("name")
                .execute()
                .data
            ) or []
        except Exception:  # noqa: BLE001
            pass

    async def load_calendar_events(self):
        auth = await self.get_state(AuthState)
        if not auth.user_id:
            return
        try:
            sb = get_supabase_client()
            self.calendar_events = (
                sb.table("calendar_events")
                .select("*")
                .eq("user_id", auth.user_id)
                .order("start_at")
                .execute()
                .data
            ) or []
        except Exception:  # noqa: BLE001
            pass

    async def load_all(self):
        await asyncio.gather(
            self.load_assignments(),
            self.load_courses(),
            self.load_calendar_events(),
        )

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def set_status(self, assignment_id: int, new_status: str):
        """Toggle todo → in_progress → done."""
        auth = await self.get_state(AuthState)
        if not auth.user_id:
            return
        sb = get_supabase_client()
        sb.table("assignments").update({"status": new_status}).eq(
            "id", assignment_id
        ).eq("user_id", auth.user_id).execute()
        await self.load_assignments()

    async def cycle_status(self, assignment_id: int):
        cur = next(
            (a for a in self.assignments if a.get("id") == assignment_id), None
        )
        if cur is None:
            return
        order = ["todo", "in_progress", "done"]
        idx = order.index(cur.get("status", "todo")) if cur.get("status") in order else 0
        await self.set_status(assignment_id, order[(idx + 1) % 3])

    def set_status_filter(self, value: str):
        self.status_filter = value

    # ------------------------------------------------------------------
    # Canvas sync trigger (calls core sync directly — same process)
    # ------------------------------------------------------------------

    async def trigger_canvas_sync(self):
        auth = await self.get_state(AuthState)
        if not auth.user_id:
            return
        self.is_syncing = True
        self.sync_message = "Syncing Canvas…"
        try:
            # Import here to avoid circular
            from api.canvas import _sync_user_canvas

            result = await _sync_user_canvas(auth.user_id)
            self.sync_message = (
                f"Synced {result['courses']} courses, "
                f"{result['assignments']} assignments."
            )
            self.last_synced_at = datetime.now(timezone.utc).isoformat()
            await self.load_all()
        except Exception as e:  # noqa: BLE001
            self.sync_message = f"Sync error: {e}"
        finally:
            self.is_syncing = False
