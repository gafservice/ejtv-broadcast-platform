"""SQLite adapter for durable managed-history authority.

ENG-013B — persistent operational history.
"""

from __future__ import annotations

from datetime import date, datetime

from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)


class SQLiteManagedHistoryRepository:
    """Persist the immutable lower bound of managed NOC history."""

    def __init__(
        self,
        database: SQLiteHistoryDatabase,
    ) -> None:
        if not isinstance(
            database,
            SQLiteHistoryDatabase,
        ):
            raise TypeError(
                "database must be a SQLiteHistoryDatabase"
            )

        self._database = database
        self._database.initialize()

    def get_managed_since_day(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> date | None:
        self._validate_scope(
            node_id,
            instance_id,
        )

        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT managed_since_day
                FROM managed_history_scopes
                WHERE node_id = ?
                  AND instance_id = ?
                """,
                (
                    node_id.id,
                    instance_id.value,
                ),
            ).fetchone()

        if row is None:
            return None

        return date.fromisoformat(
            row["managed_since_day"]
        )

    def ensure_managed_since_day(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        day: date,
        created_at: datetime,
    ) -> date:
        self._validate_scope(
            node_id,
            instance_id,
        )

        if not isinstance(day, date) or isinstance(day, datetime):
            raise TypeError(
                "day must be a date"
            )

        if not isinstance(created_at, datetime):
            raise TypeError(
                "created_at must be a datetime"
            )

        if (
            created_at.tzinfo is None
            or created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )

        if created_at.utcoffset().total_seconds() != 0:
            raise ValueError(
                "created_at must be expressed in UTC"
            )

        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO managed_history_scopes (
                    node_id,
                    instance_id,
                    managed_since_day,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    node_id.id,
                    instance_id.value,
                    day.isoformat(),
                    created_at.isoformat(
                        timespec="microseconds"
                    ),
                ),
            )

            row = connection.execute(
                """
                SELECT managed_since_day
                FROM managed_history_scopes
                WHERE node_id = ?
                  AND instance_id = ?
                """,
                (
                    node_id.id,
                    instance_id.value,
                ),
            ).fetchone()

        if row is None:
            raise RuntimeError(
                "managed-history anchor was not persisted"
            )

        return date.fromisoformat(
            row["managed_since_day"]
        )

    @staticmethod
    def _validate_scope(
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> None:
        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

        if not isinstance(
            instance_id,
            NodeInstanceId,
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )
