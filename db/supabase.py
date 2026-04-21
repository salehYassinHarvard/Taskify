"""
Supabase client singleton.

Usage:
    from db.supabase import get_supabase_client
    sb = get_supabase_client()
    sb.table("profiles").select("*").execute()
"""

from __future__ import annotations

import os
from functools import lru_cache

from supabase import create_client, Client


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client using the service-role key (bypasses RLS)."""
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def get_supabase_client_anon() -> Client:
    """Return a Supabase client using the anon/public key (RLS-aware)."""
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_ANON_KEY"]
    return create_client(url, key)
