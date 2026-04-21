"""
Google Calendar client.

Uses the Google access token that Supabase already collected during the
Google OAuth sign-in (provider_token on the Supabase session).

We ask for the 'calendar' scope in the Supabase Auth provider config, so
the same sign-in covers both login and calendar access.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _service_from_token(access_token: str, refresh_token: str = ""):
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token or None,
        client_id=None,
        client_secret=None,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=CALENDAR_SCOPES,
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def list_upcoming_events(
    access_token: str,
    refresh_token: str = "",
    max_results: int = 50,
    calendar_id: str = "primary",
) -> list[dict[str, Any]]:
    """Return a list of upcoming events as Google Calendar API dicts."""
    service = _service_from_token(access_token, refresh_token)
    now = datetime.now(timezone.utc).isoformat()
    try:
        r = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return r.get("items", [])
    except HttpError as e:
        raise RuntimeError(f"Google Calendar API error: {e}") from e


def create_event(
    access_token: str,
    *,
    summary: str,
    start: datetime,
    end: datetime,
    description: str = "",
    refresh_token: str = "",
    calendar_id: str = "primary",
) -> dict[str, Any]:
    """Create a single calendar event, return the created event object."""
    service = _service_from_token(access_token, refresh_token)
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
    }
    try:
        return (
            service.events()
            .insert(calendarId=calendar_id, body=body)
            .execute()
        )
    except HttpError as e:
        raise RuntimeError(f"Google Calendar API error: {e}") from e


def delete_event(
    access_token: str,
    event_id: str,
    refresh_token: str = "",
    calendar_id: str = "primary",
) -> None:
    service = _service_from_token(access_token, refresh_token)
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    except HttpError as e:
        # 410 = already gone, treat as success
        if e.resp.status in (404, 410):
            return
        raise RuntimeError(f"Google Calendar API error: {e}") from e
