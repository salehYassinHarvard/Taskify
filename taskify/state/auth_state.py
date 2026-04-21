"""
Auth state — handles Supabase Google OAuth flow.

Flow:
  1. User clicks "Sign in with Google" on /login
  2. We call supabase.auth.sign_in_with_oauth(provider="google") which returns a URL
  3. User is redirected to Google consent screen
  4. Supabase handles the callback, sets a session, redirects to our app
  5. On landing back, we read the session from the URL fragment (#access_token=...)
     via a client-side event handler and store it in state
"""

from __future__ import annotations

import os
from typing import Optional

import reflex as rx

from db.supabase import get_supabase_client


class AuthState(rx.State):
    """Manages user authentication via Supabase + Google OAuth."""

    # Session data
    access_token: str = ""
    refresh_token: str = ""
    user_id: str = ""
    user_email: str = ""
    user_name: str = ""
    avatar_url: str = ""

    # UI flags
    is_loading: bool = False
    auth_error: str = ""

    @rx.var
    def is_authenticated(self) -> bool:
        return bool(self.access_token and self.user_id)

    def start_google_login(self):
        """Redirect user to Supabase's Google OAuth consent screen."""
        self.is_loading = True
        self.auth_error = ""

        supabase_url = os.environ["SUPABASE_URL"]
        redirect_to = os.getenv("AUTH_REDIRECT_URL", "http://localhost:3000/auth/callback")

        # Build the OAuth URL that Supabase provides
        oauth_url = (
            f"{supabase_url}/auth/v1/authorize"
            f"?provider=google"
            f"&redirect_to={redirect_to}"
        )

        return rx.redirect(oauth_url)

    def handle_oauth_callback(self, token_data: dict):
        """Called from the client after Supabase redirects back with tokens in the URL fragment.

        token_data should contain: access_token, refresh_token, etc.
        parsed from the URL hash on the client side.
        """
        self.is_loading = True
        self.auth_error = ""

        access_token = token_data.get("access_token", "")
        refresh_token = token_data.get("refresh_token", "")

        if not access_token:
            self.auth_error = "No access token received from Google."
            self.is_loading = False
            return

        try:
            sb = get_supabase_client()
            # Verify the token and get user info
            user_response = sb.auth.get_user(access_token)
            user = user_response.user

            if user is None:
                self.auth_error = "Could not verify session."
                self.is_loading = False
                return

            self.access_token = access_token
            self.refresh_token = refresh_token
            self.user_id = user.id
            self.user_email = user.email or ""
            self.user_name = (
                user.user_metadata.get("full_name", "")
                or user.user_metadata.get("name", "")
            )
            self.avatar_url = user.user_metadata.get("avatar_url", "")

            # Upsert a profile row so downstream queries work
            sb.table("profiles").upsert(
                {
                    "id": user.id,
                    "email": self.user_email,
                    "display_name": self.user_name,
                    "avatar_url": self.avatar_url,
                },
                on_conflict="id",
            ).execute()

            self.is_loading = False
            return rx.redirect("/dashboard")

        except Exception as e:
            self.auth_error = f"Login failed: {e}"
            self.is_loading = False

    def logout(self):
        """Clear local state. Supabase session is stateless JWT so no server call needed."""
        self.access_token = ""
        self.refresh_token = ""
        self.user_id = ""
        self.user_email = ""
        self.user_name = ""
        self.avatar_url = ""
        self.auth_error = ""
        return rx.redirect("/login")

    def check_auth(self):
        """Route guard — redirect to /login if not authenticated."""
        if not self.is_authenticated:
            return rx.redirect("/login")
