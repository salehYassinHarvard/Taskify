"""Login page + OAuth callback page."""

import reflex as rx

from taskify.state.auth_state import AuthState


# ---------------------------------------------------------------------------
# Login page
# ---------------------------------------------------------------------------

@rx.page(route="/login", title="Taskify — Sign In")
def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Taskify", size="8", weight="bold", trim="both"),
            rx.text(
                "Your assignments. Your calendar. One place.",
                color="var(--gray-11)",
                size="3",
            ),
            rx.card(
                rx.vstack(
                    rx.text("Sign in to get started", size="4", weight="medium"),
                    rx.button(
                        rx.icon("chrome", size=18),
                        "Continue with Google",
                        size="3",
                        variant="solid",
                        width="100%",
                        on_click=AuthState.start_google_login,
                        loading=AuthState.is_loading,
                    ),
                    rx.cond(
                        AuthState.auth_error != "",
                        rx.callout(
                            AuthState.auth_error,
                            icon="triangle_alert",
                            color_scheme="red",
                            width="100%",
                        ),
                    ),
                    spacing="4",
                    width="100%",
                    align="center",
                ),
                width="360px",
            ),
            rx.text(
                "By signing in you agree to our Terms of Service.",
                size="1",
                color="var(--gray-9)",
            ),
            spacing="5",
            align="center",
            padding_y="10vh",
        ),
        width="100%",
        min_height="100vh",
    )


# ---------------------------------------------------------------------------
# OAuth callback page  (/auth/callback)
#
# Supabase redirects here with tokens in the URL fragment:
#   /auth/callback#access_token=...&refresh_token=...&...
#
# We run a tiny JS snippet on mount that parses the fragment and calls
# AuthState.finish_oauth with the parsed dict.
# ---------------------------------------------------------------------------

_PARSE_HASH_JS = """
(() => {
    const hash = window.location.hash.slice(1);
    if (!hash) return {};
    return Object.fromEntries(new URLSearchParams(hash));
})()
"""


@rx.page(route="/auth/callback", title="Signing in…")
def auth_callback_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Completing sign-in…", size="3", color="var(--gray-11)"),
            rx.cond(
                AuthState.auth_error != "",
                rx.callout(
                    AuthState.auth_error,
                    icon="triangle_alert",
                    color_scheme="red",
                ),
            ),
            spacing="4",
            align="center",
        ),
        width="100%",
        min_height="100vh",
        on_mount=rx.call_script(
            _PARSE_HASH_JS,
            callback=AuthState.handle_oauth_callback,
        ),
    )
