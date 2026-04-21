"""Top navbar used on dashboard / settings."""

import reflex as rx

from taskify.state.auth_state import AuthState


def navbar() -> rx.Component:
    return rx.hstack(
        # Brand
        rx.link(
            rx.hstack(
                rx.icon("book-open-check", size=22, color="var(--accent-9)"),
                rx.heading("Taskify", size="5", weight="bold"),
                align="center",
                spacing="2",
            ),
            href="/dashboard",
            text_decoration="none",
            color="inherit",
        ),
        rx.spacer(),
        # Nav links
        rx.hstack(
            rx.link(
                rx.button("Dashboard", variant="ghost", size="2"),
                href="/dashboard",
            ),
            rx.link(
                rx.button("Settings", variant="ghost", size="2"),
                href="/settings",
            ),
            spacing="2",
        ),
        # User menu
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.cond(
                        AuthState.avatar_url != "",
                        rx.avatar(src=AuthState.avatar_url, size="2"),
                        rx.avatar(fallback="?", size="2"),
                    ),
                    variant="ghost",
                    padding="2",
                ),
            ),
            rx.menu.content(
                rx.menu.item(
                    rx.vstack(
                        rx.text(AuthState.user_name, weight="medium", size="2"),
                        rx.text(
                            AuthState.user_email,
                            size="1",
                            color="var(--gray-11)",
                        ),
                        spacing="0",
                        align="start",
                    ),
                    disabled=True,
                ),
                rx.menu.separator(),
                rx.menu.item("Settings", on_click=rx.redirect("/settings")),
                rx.menu.item(
                    "Sign out",
                    color="red",
                    on_click=AuthState.logout,
                ),
            ),
        ),
        width="100%",
        padding_x="6",
        padding_y="3",
        border_bottom="1px solid var(--gray-4)",
        bg="var(--color-background)",
        position="sticky",
        top="0",
        z_index="100",
        align="center",
    )
