from __future__ import annotations

import hashlib


def hash_refresh_token_jti(jti: str) -> str:
    """Return a lowercase SHA-256 hex digest of a refresh-token jti.

    The raw jti must never be persisted or logged.
    """

    normalized = jti.strip()
    if not normalized:
        raise ValueError("Refresh token jti must not be empty.")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
