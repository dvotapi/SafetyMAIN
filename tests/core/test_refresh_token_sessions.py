from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.application.services.refresh_session_factory import (
    create_refresh_token_session,
)
from backend.core.domain.exceptions.refresh_session import DuplicateRefreshTokenFamily
from backend.core.domain.services.refresh_token_jti_hasher import hash_refresh_token_jti
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionRevocationReason,
    RefreshTokenIdHash,
)
from backend.core.infrastructure.persistence.in_memory.refresh_token_session_repository import (
    InMemoryRefreshTokenSessionRepository,
)


def test_hash_refresh_token_jti_is_sha256_hex() -> None:
    digest = hash_refresh_token_jti("opaque-jti-value")
    assert digest == RefreshTokenIdHash(value=digest).value
    assert len(digest) == 64


def test_in_memory_refresh_session_rotate_and_reuse() -> None:
    repository = InMemoryRefreshTokenSessionRepository()
    now = datetime.now(UTC)
    session, _ = create_refresh_token_session(
        user_id=UserId(value=uuid4()),
        now=now,
        sliding_ttl_seconds=3600,
        absolute_ttl_seconds=7200,
        jti=str(uuid4()),
    )
    repository.add(session)
    new_hash = RefreshTokenIdHash(value=hash_refresh_token_jti(str(uuid4())))
    assert repository.rotate(
        session.session_id,
        expected_token_id_hash=session.current_token_id_hash,
        new_token_id_hash=new_hash,
        rotated_at=now + timedelta(seconds=1),
        expires_at=now + timedelta(seconds=3600),
    )
    assert not repository.rotate(
        session.session_id,
        expected_token_id_hash=session.current_token_id_hash,
        new_token_id_hash=RefreshTokenIdHash(value=hash_refresh_token_jti(str(uuid4()))),
        rotated_at=now + timedelta(seconds=2),
        expires_at=now + timedelta(seconds=3600),
    )


def test_in_memory_refresh_session_revoke_all_for_user() -> None:
    repository = InMemoryRefreshTokenSessionRepository()
    now = datetime.now(UTC)
    user_id = UserId(value=uuid4())
    first, _ = create_refresh_token_session(
        user_id=user_id,
        now=now,
        sliding_ttl_seconds=3600,
        absolute_ttl_seconds=7200,
    )
    second, _ = create_refresh_token_session(
        user_id=user_id,
        now=now,
        sliding_ttl_seconds=3600,
        absolute_ttl_seconds=7200,
    )
    repository.add(first)
    repository.add(second)
    changed = repository.revoke_all_for_user(
        user_id,
        revoked_at=now,
        reason=RefreshSessionRevocationReason.USER_DEACTIVATED,
    )
    assert changed == 2
    assert repository.get_by_id(first.session_id).is_revoked()


def test_in_memory_refresh_session_rejects_duplicate_family() -> None:
    repository = InMemoryRefreshTokenSessionRepository()
    now = datetime.now(UTC)
    session, _ = create_refresh_token_session(
        user_id=UserId(value=uuid4()),
        now=now,
        sliding_ttl_seconds=3600,
        absolute_ttl_seconds=7200,
    )
    repository.add(session)
    duplicate, _ = create_refresh_token_session(
        user_id=UserId(value=uuid4()),
        now=now,
        sliding_ttl_seconds=3600,
        absolute_ttl_seconds=7200,
    )
    duplicate = duplicate.model_copy(update={"family_id": session.family_id})
    with pytest.raises(DuplicateRefreshTokenFamily):
        repository.add(duplicate)
