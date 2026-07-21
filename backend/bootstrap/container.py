from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.bootstrap.settings import AppSettings
from backend.core.application.authorization.authorization_service import AuthorizationService
from backend.core.application.tenant.tenant_context_resolver import TenantContextResolver
from backend.core.contracts.password_hasher import PasswordHasherContract
from backend.core.contracts.token_service import TokenServiceContract
from backend.core.contracts.unit_of_work import UnitOfWorkContract
from backend.core.contracts.membership_lookup import MembershipLookupPort
from backend.core.contracts.membership_verification import MembershipVerificationPort
from backend.core.contracts.user_credentials import UserCredentialsPort
from backend.core.contracts.user_lookup import UserLookupPort
from backend.core.infrastructure.auth.bcrypt_password_hasher import create_password_hasher
from backend.core.infrastructure.auth.in_memory_identity_store import InMemoryIdentityStore
from backend.core.infrastructure.auth.in_memory_membership_store import InMemoryMembershipStore
from backend.core.infrastructure.auth.jwt_token_service import create_token_service
from backend.core.infrastructure.persistence.sqlalchemy.engine import (
    create_engine,
    create_session_factory,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)

UowFactory = Callable[[], UnitOfWorkContract]
ReadinessCheck = Callable[[], None]


@dataclass(slots=True)
class AppContainer:
    """Explicit composition root for production infrastructure wiring.

    Intentionally not a service locator: callers receive this object through
    application state / FastAPI dependencies rather than a hidden global.
    """

    settings: AppSettings
    engine: Engine | None
    session_factory: sessionmaker[Session] | None
    uow_factory: UowFactory
    readiness_check: ReadinessCheck
    user_lookup: UserLookupPort
    user_credentials: UserCredentialsPort
    password_hasher: PasswordHasherContract
    token_service: TokenServiceContract
    identity_store: InMemoryIdentityStore
    membership_lookup: MembershipLookupPort
    membership_verification: MembershipVerificationPort
    membership_store: InMemoryMembershipStore
    authorization_service: AuthorizationService
    tenant_context_resolver: TenantContextResolver

    def dispose(self) -> None:
        if self.engine is not None:
            self.engine.dispose()


def create_container(
    settings: AppSettings,
    *,
    identity_store: InMemoryIdentityStore | None = None,
    membership_store: InMemoryMembershipStore | None = None,
) -> AppContainer:
    """Assemble infrastructure dependencies without connecting to PostgreSQL.

    ``create_engine`` is lazy: no network I/O occurs until a connection is used.
    """

    engine: Engine | None = None
    session_factory: sessionmaker[Session] | None = None

    if settings.database_url:
        engine = create_engine(settings.database_url)
        session_factory = create_session_factory(engine)

    def uow_factory() -> UnitOfWorkContract:
        if session_factory is None:
            raise RuntimeError("Database is not configured.")
        return SQLAlchemyUnitOfWork(session_factory)

    def readiness_check() -> None:
        if engine is None:
            raise RuntimeError("Database is not configured.")
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    resolved_identity_store = identity_store or InMemoryIdentityStore()
    resolved_membership_store = membership_store or InMemoryMembershipStore()
    password_hasher = create_password_hasher()
    token_service = create_token_service(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_ttl_seconds=settings.jwt_access_token_ttl_seconds,
        refresh_token_ttl_seconds=settings.jwt_refresh_token_ttl_seconds,
        issuer=settings.jwt_issuer,
    )
    authorization_service = AuthorizationService(
        membership_verification=resolved_membership_store,
    )
    tenant_context_resolver = TenantContextResolver(
        resolved_membership_store,
        default_organization_id=settings.default_organization_id,
    )

    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        uow_factory=uow_factory,
        readiness_check=readiness_check,
        user_lookup=resolved_identity_store,
        user_credentials=resolved_identity_store,
        password_hasher=password_hasher,
        token_service=token_service,
        identity_store=resolved_identity_store,
        membership_lookup=resolved_membership_store,
        membership_verification=resolved_membership_store,
        membership_store=resolved_membership_store,
        authorization_service=authorization_service,
        tenant_context_resolver=tenant_context_resolver,
    )
