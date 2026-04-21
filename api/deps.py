"""
Shared FastAPI dependencies.

The main one is `current_user_id` — it reads the Supabase JWT from the
Authorization header and returns the user's uuid.
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from db.supabase import get_supabase_client


def current_user_id(
    authorization: str = Header(..., alias="Authorization"),
) -> str:
    """Validate the Bearer token via Supabase and return the user uuid."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    token = authorization.split(" ", 1)[1]
    try:
        sb = get_supabase_client()
        user_resp = sb.auth.get_user(token)
        user = user_resp.user
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}")

    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No user for token")
    return user.id


CurrentUser = Depends(current_user_id)
