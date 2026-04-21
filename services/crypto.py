"""
Fernet symmetric encryption for storing third-party tokens (Canvas, Google).

Generate a key once:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
Store as FERNET_KEY env var in Railway / .env. NEVER commit it.
"""

from __future__ import annotations

import os
from functools import lru_cache

from cryptography.fernet import Fernet


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    key = os.environ["FERNET_KEY"]
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plaintext: str) -> str:
    """Encrypt a string, return URL-safe base64 token."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a Fernet token back to plaintext."""
    return _get_fernet().decrypt(token.encode()).decode()
