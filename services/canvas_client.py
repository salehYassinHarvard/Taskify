"""
Canvas LMS API client (httpx).

We use Canvas *personal access tokens* (user generates them in
Canvas > Account > Settings > New Access Token). Much simpler than OAuth
and doesn't require school-admin approval.

Docs: https://canvas.instructure.com/doc/api/
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx


@dataclass
class CanvasCourse:
    id: int
    name: str
    course_code: str


@dataclass
class CanvasAssignment:
    id: int
    course_id: int
    name: str
    description: str
    due_at: datetime | None
    points_possible: float | None
    html_url: str


class CanvasClient:
    """Async Canvas REST client."""

    def __init__(self, base_url: str, token: str, timeout: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=f"{self.base_url}/api/v1",
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    async def __aenter__(self) -> "CanvasClient":
        return self

    async def __aexit__(self, *_):
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Token validation
    # ------------------------------------------------------------------
    async def validate(self) -> dict[str, Any] | None:
        """Return user profile if token is valid, None otherwise."""
        try:
            r = await self._client.get("/users/self/profile")
            if r.status_code == 200:
                return r.json()
            return None
        except httpx.HTTPError:
            return None

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------
    async def list_courses(self) -> list[CanvasCourse]:
        r = await self._client.get(
            "/courses",
            params={
                "enrollment_state": "active",
                "per_page": 100,
                "include[]": "term",
            },
        )
        r.raise_for_status()
        out: list[CanvasCourse] = []
        for c in r.json():
            # Canvas returns some weird objects for restricted courses
            if "name" not in c:
                continue
            out.append(
                CanvasCourse(
                    id=c["id"],
                    name=c["name"],
                    course_code=c.get("course_code", ""),
                )
            )
        return out

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------
    async def list_assignments(self, course_id: int) -> list[CanvasAssignment]:
        r = await self._client.get(
            f"/courses/{course_id}/assignments",
            params={"per_page": 100, "order_by": "due_at"},
        )
        r.raise_for_status()
        out: list[CanvasAssignment] = []
        for a in r.json():
            due = None
            if a.get("due_at"):
                try:
                    due = datetime.fromisoformat(a["due_at"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            out.append(
                CanvasAssignment(
                    id=a["id"],
                    course_id=course_id,
                    name=a.get("name", ""),
                    description=a.get("description") or "",
                    due_at=due,
                    points_possible=a.get("points_possible"),
                    html_url=a.get("html_url", ""),
                )
            )
        return out

    async def list_all_assignments(
        self, course_ids: list[int]
    ) -> list[CanvasAssignment]:
        """Fan-out: fetch assignments for every course concurrently."""
        results = await asyncio.gather(
            *(self.list_assignments(cid) for cid in course_ids),
            return_exceptions=True,
        )
        flat: list[CanvasAssignment] = []
        for r in results:
            if isinstance(r, list):
                flat.extend(r)
        return flat


# ---------------------------------------------------------------------------
# Convenience — run a quick validate without needing async context
# ---------------------------------------------------------------------------

async def validate_token(base_url: str, token: str) -> dict[str, Any] | None:
    async with CanvasClient(base_url, token) as client:
        return await client.validate()
