from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.core.application.services.refresh_session_factory import (
    create_refresh_token_session,
)
from backend.core.domain.exceptions.refresh_session import DuplicateRefreshTokenFamily
from backend.core.domain.repositories.refresh_token_session_repository import (
    RefreshTokenSessionRepositoryContract,
)
from backend.core.domain.services.refresh_token_jti_hasher import hash_refresh_token_jti
from backend.core.domain.value_objects import UserId
from backend.core.domain.value_objects.refresh_session import (
    RefreshSessionRevocationReason,
    RefreshTokenIdHash,
)


class RefreshTokenSessionRepositoryContractSuite:
    """Shared contract expectations for in-memory and PostgreSQL repositories."""

    @pytest.fixture()
    def repository(self) -> RefreshTokenSessionRepositoryContract:
        raise NotImplementedError

    @pytest.fixture()
    def user_id(self) -> UserId:
        return UserId(value=uuid4())

    def test_add_and_retrieve(
        self,
        repository: RefreshTokenSessionRepositoryContract,
        user_id: UserId,
    ) -> None:
        now = datetime.now(UTC)
        session, _ = create_refresh_token_session(
            user_id=user_id,
            now=now,
            sliding_ttl_seconds=3600,
            absolute_ttl_seconds=7200,
        )
        repository.add(session)
        loaded = repository.get_by_id(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.current_token_id_hash == session.current_token_id_hash

    def test_duplicate_family_rejected(
        self,
        repository: RefreshTokenSessionRepositoryContract,
        user_id: UserId,
    ) -> None:
        now = datetime.now(UTC)
        session, _ = create_refresh_token_session(
            user_id=user_id,
            now=now,
            sliding_ttl_seconds=3600,
            absolute_ttl_seconds=7200,
        )
        repository.add(session)
        duplicate_family, _ = create_refresh_token_session(
            user_id=user_id,
            now=now,
            sliding_ttl_seconds=3600,
            absolute_ttl_seconds=7200,
        )
        duplicate_family = duplicate_family.model_copy(
            update={"family_id": session.family_id}
        )
        with pytest.raises(DuplicateRefreshTokenFamily):
            repository.add(duplicate_family)

    def test_rotate_with_expected_hash(
        self,
        repository: RefreshTokenSessionRepositoryContract,
        user_id: UserId,
    ) -> None:
        now = datetime.now(UTC)
        session, _ = create_refresh_token_session(
            user_id=user_id,
            now=now,
            sliding_ttl_seconds=3600,
            absolute_ttl_seconds=7200,
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
        loaded = repository.get_by_id(session.session_id)
        assert loaded is not None
        assert loaded.current_token_id_hash == new_hash
        assert loaded.previous_token_id_hash == session.current_token_id_hash

    def test_rotate_with_stale_hash_fails(
        self,
        repository: RefreshTokenSessionRepositoryContract,
        user_id: UserId,
    ) -> None:
        now = datetime.now(UTC)
        session, _ = create_refresh_token_session(
            user_id=user_id,
            now=now,
            sliding_ttl_seconds=3600,
            absolute_ttl_seconds=7200,
        )
        repository.add(session)
        stale = RefreshTokenIdHash(value=hash_refresh_token_jti("stale-jti"))
        assert not repository.rotate(
            session.session_id,
            expected_token_id_hash=stale,
            new_token_id_hash=RefreshTokenIdHash(
                value=hash_refresh_token_jti(str(uuid4()))
            ),
            rotated_at=now + timedelta(seconds=1),
            expires_at=now + timedelta(seconds=3600),
        )

    def test_revoke_and_revoke_twice(
        self,
        repository: RefreshTokenSessionRepositoryContract,
        user_id: UserId,
    ) -> None:
        now = datetime.now(UTC)
        session, _ = create_refresh_token_session(
            user_id=user_id,
            now=now,
            sliding_ttl_seconds=3600,
            absolute_ttl_seconds=7200,
        )
        repository.add(session)
        repository.revoke(
            session.session_id,
            revoked_at=now,
            reason=RefreshSessionRevocationReason.LOGOUT,
        )
        loaded = repository.get_by_id(session.session_id)
        assert loaded is not None
        assert loaded.is_revoked()
        repository.revoke(
            session.session_id,
            revoked_at=now + timedelta(seconds=1),
            reason=RefreshSessionRevocationReason.LOGOUT,
        )
        assert repository.get_by_id(session.session_id).is_revoked()

    def test_revoke_all_for_user(
        self,
        repository: RefreshTokenSessionRepositoryContract,
        user_id: UserId,
    ) -> None:
        now = datetime.now(UTC)
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
        other, _ = create_refresh_token_session(
            user_id=UserId(value=uuid4()),
            now=now,
            sliding_ttl_seconds=3600,
            absolute_ttl_seconds=7200,
        )
        repository.add(first)
        repository.add(second)
        repository.add(other)
        changed = repository.revoke_all_for_user(
            user_id,
            revoked_at=now,
            reason=RefreshSessionRevocationReason.USER_DEACTIVATED,
        )
        assert changed == 2
        assert repository.get_by_id(first.session_id).is_revoked()
        assert not repository.get_by_id(other.session_id).is_revoked()
