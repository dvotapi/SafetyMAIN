from __future__ import annotations

import hashlib
import secrets


def generate_invitation_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = hash_invitation_token(token)
    return token, token_hash


def hash_invitation_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_invitation_token(token: str, token_hash: str) -> bool:
    candidate = hash_invitation_token(token)
    return secrets.compare_digest(candidate, token_hash)
