"""
Taskify — Reflex app entry point.

Responsibilities:
  - Register all pages (imported for side effects via @rx.page)
  - Mount FastAPI routers onto Reflex's built-in FastAPI app via
    the `api_transformer` hook
  - Start the APScheduler background job on first request
"""

from __future__ import annotations

import logging

import reflex as rx
from fastapi import FastAPI

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
# api_transformer — receives Reflex's FastAPI app and mutates it in place
# ---------------------------------------------------------------------------

def mount_api(fastapi_app: FastAPI) -> FastAPI:
    fastapi_app.include_router(canvas_router)
    fastapi_app.include_router(syllabus_router)
    fastapi_app.include_router(calendar_router)
    fastapi_app.include_router(assignments_router)

    @fastapi_app.middleware("http")
    async def _lazy_startup(request, call_next):
        # APScheduler needs a running event loop; start it on first request.
        # start_scheduler() is idempotent.
        start_scheduler()
        return await call_next(request)

    return fastapi_app


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
