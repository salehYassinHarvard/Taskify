"""Assignment card — one row in the dashboard list."""

import reflex as rx

from taskify.state.app_state import AppState


def _status_badge(status: rx.Var) -> rx.Component:
    return rx.match(
        status,
        (
            "done",
            rx.badge("Done", color_scheme="green", variant="soft"),
        ),
        (
            "in_progress",
            rx.badge("In progress", color_scheme="amber", variant="soft"),
        ),
        rx.badge("To do", color_scheme="gray", variant="soft"),
    )


def assignment_card(a: rx.Var) -> rx.Component:
    """Render a single assignment dict."""
    return rx.card(
        rx.hstack(
            # Checkbox-style status toggler
            rx.button(
                rx.cond(
                    a["status"] == "done",
                    rx.icon("check", size=16),
                    rx.cond(
                        a["status"] == "in_progress",
                        rx.icon("clock", size=16),
                        rx.icon("circle", size=16),
                    ),
                ),
                on_click=AppState.cycle_status(a["id"]),
                variant="soft",
                size="2",
                color_scheme=rx.cond(
                    a["status"] == "done",
                    "green",
                    rx.cond(a["status"] == "in_progress", "amber", "gray"),
                ),
            ),
            # Main content
            rx.vstack(
                rx.hstack(
                    rx.text(
                        a["title"],
                        weight="medium",
                        size="3",
                        text_decoration=rx.cond(
                            a["status"] == "done", "line-through", "none"
                        ),
                        color=rx.cond(
                            a["status"] == "done", "var(--gray-10)", "inherit"
                        ),
                    ),
                    _status_badge(a["status"]),
                    align="center",
                    spacing="3",
                ),
                rx.hstack(
                    rx.cond(
                        a["courses"],
                        rx.hstack(
                            rx.icon("book", size=12),
                            rx.text(
                                a["courses"]["name"],
                                size="1",
                                color="var(--gray-11)",
                            ),
                            spacing="1",
                            align="center",
                        ),
                    ),
                    rx.cond(
                        a["due_at"],
                        rx.hstack(
                            rx.icon("calendar", size=12),
                            rx.text(
                                a["due_at"],
                                size="1",
                                color="var(--gray-11)",
                            ),
                            spacing="1",
                            align="center",
                        ),
                    ),
                    rx.cond(
                        a["points_possible"],
                        rx.hstack(
                            rx.icon("star", size=12),
                            rx.text(
                                a["points_possible"].to_string() + " pts",
                                size="1",
                                color="var(--gray-11)",
                            ),
                            spacing="1",
                            align="center",
                        ),
                    ),
                    spacing="4",
                ),
                spacing="1",
                align="start",
                flex="1",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        width="100%",
        _hover={"background_color": "var(--gray-2)"},
        transition="background-color 120ms",
    )
