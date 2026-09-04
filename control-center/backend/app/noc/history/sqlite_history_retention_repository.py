"""SQLite adapter for durable NOC history retention.

ENG-013B — Operational History

This adapter performs one scope-local retention prune atomically.

Policy decisions such as retention duration and evidence eligibility
belong to higher layers. This adapter only applies an explicit UTC
cutoff while preserving complete alarm lifecycles.
"""

from __future__ import annotations

from datetime import datetime

from app.noc.domain.node_alarm import AlarmState
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.history_retention_repository import (
    HistoryRetentionResult,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)


class SQLiteHistoryRetentionRepository:
    """Transactional SQLite implementation of history retention."""

    _TERMINAL_STATES = (
        AlarmState.RESOLVED.value,
        AlarmState.CLOSED.value,
        AlarmState.INVALIDATED.value,
    )

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

    def prune_before(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        cutoff: datetime,
    ) -> HistoryRetentionResult:
        self._validate_scope(
            node_id=node_id,
            instance_id=instance_id,
        )

        self._validate_cutoff(cutoff)

        cutoff_value = cutoff.isoformat(
            timespec="microseconds"
        )

        with self._database.connect() as connection:
            alarm_rows = connection.execute(
                """
                SELECT a.alarm_id
                FROM alarms AS a
                WHERE a.node_id = ?
                  AND a.instance_id = ?
                  AND a.state IN (?, ?, ?)
                  AND EXISTS (
                      SELECT 1
                      FROM alarm_transitions AS t
                      WHERE t.alarm_id = a.alarm_id
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM alarm_transitions AS t
                      WHERE t.alarm_id = a.alarm_id
                        AND t.transition_timestamp >= ?
                  )
                ORDER BY a.alarm_id ASC
                """,
                (
                    node_id.id,
                    instance_id.value,
                    *self._TERMINAL_STATES,
                    cutoff_value,
                ),
            ).fetchall()

            alarm_ids = tuple(
                row["alarm_id"]
                for row in alarm_rows
            )

            alarm_transitions_deleted = 0
            alarms_deleted = 0

            if alarm_ids:
                placeholders = ", ".join(
                    "?"
                    for _ in alarm_ids
                )

                transition_cursor = connection.execute(
                    f"""
                    DELETE FROM alarm_transitions
                    WHERE alarm_id IN ({placeholders})
                    """,
                    alarm_ids,
                )

                alarm_transitions_deleted = (
                    transition_cursor.rowcount
                )

                alarm_cursor = connection.execute(
                    f"""
                    DELETE FROM alarms
                    WHERE alarm_id IN ({placeholders})
                    """,
                    alarm_ids,
                )

                alarms_deleted = alarm_cursor.rowcount

            event_cursor = connection.execute(
                """
                DELETE FROM events
                WHERE node_id = ?
                  AND instance_id = ?
                  AND event_timestamp < ?
                """,
                (
                    node_id.id,
                    instance_id.value,
                    cutoff_value,
                ),
            )

            return HistoryRetentionResult(
                events_deleted=event_cursor.rowcount,
                alarm_transitions_deleted=(
                    alarm_transitions_deleted
                ),
                alarms_deleted=alarms_deleted,
            )

    @staticmethod
    def _validate_scope(
        *,
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

    @staticmethod
    def _validate_cutoff(
        cutoff: datetime,
    ) -> None:
        if not isinstance(cutoff, datetime):
            raise TypeError(
                "cutoff must be a datetime"
            )

        if (
            cutoff.tzinfo is None
            or cutoff.utcoffset() is None
        ):
            raise ValueError(
                "cutoff must be timezone-aware"
            )

        if cutoff.utcoffset().total_seconds() != 0:
            raise ValueError(
                "cutoff must be expressed in UTC"
            )
