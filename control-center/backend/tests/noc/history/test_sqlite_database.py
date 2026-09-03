import sqlite3

import pytest

from app.noc.history.sqlite_database import (
    SCHEMA_VERSION,
    SQLiteHistoryDatabase,
)


def test_database_initializes_schema(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"

    database = SQLiteHistoryDatabase(path)
    database.initialize()

    assert path.exists()

    with database.connect() as connection:
        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            )
        }

    assert {
        "schema_version",
        "events",
        "alarms",
        "alarm_transitions",
    }.issubset(tables)


def test_schema_version_is_current(tmp_path) -> None:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    database.initialize()

    with database.connect() as connection:
        row = connection.execute(
            """
            SELECT version
            FROM schema_version
            """
        ).fetchone()

    assert row is not None
    assert row["version"] == SCHEMA_VERSION


def test_initialize_is_idempotent(tmp_path) -> None:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    database.initialize()
    database.initialize()

    with database.connect() as connection:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM schema_version
            """
        ).fetchone()[0]

    assert count == 1


def test_foreign_keys_are_enabled(tmp_path) -> None:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    database.initialize()

    with database.connect() as connection:
        enabled = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

    assert enabled == 1


def test_journal_mode_is_wal(tmp_path) -> None:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    database.initialize()

    with database.connect() as connection:
        mode = connection.execute(
            "PRAGMA journal_mode"
        ).fetchone()[0]

    assert mode.lower() == "wal"


def test_synchronous_is_full(tmp_path) -> None:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    database.initialize()

    with database.connect() as connection:
        synchronous = connection.execute(
            "PRAGMA synchronous"
        ).fetchone()[0]

    # SQLite FULL = 2
    assert synchronous == 2


def test_alarm_transition_requires_existing_alarm(
    tmp_path,
) -> None:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    database.initialize()

    with database.connect() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO alarm_transitions (
                    transition_id,
                    alarm_id,
                    transition_type,
                    transition_timestamp,
                    source,
                    state,
                    actor,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "transition-001",
                    "missing-alarm",
                    "OPENED",
                    "2026-09-01T12:00:00+00:00",
                    "instance-001",
                    "ACTIVE",
                    None,
                    "{}",
                ),
            )


def test_unknown_schema_version_is_rejected(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    connection = sqlite3.connect(path)

    connection.execute(
        """
        CREATE TABLE schema_version (
            version INTEGER NOT NULL
        )
        """
    )

    connection.execute(
        """
        INSERT INTO schema_version(version)
        VALUES (999)
        """
    )

    connection.commit()
    connection.close()

    database = SQLiteHistoryDatabase(path)

    with pytest.raises(RuntimeError):
        database.initialize()


def test_v2_schema_contains_node_health_diagnostics(
    tmp_path,
) -> None:
    database = SQLiteHistoryDatabase(
        tmp_path / "history.sqlite3"
    )

    database.initialize()

    with database.connect() as connection:
        row = connection.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'node_health_diagnostics'
            """
        ).fetchone()

    assert row is not None
    assert "node_id" in row["sql"]
    assert "instance_id" in row["sql"]
    assert "captured_at" in row["sql"]
    assert "diagnostic_json" in row["sql"]


def test_existing_v1_database_migrates_to_current_schema(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    database = SQLiteHistoryDatabase(path)

    with database.connect() as connection:
        database._create_schema_version_table(
            connection
        )
        database._migrate_v1(
            connection
        )
        database._set_version(
            connection,
            1,
        )

        connection.execute(
            """
            INSERT INTO events (
                event_id,
                node_id,
                node_name,
                node_display_name,
                node_created_at,
                instance_id,
                event_type,
                severity,
                event_timestamp,
                recorded_at,
                source,
                title,
                description,
                correlation_id,
                attributes_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "event-before-v2",
                "node-001",
                "node-001",
                "Node 001",
                "2026-09-03T12:00:00+00:00",
                "instance-001",
                "TEST_EVENT",
                "INFO",
                "2026-09-03T12:01:00+00:00",
                "2026-09-03T12:01:00+00:00",
                "instance-001",
                "Before migration",
                "Existing v1 event",
                None,
                None,
            ),
        )

    database.initialize()

    with database.connect() as connection:
        version = connection.execute(
            """
            SELECT version
            FROM schema_version
            """
        ).fetchone()

        table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'node_health_diagnostics'
            """
        ).fetchone()

        event = connection.execute(
            """
            SELECT event_id
            FROM events
            WHERE event_id = ?
            """,
            ("event-before-v2",),
        ).fetchone()

    assert version is not None
    assert version["version"] == SCHEMA_VERSION
    assert table is not None
    assert event is not None
    assert event["event_id"] == "event-before-v2"


def test_existing_v2_database_migrates_to_v3_preserving_history(
    tmp_path,
) -> None:
    path = tmp_path / "history.sqlite3"

    database = SQLiteHistoryDatabase(path)

    with database.connect() as connection:
        database._create_schema_version_table(
            connection
        )
        database._migrate_v1(
            connection
        )
        database._migrate_v2(
            connection
        )
        database._set_version(
            connection,
            2,
        )

        connection.execute(
            """
            INSERT INTO events (
                event_id,
                node_id,
                node_name,
                node_display_name,
                node_created_at,
                instance_id,
                event_type,
                severity,
                event_timestamp,
                recorded_at,
                source,
                title,
                description,
                correlation_id,
                attributes_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "event-before-v3",
                "node-001",
                "node-001",
                "Node 001",
                "2026-09-03T12:00:00+00:00",
                "instance-001",
                "TEST_EVENT",
                "INFO",
                "2026-09-03T12:01:00+00:00",
                "2026-09-03T12:01:00+00:00",
                "instance-001",
                "Before v3 migration",
                "Existing v2 event",
                None,
                None,
            ),
        )

    database.initialize()

    with database.connect() as connection:
        version = connection.execute(
            """
            SELECT version
            FROM schema_version
            """
        ).fetchone()

        managed_table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'managed_history_scopes'
            """
        ).fetchone()

        event = connection.execute(
            """
            SELECT event_id
            FROM events
            WHERE event_id = ?
            """,
            ("event-before-v3",),
        ).fetchone()

    assert version is not None
    assert version["version"] == SCHEMA_VERSION

    assert managed_table is not None
    assert managed_table["name"] == "managed_history_scopes"

    assert event is not None
    assert event["event_id"] == "event-before-v3"
