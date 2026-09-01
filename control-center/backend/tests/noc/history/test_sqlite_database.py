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
