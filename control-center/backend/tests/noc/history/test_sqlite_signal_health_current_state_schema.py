"""Schema contract for Signal Health current state.

ENG-013C — Signal Health Current State

Schema version 5 introduces signal_health_current_state while
preserving an existing version-4 database and its Media Health
current-state data.

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
    "health_since",
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


def test_current_schema_version_is_six() -> None:
    assert SCHEMA_VERSION == 6


def test_new_database_contains_signal_health_current_state(
    tmp_path,
) -> None:
    database_path = tmp_path / "new.db"

    database = SQLiteHistoryDatabase(database_path)
    database.initialize()

    assert _schema_version(database_path) == 6
    assert (
        "signal_health_current_state"
        in _table_names(database_path)
    )
    assert _columns(
        database_path,
        "signal_health_current_state",
    ) == EXPECTED_COLUMNS


def test_signal_health_current_state_uses_full_identity_primary_key(
    tmp_path,
) -> None:
    database_path = tmp_path / "identity.db"

    database = SQLiteHistoryDatabase(database_path)
    database.initialize()

    connection = sqlite3.connect(database_path)

    try:
        rows = connection.execute(
            """
            PRAGMA table_info(signal_health_current_state)
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


def test_version_four_database_migrates_to_current_without_data_loss(
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
        database._migrate_v4(connection)
        database._set_version(
            connection,
            4,
        )

        connection.execute(
            """
            INSERT INTO media_health_current_state (
                profile_id,
                service_id,
                path_name,
                observed_at,
                health_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "profile-enlace",
                "enlace",
                "enlace",
                "2026-10-06T12:00:00.000000+00:00",
                "{\"preserved\":true}",
            ),
        )

        connection.commit()

    assert _schema_version(database_path) == 4
    assert (
        "signal_health_current_state"
        not in _table_names(database_path)
    )

    migrated = SQLiteHistoryDatabase(database_path)
    migrated.initialize()

    assert _schema_version(database_path) == 6

    tables = _table_names(database_path)

    assert "events" in tables
    assert "alarms" in tables
    assert "alarm_transitions" in tables
    assert "node_health_diagnostics" in tables
    assert "managed_history_scopes" in tables
    assert "media_health_current_state" in tables
    assert "signal_health_current_state" in tables

    connection = sqlite3.connect(database_path)

    try:
        row = connection.execute(
            """
            SELECT
                profile_id,
                service_id,
                path_name,
                observed_at,
                health_json
            FROM media_health_current_state
            WHERE profile_id = ?
              AND service_id = ?
              AND path_name = ?
            """,
            (
                "profile-enlace",
                "enlace",
                "enlace",
            ),
        ).fetchone()
    finally:
        connection.close()

    assert row == (
        "profile-enlace",
        "enlace",
        "enlace",
        "2026-10-06T12:00:00.000000+00:00",
        "{\"preserved\":true}",
    )


def test_reinitializing_current_database_is_idempotent(
    tmp_path,
) -> None:
    database_path = tmp_path / "idempotent.db"

    database = SQLiteHistoryDatabase(database_path)
    database.initialize()
    database.initialize()

    assert _schema_version(database_path) == 6
    assert (
        "media_health_current_state"
        in _table_names(database_path)
    )
    assert (
        "signal_health_current_state"
        in _table_names(database_path)
    )

# ENG-013C 235E.23 — Health Since schema v6 contract.

def test_schema_version_is_six() -> None:
    assert SCHEMA_VERSION == 6


def test_new_database_contains_nullable_health_since(
    tmp_path,
) -> None:
    database_path = tmp_path / "health-since-new.db"

    database = SQLiteHistoryDatabase(database_path)
    database.initialize()

    assert _schema_version(database_path) == 6

    connection = sqlite3.connect(database_path)

    try:
        columns = {
            row[1]: row
            for row in connection.execute(
                """
                PRAGMA table_info(
                    signal_health_current_state
                )
                """
            )
        }
    finally:
        connection.close()

    assert "health_since" in columns

    # Nullable is intentional for legacy v5 rows:
    # v5 has no trustworthy state-start evidence.
    assert columns["health_since"][3] == 0


def test_version_five_database_migrates_to_six_without_fabricating_since(
    tmp_path,
) -> None:
    database_path = tmp_path / "health-since-v5.db"
    database = SQLiteHistoryDatabase(database_path)

    with database.connect() as connection:
        database._create_schema_version_table(
            connection
        )
        database._migrate_v1(connection)
        database._migrate_v2(connection)
        database._migrate_v3(connection)
        database._migrate_v4(connection)
        database._migrate_v5(connection)
        database._set_version(
            connection,
            5,
        )

        connection.execute(
            """
            INSERT INTO signal_health_current_state (
                profile_id,
                service_id,
                path_name,
                observed_at,
                health_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "impact-main",
                "impact",
                "impact",
                "2026-10-07T12:00:00.000000+00:00",
                '{"status":"HEALTHY"}',
            ),
        )

        connection.commit()

    assert _schema_version(database_path) == 5

    migrated = SQLiteHistoryDatabase(database_path)
    migrated.initialize()

    assert _schema_version(database_path) == 6

    connection = sqlite3.connect(database_path)

    try:
        row = connection.execute(
            """
            SELECT
                profile_id,
                service_id,
                path_name,
                observed_at,
                health_since,
                health_json
            FROM signal_health_current_state
            WHERE profile_id = ?
              AND service_id = ?
              AND path_name = ?
            """,
            (
                "impact-main",
                "impact",
                "impact",
            ),
        ).fetchone()
    finally:
        connection.close()

    assert row == (
        "impact-main",
        "impact",
        "impact",
        "2026-10-07T12:00:00.000000+00:00",
        None,
        '{"status":"HEALTHY"}',
    )


def test_reinitializing_version_six_database_is_idempotent(
    tmp_path,
) -> None:
    database_path = tmp_path / "health-since-idempotent.db"

    database = SQLiteHistoryDatabase(database_path)
    database.initialize()
    database.initialize()

    assert _schema_version(database_path) == 6

    connection = sqlite3.connect(database_path)

    try:
        columns = [
            row[1]
            for row in connection.execute(
                """
                PRAGMA table_info(
                    signal_health_current_state
                )
                """
            )
        ]
    finally:
        connection.close()

    assert columns.count("health_since") == 1
