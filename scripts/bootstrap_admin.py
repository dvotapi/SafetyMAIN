"""One-shot production identity bootstrap.

Creates the first organization, the first user, and an ACTIVE admin membership
so that an operator can log in. Every later user must be created through the
administrative API (`POST /api/v1/admin/users`) by an authenticated admin.

The script refuses to run when any user already exists: it exists solely to
break the chicken-and-egg situation of an empty production database.

No administrative audit event is recorded, because audit requires an acting
principal and none exists before the first user. This is the single documented
exception; it is why the script is one-shot and refuses a non-empty database.

Usage (inside the backend image, with DATABASE_URL set):

    python -m scripts.bootstrap_admin \
        --email admin@example.com \
        --display-name "Platform Admin" \
        --organization "Example Corp" \
        --password-file /run/secrets/bootstrap-admin-password

The password is read from a file (or from BOOTSTRAP_ADMIN_PASSWORD) and is
never accepted as a command-line argument, so it does not leak into the process
list or shell history.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from backend.core.domain.entities.membership import Membership, MembershipStatus
from backend.core.domain.entities.organization import (
    Organization,
    OrganizationStatus,
    normalized_organization_name_key,
)
from backend.core.domain.entities.user import User, UserStatus
from backend.core.domain.value_objects import MembershipId, OrganizationId, Role, UserId
from backend.core.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from backend.core.infrastructure.auth.sqlalchemy_identity_adapter import (
    SQLAlchemyIdentityAdapter,
)
from backend.core.infrastructure.persistence.sqlalchemy.engine import (
    create_engine,
    create_session_factory,
)
from backend.core.infrastructure.persistence.sqlalchemy.models.user_model import (
    UserModel,
)
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)

MIN_PASSWORD_LENGTH = 12


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--organization", required=True)
    parser.add_argument(
        "--password-file",
        help="File holding the initial password. Falls back to BOOTSTRAP_ADMIN_PASSWORD.",
    )
    return parser.parse_args(argv)


def _read_password(password_file: str | None) -> str:
    if password_file:
        password = Path(password_file).read_text(encoding="utf-8").strip()
    else:
        password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "").strip()

    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(
            f"Initial password must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    return password


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    password = _read_password(args.password_file)

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise SystemExit("DATABASE_URL must be set.")

    engine = create_engine(database_url)
    session_factory = create_session_factory(engine)
    now = datetime.now(UTC)

    with SQLAlchemyUnitOfWork(session_factory) as unit_of_work:
        existing_users = unit_of_work.session.query(UserModel).count()
        if existing_users:
            raise SystemExit(
                f"Refusing to bootstrap: {existing_users} user(s) already exist. "
                "Create further users through the administrative API."
            )

        organization = unit_of_work.organizations.get_by_normalized_name(
            normalized_organization_name_key(args.organization)
        )
        if organization is None:
            organization = Organization(
                id=OrganizationId(value=uuid4()),
                name=args.organization,
                status=OrganizationStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
            unit_of_work.organizations.add(organization)
            unit_of_work.commit()
            created_organization = True
        else:
            created_organization = False

    user = User(
        id=UserId(value=uuid4()),
        display_name=args.display_name,
        email=args.email,
        status=UserStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )
    identity = SQLAlchemyIdentityAdapter(session_factory)
    identity.register_user(user, BcryptPasswordHasher().hash_password(password))

    with SQLAlchemyUnitOfWork(session_factory) as unit_of_work:
        unit_of_work.memberships.add(
            Membership(
                id=MembershipId(value=uuid4()),
                user_id=user.id,
                organization_id=organization.id,
                status=MembershipStatus.ACTIVE,
                role=Role.admin(),
                joined_at=now,
                updated_at=now,
            )
        )
        unit_of_work.commit()

    print(f"organization_id={organization.id.value} created={created_organization}")
    print(f"user_id={user.id.value} email={user.email} role=admin")
    print("Bootstrap complete. Keep the initial password in the operator secret store.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
