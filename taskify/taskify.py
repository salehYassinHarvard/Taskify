"""
Taskify — Reflex app entry point.

Responsibilities:
  - Register all pages (imported for side effects via @rx.page)
  - Mount FastAPI routers ahead of Reflex's Starlette backend via
    the `api_transformer` hook
  - Start the APScheduler background job on first request
"""

from __future__ import annotations

import logging

import reflex as rx
from fastapi import FastAPI
from starlette.types import ASGIApp

# Register pages (each module uses @rx.page decorator)
from taskify.pages import login as _login  # noqa: F401
from taskify.pages import dashboard as _dashboard  # noqa: F401
from taskify.pages import settings as _settings  # noqa: F401

# FastAPI routers
from api.assignments import router as assignments_router
from api.calendar_routes import router as calendar_router
from api.canvas import router as canvas_router
from api.syllabus import router as syllabus_router

from scheduler import start_scheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s %(message)s",
)


# ---------------------------------------------------------------------------
# api_transformer — Reflex ≥0.9 passes a Starlette ASGI app (no include_router).
# We layer FastAPI routes on top, then mount the Reflex backend as fallback.
# ---------------------------------------------------------------------------

def mount_api(reflex_backend: ASGIApp) -> ASGIApp:
    api = FastAPI()
    api.include_router(canvas_router)
    api.include_router(syllabus_router)
    api.include_router(calendar_router)
    api.include_router(assignments_router)

    @api.middleware("http")
    async def _lazy_startup(request, call_next):
        # APScheduler needs a running event loop; start it on first request.
        # start_scheduler() is idempotent.
        start_scheduler()
        return await call_next(request)

    api.mount("", reflex_backend)
    return api


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@rx.page(route="/", title="Taskify")
def index_page() -> rx.Component:
    from taskify.state.auth_state import AuthState
    return rx.center(
        rx.spinner(size="3"),
        width="100%",
        min_height="100vh",
        on_mount=rx.cond(
            AuthState.is_authenticated,
            rx.redirect("/dashboard"),
            rx.redirect("/login"),
        ),
    )


# ---------------------------------------------------------------------------
# Reflex app
# ---------------------------------------------------------------------------

app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="blue",
        radius="medium",
    ),
    style={
        "font_family": "'Inter', system-ui, sans-serif",
        "::selection": {"background_color": "var(--accent-4)"},
    },
    api_transformer=mount_api,
)
