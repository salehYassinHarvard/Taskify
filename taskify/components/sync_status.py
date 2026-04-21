"""Small banner showing last sync time + a manual sync button."""

import reflex as rx

from taskify.state.app_state import AppState


def sync_status() -> rx.Component:
    return rx.hstack(
        rx.cond(
            AppState.is_syncing,
            rx.hstack(
                rx.spinner(size="1"),
                rx.text("Syncing…", size="2", color="var(--gray-11)"),
                spacing="2",
                align="center",
            ),
            rx.cond(
                AppState.last_synced_at != "",
                rx.hstack(
                    rx.icon("check", size=14, color="var(--green-9)"),
                    rx.text(
                        "Last sync: " + AppState.last_synced_at,
                        size="2",
                        color="var(--gray-11)",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Not synced yet.",
                    size="2",
                    color="var(--gray-11)",
                ),
            ),
        ),
        rx.spacer(),
        rx.button(
            rx.icon("refresh-cw", size=14),
            "Sync Canvas",
            size="2",
            variant="soft",
            on_click=AppState.trigger_canvas_sync,
            loading=AppState.is_syncing,
        ),
        rx.cond(
            AppState.sync_message != "",
            rx.text(
                AppState.sync_message,
                size="1",
                color="var(--gray-10)",
            ),
        ),
        width="100%",
        align="center",
        padding="3",
        border="1px solid var(--gray-4)",
        border_radius="8px",
        bg="var(--gray-1)",
    )
