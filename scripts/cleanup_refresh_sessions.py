#!/usr/bin/env python3
"""Delete expired or long-revoked refresh-token sessions past the retention window.

Does not print token hashes or raw tokens. Use --dry-run to report counts only.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta

from backend.bootstrap.container import create_container
from backend.bootstrap.settings import load_settings
from backend.core.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SQLAlchemyUnitOfWork,
)

DEFAULT_RETENTION_DAYS = 30


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--retention-days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help="Retain revoked/expired sessions for this many days (default: 30).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many sessions would be deleted without deleting them.",
    )
    args = parser.parse_args(argv)

    if args.retention_days < 1:
        print("retention-days must be >= 1", file=sys.stderr)
        return 2

    settings = load_settings()
    if not settings.database_url:
        print("DATABASE_URL is required.", file=sys.stderr)
        return 2

    container = create_container(settings)
    try:
        if container.session_factory is None:
            print("Database session factory is unavailable.", file=sys.stderr)
            return 2
        cutoff = datetime.now(UTC) - timedelta(days=args.retention_days)
        with SQLAlchemyUnitOfWork(container.session_factory) as unit_of_work:
            if args.dry_run:
                # Count without deleting by scanning through repository delete path
                # would mutate; perform a dry estimate via rotate-safe delete preview.
                from sqlalchemy import and_, func, or_, select

                from backend.core.infrastructure.persistence.sqlalchemy.models.refresh_token_session_model import (
                    RefreshTokenSessionModel,
                )

                statement = select(func.count()).select_from(RefreshTokenSessionModel).where(
                    or_(
                        and_(
                            RefreshTokenSessionModel.revoked_at.is_not(None),
                            RefreshTokenSessionModel.revoked_at < cutoff,
                        ),
                        and_(
                            RefreshTokenSessionModel.revoked_at.is_(None),
                            RefreshTokenSessionModel.expires_at < cutoff,
                            RefreshTokenSessionModel.absolute_expires_at < cutoff,
                        ),
                    )
                )
                count = int(unit_of_work.session.scalar(statement) or 0)
                print(f"dry_run=true deletable_sessions={count}")
                return 0

            deleted = unit_of_work.refresh_sessions.delete_expired_before(cutoff)
            unit_of_work.commit()
            print(f"dry_run=false deleted_sessions={deleted}")
            return 0
    except Exception as error:  # noqa: BLE001 — CLI surface
        print(f"cleanup_failed error_type={type(error).__name__}", file=sys.stderr)
        return 1
    finally:
        container.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
