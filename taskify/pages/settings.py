"""Settings page — Canvas token entry + validate."""

import os

import httpx
import reflex as rx

from taskify.components.navbar import navbar
from taskify.state.auth_state import AuthState


class SettingsState(rx.State):
    canvas_base_url: str = ""
    canvas_token: str = ""

    has_canvas_token: bool = False
    canvas_user_name: str = ""
    canvas_courses_count: int = 0

    is_saving: bool = False
    save_message: str = ""
    save_success: bool = False

    # Explicit setters (Reflex doesn't auto-generate them in current version)
    def set_canvas_base_url(self, value: str):
        self.canvas_base_url = value

    def set_canvas_token(self, value: str):
        self.canvas_token = value

    # ----------------------------------------------------------
    # Load current status
    # ----------------------------------------------------------
    async def load_status(self):
        auth = await self.get_state(AuthState)
        if not auth.access_token:
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                # Reflex backend is on the same host as the API
                r = await c.get(
                    "/api/canvas/status",
                    headers={"Authorization": f"Bearer {auth.access_token}"},
                    base_url=os.getenv("API_URL", "http://localhost:8000"),
                )
                if r.status_code == 200:
                    data = r.json()
                    self.has_canvas_token = data.get("has_token", False)
                    self.canvas_courses_count = data.get("courses_count", 0)
        except Exception:  # noqa: BLE001
            pass

    # ----------------------------------------------------------
    # Save Canvas token
    # ----------------------------------------------------------
    async def save_canvas(self):
        auth = await self.get_state(AuthState)
        if not auth.access_token:
            self.save_message = "You need to be signed in."
            return

        if not self.canvas_base_url or not self.canvas_token:
            self.save_message = "Both URL and token are required."
            return

        self.is_saving = True
        self.save_message = ""
        self.save_success = False

        try:
            async with httpx.AsyncClient(timeout=20.0) as c:
                r = await c.post(
                    "/api/canvas/token",
                    json={
                        "base_url": self.canvas_base_url,
                        "token": self.canvas_token,
                    },
                    headers={"Authorization": f"Bearer {auth.access_token}"},
                    base_url=os.getenv("API_URL", "http://localhost:8000"),
                )
                data = r.json()
                if r.status_code == 200 and data.get("valid"):
                    self.save_success = True
                    self.canvas_user_name = data.get("user_name", "")
                    self.save_message = (
                        f"✓ Connected as {self.canvas_user_name or 'you'}. "
                        "Click Sync to pull assignments."
                    )
                    self.has_canvas_token = True
                    self.canvas_token = ""  # don't keep in memory
                else:
                    self.save_message = data.get("error", "Invalid token.")
        except Exception as e:  # noqa: BLE001
            self.save_message = f"Error: {e}"
        finally:
            self.is_saving = False

    # ----------------------------------------------------------
    # Remove Canvas token
    # ----------------------------------------------------------
    async def remove_canvas(self):
        auth = await self.get_state(AuthState)
        if not auth.access_token:
            return
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                await c.delete(
                    "/api/canvas/token",
                    headers={"Authorization": f"Bearer {auth.access_token}"},
                    base_url=os.getenv("API_URL", "http://localhost:8000"),
                )
            self.has_canvas_token = False
            self.canvas_user_name = ""
            self.save_message = "Canvas disconnected."
            self.save_success = False
        except Exception as e:  # noqa: BLE001
            self.save_message = f"Error: {e}"


def _canvas_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("graduation-cap", size=20, color="var(--accent-9)"),
                rx.heading("Canvas LMS", size="4", weight="medium"),
                rx.spacer(),
                rx.cond(
                    SettingsState.has_canvas_token,
                    rx.badge("Connected", color_scheme="green"),
                    rx.badge("Not connected", color_scheme="gray"),
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                "Paste a personal access token from Canvas > Account > Settings > "
                "New Access Token.",
                size="2",
                color="var(--gray-11)",
            ),
            rx.vstack(
                rx.text("Canvas URL", size="1", weight="medium"),
                rx.input(
                    placeholder="https://your-school.instructure.com",
                    value=SettingsState.canvas_base_url,
                    on_change=SettingsState.set_canvas_base_url,
                    width="100%",
                ),
                spacing="1",
                width="100%",
                align="start",
            ),
            rx.vstack(
                rx.text("Access Token", size="1", weight="medium"),
                rx.input(
                    placeholder="Canvas access token",
                    value=SettingsState.canvas_token,
                    on_change=SettingsState.set_canvas_token,
                    type="password",
                    width="100%",
                ),
                spacing="1",
                width="100%",
                align="start",
            ),
            rx.hstack(
                rx.button(
                    "Save & validate",
                    on_click=SettingsState.save_canvas,
                    loading=SettingsState.is_saving,
                    size="2",
                ),
                rx.cond(
                    SettingsState.has_canvas_token,
                    rx.button(
                        "Disconnect",
                        on_click=SettingsState.remove_canvas,
                        color_scheme="red",
                        variant="soft",
                        size="2",
                    ),
                ),
                spacing="2",
            ),
            rx.cond(
                SettingsState.save_message != "",
                rx.callout(
                    SettingsState.save_message,
                    icon=rx.cond(
                        SettingsState.save_success, "check", "info"
                    ),
                    color_scheme=rx.cond(
                        SettingsState.save_success, "green", "gray"
                    ),
                    width="100%",
                ),
            ),
            rx.cond(
                SettingsState.canvas_courses_count > 0,
                rx.text(
                    SettingsState.canvas_courses_count.to_string()
                    + " courses synced.",
                    size="2",
                    color="var(--gray-11)",
                ),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


def _account_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("user", size=20),
                rx.heading("Account", size="4", weight="medium"),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.cond(
                    AuthState.avatar_url != "",
                    rx.avatar(src=AuthState.avatar_url, size="4"),
                    rx.avatar(fallback="?", size="4"),
                ),
                rx.vstack(
                    rx.text(AuthState.user_name, weight="medium", size="3"),
                    rx.text(
                        AuthState.user_email,
                        size="2",
                        color="var(--gray-11)",
                    ),
                    spacing="0",
                    align="start",
                ),
                spacing="3",
                align="center",
            ),
            rx.button(
                "Sign out",
                on_click=AuthState.logout,
                color_scheme="red",
                variant="soft",
                size="2",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )


@rx.page(
    route="/settings",
    title="Taskify — Settings",
    on_load=[AuthState.check_auth, SettingsState.load_status],
)
def settings_page() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading("Settings", size="7", weight="bold"),
                rx.text(
                    "Manage your integrations and account.",
                    color="var(--gray-11)",
                    size="2",
                ),
                _canvas_section(),
                _account_section(),
                spacing="4",
                width="100%",
                padding_y="5",
            ),
            max_width="720px",
            padding_x="4",
        ),
        width="100%",
        min_height="100vh",
    )
