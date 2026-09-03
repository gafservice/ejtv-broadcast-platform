"""SQLite infrastructure for durable NOC operational history.

ENG-013B — Operational History

This module owns:
- SQLite connection policy;
- schema versioning;
- initial database migration.

It contains no NOC domain policy.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_VERSION = 2


class SQLiteHistoryDatabase:
    """Manage the SQLite operational-history database."""

    def __init__(
        self,
        path: str | Path,
    ) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def connect(self) -> sqlite3.Connection:
        """Open and configure one SQLite connection."""

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(
            self._path,
            timeout=5.0,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        connection.execute(
            "PRAGMA busy_timeout = 5000"
        )

        connection.execute(
            "PRAGMA synchronous = FULL"
        )

        connection.execute(
            "PRAGMA journal_mode = WAL"
        )

        return connection

    def initialize(self) -> None:
        """Create or migrate the operational-history schema."""

        with self.connect() as connection:
            self._create_schema_version_table(
                connection
            )

            current_version = self._current_version(
                connection
            )

            if current_version == 0:
                self._migrate_v1(connection)
                self._set_version(
                    connection,
                    1,
                )
                current_version = 1

            if current_version == 1:
                self._migrate_v2(connection)
                self._set_version(
                    connection,
                    2,
                )
                current_version = 2

            if current_version != SCHEMA_VERSION:
                raise RuntimeError(
                    "Unsupported NOC history schema version: "
                    f"{current_version}; "
                    f"expected {SCHEMA_VERSION}"
                )

    @staticmethod
    def _create_schema_version_table(
        connection: sqlite3.Connection,
    ) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            )
            """
        )

    @staticmethod
    def _current_version(
        connection: sqlite3.Connection,
    ) -> int:
        row = connection.execute(
            """
            SELECT version
            FROM schema_version
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            return 0

        return int(row["version"])

    @staticmethod
    def _set_version(
        connection: sqlite3.Connection,
        version: int,
    ) -> None:
        connection.execute(
            "DELETE FROM schema_version"
        )

        connection.execute(
            """
            INSERT INTO schema_version(version)
            VALUES (?)
            """,
            (version,),
        )

    @staticmethod
    def _migrate_v1(
        connection: sqlite3.Connection,
    ) -> None:
        connection.executescript(
            """
            CREATE TABLE events (
                event_id TEXT PRIMARY KEY,
                node_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                node_display_name TEXT NOT NULL,
                node_created_at TEXT NOT NULL,

                instance_id TEXT NOT NULL,

                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,

                event_timestamp TEXT NOT NULL,
                recorded_at TEXT NOT NULL,

                source TEXT NOT NULL,

                title TEXT NOT NULL,
                description TEXT NOT NULL,

                correlation_id TEXT,
                attributes_json TEXT
            );

            CREATE INDEX idx_events_timestamp
                ON events(event_timestamp);

            CREATE INDEX idx_events_node_instance_timestamp
                ON events(
                    node_id,
                    instance_id,
                    event_timestamp
                );


            CREATE TABLE alarms (
                alarm_id TEXT PRIMARY KEY,

                node_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                node_display_name TEXT NOT NULL,
                node_created_at TEXT NOT NULL,

                instance_id TEXT NOT NULL,

                alarm_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                state TEXT NOT NULL,

                opened_at TEXT NOT NULL,
                source TEXT NOT NULL,

                title TEXT NOT NULL,
                description TEXT NOT NULL,

                acknowledged INTEGER NOT NULL,
                acknowledged_by TEXT,
                acknowledged_at TEXT,

                resolved_at TEXT,
                closed_at TEXT,

                correlation_id TEXT,
                attributes_json TEXT NOT NULL
            );

            CREATE INDEX idx_alarms_state
                ON alarms(state);

            CREATE INDEX idx_alarms_node_instance_state
                ON alarms(
                    node_id,
                    instance_id,
                    state
                );


            CREATE TABLE alarm_transitions (
                transition_id TEXT PRIMARY KEY,

                alarm_id TEXT NOT NULL,

                transition_type TEXT NOT NULL,
                transition_timestamp TEXT NOT NULL,

                source TEXT NOT NULL,
                state TEXT NOT NULL,

                actor TEXT,
                metadata_json TEXT NOT NULL,

                FOREIGN KEY(alarm_id)
                    REFERENCES alarms(alarm_id)
                    ON DELETE RESTRICT
            );

            CREATE INDEX idx_alarm_transitions_alarm_timestamp
                ON alarm_transitions(
                    alarm_id,
                    transition_timestamp
                );

            CREATE INDEX idx_alarm_transitions_timestamp
                ON alarm_transitions(
                    transition_timestamp
                );
            """
        )

    @staticmethod
    def _migrate_v2(
        connection: sqlite3.Connection,
    ) -> None:
        """Add shared current-state storage for Node health diagnostics."""

        connection.executescript(
            """
            CREATE TABLE node_health_diagnostics (
                node_id TEXT NOT NULL,
                instance_id TEXT NOT NULL,

                captured_at TEXT NOT NULL,
                diagnostic_json TEXT NOT NULL,

                PRIMARY KEY (
                    node_id,
                    instance_id
                )
            );

            CREATE INDEX idx_node_health_diagnostics_captured_at
                ON node_health_diagnostics(captured_at);
            """
        )
