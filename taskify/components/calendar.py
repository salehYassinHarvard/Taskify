"""
Compact upcoming-calendar widget for the dashboard sidebar.

Renders the next N Google Calendar events that have been cached into
Supabase via the /api/calendar/events route.
"""

import reflex as rx

from taskify.state.app_state import AppState


def _event_row(e: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.box(
            width="3px",
            height="40px",
            bg="var(--accent-9)",
            border_radius="2px",
        ),
        rx.vstack(
            rx.text(
                e["summary"],
                size="2",
                weight="medium",
                no_of_lines=1,
            ),
            rx.text(
                e["start_at"],
                size="1",
                color="var(--gray-11)",
            ),
            spacing="0",
            align="start",
            flex="1",
        ),
        width="100%",
        spacing="3",
        align="center",
        padding_y="2",
    )


def calendar_widget() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("calendar-days", size=16),
                rx.heading("Upcoming", size="3", weight="medium"),
                spacing="2",
                align="center",
            ),
            rx.divider(),
            rx.cond(
                AppState.calendar_events.length() > 0,
                rx.vstack(
                    rx.foreach(
                        AppState.calendar_events[:8],
                        _event_row,
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.icon(
                        "calendar-x",
                        size=28,
                        color="var(--gray-9)",
                    ),
                    rx.text(
                        "No upcoming events.",
                        size="2",
                        color="var(--gray-10)",
                    ),
                    spacing="2",
                    align="center",
                    padding_y="4",
                ),
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        width="100%",
    )
