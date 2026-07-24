from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command


@pytest.mark.db
def test_migration_0007_backfills_audit_integrity_chain() -> None:
    if os.environ.get("SAFETYMAIN_RUN_DB_TESTS") != "1":
        pytest.skip("Set SAFETYMAIN_RUN_DB_TESTS=1 to run database migration tests.")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for database migration tests.")

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    engine = create_engine(database_url)

    command.downgrade(config, "base")
    command.upgrade(config, "0006_audit_investigation_indexes")

    org_a = uuid4()
    org_b = uuid4()
    event_a1 = uuid4()
    event_a2 = uuid4()
    event_b1 = uuid4()
    t1 = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    t2 = t1 + timedelta(seconds=1)

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO audit_events (
                    id,
                    actor_user_id,
                    authorization_organization_id,
                    target_organization_id,
                    action,
                    resource_type,
                    resource_id,
                    outcome,
                    failure_code,
                    metadata,
                    occurred_at
                ) VALUES
                (
                    :a1, :actor, :org_a, NULL, 'user.create', 'USER', :resource,
                    'SUCCESS', NULL, '{}'::jsonb, :t1
                ),
                (
                    :a2, :actor, :org_a, NULL, 'user.update', 'USER', :resource,
                    'SUCCESS', NULL, '{"request_id":"r2"}'::jsonb, :t2
                ),
                (
                    :b1, :actor, :org_b, NULL, 'user.create', 'USER', :resource,
                    'SUCCESS', NULL, '{}'::jsonb, :t1
                )
                """
            ),
            {
                "a1": event_a1,
                "a2": event_a2,
                "b1": event_b1,
                "actor": uuid4(),
                "org_a": org_a,
                "org_b": org_b,
                "resource": uuid4(),
                "t1": t1,
                "t2": t2,
            },
        )

    command.upgrade(config, "0007_audit_event_integrity_chain")

    inspector = inspect(engine)
    assert "audit_chain_heads" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("audit_events")}
    assert {
        "previous_integrity_hash",
        "integrity_hash",
        "integrity_version",
    }.issubset(columns)
    index_names = {index["name"] for index in inspector.get_indexes("audit_events")}
    assert "ix_audit_events_action_occurred_at" in index_names

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT id, previous_integrity_hash, integrity_hash, integrity_version
                FROM audit_events
                ORDER BY occurred_at ASC, id ASC
                """
            )
        ).mappings().all()
        assert len(rows) == 3
        assert all(row["integrity_hash"] and len(row["integrity_hash"]) == 64 for row in rows)
        assert all(row["integrity_version"] == 1 for row in rows)

        org_a_ordered = connection.execute(
            text(
                """
                SELECT id, previous_integrity_hash, integrity_hash
                FROM audit_events
                WHERE authorization_organization_id = :org
                ORDER BY occurred_at ASC, id ASC
                """
            ),
            {"org": org_a},
        ).mappings().all()
        assert org_a_ordered[0]["previous_integrity_hash"] is None
        assert (
            org_a_ordered[1]["previous_integrity_hash"]
            == org_a_ordered[0]["integrity_hash"]
        )

        org_b_ordered = connection.execute(
            text(
                """
                SELECT id, previous_integrity_hash, integrity_hash
                FROM audit_events
                WHERE authorization_organization_id = :org
                ORDER BY occurred_at ASC, id ASC
                """
            ),
            {"org": org_b},
        ).mappings().all()
        assert org_b_ordered[0]["previous_integrity_hash"] is None
        assert org_b_ordered[0]["integrity_hash"] != org_a_ordered[0]["integrity_hash"]

        heads = connection.execute(
            text(
                """
                SELECT organization_id, latest_audit_event_id, latest_integrity_hash
                FROM audit_chain_heads
                ORDER BY organization_id
                """
            )
        ).mappings().all()
        assert len(heads) == 2

    # Downgrade removes integrity information (destructive).
    command.downgrade(config, "0006_audit_investigation_indexes")
    inspector = inspect(engine)
    assert "audit_chain_heads" not in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("audit_events")}
    assert "integrity_hash" not in columns

    command.downgrade(config, "base")
    engine.dispose()
