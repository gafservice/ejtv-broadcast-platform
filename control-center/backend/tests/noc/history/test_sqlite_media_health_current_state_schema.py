"""Schema contract for Media Health current state.

ENG-013C — Media Health Current State

This contract requires schema version 4 to introduce the
media_health_current_state table while preserving an existing
version-3 database.

All databases used here are temporary test databases.
"""

from __future__ import annotations

import sqlite3

from app.noc.history.sqlite_database import (
    SCHEMA_VERSION,
    SQLiteHistoryDatabase,
)


EXPECTED_COLUMNS = {
    "profile_id",
    "service_id",
    "path_name",
    "observed_at",
    "health_json",
}


def _table_names(database_path) -> set[str]:
    connection = sqlite3.connect(database_path)

    try:
        return {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            )
        }
    finally:
        connection.close()


def _columns(
    database_path,
    table_name: str,
) -> set[str]:
    connection = sqlite3.connect(database_path)

    try:
        return {
            row[1]
            for row in connection.execute(
                f"PRAGMA table_info({table_name})"
            )
        }
    finally:
        connection.close()


def _schema_version(database_path) -> int:
    connection = sqlite3.connect(database_path)

    try:
        row = connection.execute(
            """
            SELECT version
            FROM schema_version
            LIMIT 1
            """
        ).fetchone()

        assert row is not None
        return int(row[0])
    finally:
        connection.close()


def test_schema_version_is_four() -> None:
    assert SCHEMA_VERSION == 4


def test_new_database_contains_media_health_current_state(
    tmp_path,
) -> None:
    database_path = tmp_path / "new.db"

    database = SQLiteHistoryDatabase(database_path)
    database.initialize()

    assert _schema_version(database_path) == 4

    assert (
        "media_health_current_state"
        in _table_names(database_path)
    )

    assert _columns(
        database_path,
        "media_health_current_state",
    ) == EXPECTED_COLUMNS


def test_media_health_current_state_uses_full_identity_primary_key(
    tmp_path,
) -> None:
    database_path = tmp_path / "identity.db"

    database = SQLiteHistoryDatabase(database_path)
    database.initialize()

    connection = sqlite3.connect(database_path)

    try:
        rows = connection.execute(
            """
            PRAGMA table_info(media_health_current_state)
            """
        ).fetchall()
    finally:
        connection.close()

    primary_key = [
        row[1]
        for row in sorted(
            rows,
            key=lambda row: row[5],
        )
        if row[5] > 0
    ]

    assert primary_key == [
        "profile_id",
        "service_id",
        "path_name",
    ]


def test_version_three_database_migrates_to_four_without_data_loss(
    tmp_path,
) -> None:
    database_path = tmp_path / "migration.db"

    database = SQLiteHistoryDatabase(database_path)

    with database.connect() as connection:
        database._create_schema_version_table(
            connection
        )
        database._migrate_v1(connection)
        database._migrate_v2(connection)
        database._migrate_v3(connection)
        database._set_version(
            connection,
            3,
        )

        connection.execute(
            """
            INSERT INTO managed_history_scopes (
                node_id,
                instance_id,
                managed_since_day,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "node-1",
                "instance-1",
                "2026-09-23",
                "2026-09-23T12:00:00.000000+00:00",
            ),
        )

        connection.commit()

    assert _schema_version(database_path) == 3
    assert (
        "media_health_current_state"
        not in _table_names(database_path)
    )

    migrated = SQLiteHistoryDatabase(database_path)
    migrated.initialize()

    assert _schema_version(database_path) == 4

    tables = _table_names(database_path)

    assert "events" in tables
    assert "alarms" in tables
    assert "alarm_transitions" in tables
    assert "managed_history_scopes" in tables
    assert "node_health_diagnostics" in tables
    assert "media_health_current_state" in tables

    connection = sqlite3.connect(database_path)

    try:
        row = connection.execute(
            """
            SELECT
                node_id,
                instance_id,
                managed_since_day,
                created_at
            FROM managed_history_scopes
            WHERE node_id = ?
              AND instance_id = ?
            """,
            (
                "node-1",
                "instance-1",
            ),
        ).fetchone()
    finally:
        connection.close()

    assert row == (
        "node-1",
        "instance-1",
        "2026-09-23",
        "2026-09-23T12:00:00.000000+00:00",
    )


def test_reinitializing_version_four_database_is_idempotent(
    tmp_path,
) -> None:
    database_path = tmp_path / "idempotent.db"

    database = SQLiteHistoryDatabase(database_path)

    database.initialize()
    database.initialize()

    assert _schema_version(database_path) == 4

    assert (
        "media_health_current_state"
        in _table_names(database_path)
    )
