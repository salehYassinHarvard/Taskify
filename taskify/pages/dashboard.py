"""Dashboard — assignment list + calendar widget."""

import reflex as rx

from taskify.components.assignment_card import assignment_card
from taskify.components.calendar import calendar_widget
from taskify.components.navbar import navbar
from taskify.components.sync_status import sync_status
from taskify.state.app_state import AppState
from taskify.state.auth_state import AuthState


def _filter_button(label: str, value: str) -> rx.Component:
    return rx.button(
        label,
        size="2",
        variant=rx.cond(AppState.status_filter == value, "solid", "soft"),
        on_click=lambda: AppState.set_status_filter(value),
    )


def _stat_card(label: str, value: rx.Var, color: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(label, size="1", color="var(--gray-11)", weight="medium"),
            rx.heading(value.to_string(), size="6", color=color, weight="bold"),
            spacing="1",
            align="start",
        ),
        flex="1",
    )


def _empty_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon("inbox", size=48, color="var(--gray-8)"),
            rx.heading("No assignments yet", size="4", weight="medium"),
            rx.text(
                "Connect Canvas or upload a syllabus to get started.",
                color="var(--gray-11)",
                size="2",
            ),
            rx.hstack(
                rx.link(
                    rx.button("Connect Canvas", size="2"),
                    href="/settings",
                ),
                spacing="2",
            ),
            spacing="3",
            align="center",
            padding_y="10",
        ),
        width="100%",
    )


@rx.page(
    route="/dashboard",
    title="Taskify — Dashboard",
    on_load=[AuthState.check_auth, AppState.load_all],
)
def dashboard_page() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.vstack(
                        rx.heading("Your work", size="7", weight="bold"),
                        rx.text(
                            "Everything due, in one place.",
                            color="var(--gray-11)",
                            size="2",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.spacer(),
                    width="100%",
                ),
                # Stats
                rx.hstack(
                    _stat_card("To do", AppState.todo_count, "var(--blue-11)"),
                    _stat_card("Done", AppState.done_count, "var(--green-11)"),
                    _stat_card(
                        "Total", AppState.assignments.length(), "var(--gray-12)"
                    ),
                    spacing="3",
                    width="100%",
                ),
                # Sync bar
                sync_status(),
                # Two-column layout: assignments + calendar
                rx.grid(
                    # Left column: assignments
                    rx.vstack(
                        rx.hstack(
                            rx.heading("Assignments", size="4", weight="medium"),
                            rx.spacer(),
                            _filter_button("All", "all"),
                            _filter_button("To do", "todo"),
                            _filter_button("In progress", "in_progress"),
                            _filter_button("Done", "done"),
                            spacing="2",
                            align="center",
                            width="100%",
                        ),
                        rx.cond(
                            AppState.is_loading,
                            rx.center(rx.spinner(size="3"), padding_y="6"),
                            rx.cond(
                                AppState.has_assignments,
                                rx.vstack(
                                    rx.foreach(
                                        AppState.filtered_assignments,
                                        assignment_card,
                                    ),
                                    spacing="2",
                                    width="100%",
                                ),
                                _empty_state(),
                            ),
                        ),
                        spacing="3",
                        align="start",
                        width="100%",
                    ),
                    # Right column: calendar
                    rx.box(
                        calendar_widget(),
                    ),
                    columns="2fr 1fr",
                    gap="4",
                    width="100%",
                ),
                spacing="5",
                width="100%",
                padding_y="5",
            ),
            max_width="1100px",
            padding_x="4",
        ),
        width="100%",
        min_height="100vh",
    )
