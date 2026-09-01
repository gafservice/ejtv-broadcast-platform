"""SQLite adapter for durable NOC alarm history.

ENG-013B — Operational History
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import nullcontext
from datetime import datetime

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)


class SQLiteAlarmHistoryRepository:
    """SQLite implementation of the AlarmHistoryRepository port."""

    def __init__(
        self,
        database: SQLiteHistoryDatabase,
    ) -> None:
        if not isinstance(database, SQLiteHistoryDatabase):
            raise TypeError(
                "database must be a SQLiteHistoryDatabase"
            )

        self._database = database
        self._database.initialize()

    def save_current(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm: AlarmRecord,
        _connection: sqlite3.Connection | None = None,
    ) -> None:
        if not isinstance(node_id, NodeId):
            raise TypeError("node_id must be a NodeId")

        if not isinstance(instance_id, NodeInstanceId):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        if not isinstance(alarm, AlarmRecord):
            raise TypeError(
                "alarm must be an AlarmRecord"
            )

        if alarm.source != instance_id:
            raise ValueError(
                "instance_id must match AlarmRecord.source"
            )

        with self._connection_context(
            _connection
        ) as connection:
            existing = connection.execute(
                """
                SELECT node_id, instance_id
                FROM alarms
                WHERE alarm_id = ?
                """,
                (alarm.alarm_id,),
            ).fetchone()

            if existing is not None:
                if (
                    existing["node_id"] != node_id.id
                    or existing["instance_id"] != instance_id.value
                ):
                    raise ValueError(
                        "alarm_id already belongs to another scope"
                    )

            connection.execute(
                """
                INSERT INTO alarms (
                    alarm_id,

                    node_id,
                    node_name,
                    node_display_name,
                    node_created_at,
                    instance_id,

                    alarm_type,
                    severity,
                    state,

                    opened_at,
                    source,

                    title,
                    description,

                    acknowledged,
                    acknowledged_by,
                    acknowledged_at,

                    resolved_at,
                    closed_at,

                    correlation_id,
                    attributes_json
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?
                )
                ON CONFLICT(alarm_id)
                DO UPDATE SET
                    node_name = excluded.node_name,
                    node_display_name = excluded.node_display_name,
                    node_created_at = excluded.node_created_at,

                    alarm_type = excluded.alarm_type,
                    severity = excluded.severity,
                    state = excluded.state,

                    opened_at = excluded.opened_at,
                    source = excluded.source,

                    title = excluded.title,
                    description = excluded.description,

                    acknowledged = excluded.acknowledged,
                    acknowledged_by = excluded.acknowledged_by,
                    acknowledged_at = excluded.acknowledged_at,

                    resolved_at = excluded.resolved_at,
                    closed_at = excluded.closed_at,

                    correlation_id = excluded.correlation_id,
                    attributes_json = excluded.attributes_json
                """,
                (
                    alarm.alarm_id,

                    node_id.id,
                    node_id.name,
                    node_id.display_name,
                    self._encode_datetime(
                        node_id.created_at
                    ),
                    instance_id.value,

                    alarm.alarm_type,
                    alarm.severity.value,
                    alarm.state.value,

                    self._encode_datetime(
                        alarm.timestamp
                    ),
                    alarm.source.value,

                    alarm.title,
                    alarm.description,

                    int(alarm.acknowledged),
                    alarm.acknowledged_by,
                    self._encode_optional_datetime(
                        alarm.acknowledged_at
                    ),

                    self._encode_optional_datetime(
                        alarm.resolved_at
                    ),
                    self._encode_optional_datetime(
                        alarm.closed_at
                    ),

                    alarm.correlation_id,
                    json.dumps(
                        (
                            None
                            if alarm.attributes is None
                            else dict(alarm.attributes)
                        ),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )

    def append_transition(
        self,
        transition: AlarmTransition,
        *,
        _connection: sqlite3.Connection | None = None,
    ) -> None:
        if not isinstance(
            transition,
            AlarmTransition,
        ):
            raise TypeError(
                "transition must be an AlarmTransition"
            )

        with self._connection_context(
            _connection
        ) as connection:
            try:
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
                        transition.transition_id,
                        transition.alarm_id,
                        transition.transition_type.value,
                        self._encode_datetime(
                            transition.timestamp
                        ),
                        transition.source.value,
                        transition.state.value,
                        transition.actor,
                        json.dumps(
                                (
                                    None
                                    if transition.metadata is None
                                    else dict(transition.metadata)
                                ),
                                sort_keys=True,
                                separators=(",", ":"),
                            ),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                message = str(exc).lower()

                if (
                    "unique" in message
                    or "primary key" in message
                ):
                    raise ValueError(
                        f"transition "
                        f"{transition.transition_id!r} "
                        "already exists"
                    ) from exc

                raise

    def record_lifecycle(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm: AlarmRecord,
        transition: AlarmTransition,
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

        if not isinstance(alarm, AlarmRecord):
            raise TypeError(
                "alarm must be an AlarmRecord"
            )

        if not isinstance(
            transition,
            AlarmTransition,
        ):
            raise TypeError(
                "transition must be an AlarmTransition"
            )

        if alarm.source != instance_id:
            raise ValueError(
                "instance_id must match AlarmRecord.source"
            )

        if transition.alarm_id != alarm.alarm_id:
            raise ValueError(
                "transition alarm_id must match alarm"
            )

        if transition.source != instance_id:
            raise ValueError(
                "transition source must match instance_id"
            )

        if transition.state != alarm.state:
            raise ValueError(
                "transition state must match alarm state"
            )

        with self._database.connect() as connection:
            transition_row = connection.execute(
                """
                SELECT *
                FROM alarm_transitions
                WHERE transition_id = ?
                """,
                (transition.transition_id,),
            ).fetchone()

            if transition_row is not None:
                existing_transition = self._decode_transition(
                    transition_row
                )

                alarm_row = connection.execute(
                    """
                    SELECT *
                    FROM alarms
                    WHERE alarm_id = ?
                    """,
                    (alarm.alarm_id,),
                ).fetchone()

                existing_alarm = (
                    None
                    if alarm_row is None
                    else self._decode_alarm(alarm_row)
                )

                if (
                    existing_transition == transition
                    and existing_alarm == alarm
                    and alarm_row is not None
                    and alarm_row["node_id"] == node_id.id
                    and alarm_row["instance_id"]
                    == instance_id.value
                ):
                    return

                raise ValueError(
                    f"transition "
                    f"{transition.transition_id!r} "
                    "already exists with conflicting lifecycle data"
                )

            self.save_current(
                node_id=node_id,
                instance_id=instance_id,
                alarm=alarm,
                _connection=connection,
            )

            self.append_transition(
                transition,
                _connection=connection,
            )

    def get_current(
        self,
        alarm_id: str,
    ) -> AlarmRecord | None:
        normalized = self._normalize_id(
            alarm_id,
            "alarm_id",
        )

        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM alarms
                WHERE alarm_id = ?
                """,
                (normalized,),
            ).fetchone()

        if row is None:
            return None

        return self._decode_alarm(row)

    def list_all(
        self,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[AlarmRecord, ...]:
        if node_id is not None and not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId or None"
            )

        if (
            instance_id is not None
            and not isinstance(instance_id, NodeInstanceId)
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId or None"
            )

        clauses: list[str] = []
        parameters: list[str] = []

        if node_id is not None:
            clauses.append("node_id = ?")
            parameters.append(node_id.id)

        if instance_id is not None:
            clauses.append("instance_id = ?")
            parameters.append(instance_id.value)

        where = (
            ""
            if not clauses
            else "WHERE " + " AND ".join(clauses)
        )

        query = f"""
            SELECT *
            FROM alarms
            {where}
            ORDER BY opened_at ASC, alarm_id ASC
        """

        with self._database.connect() as connection:
            rows = connection.execute(
                query,
                tuple(parameters),
            ).fetchall()

        return tuple(
            self._decode_alarm(row)
            for row in rows
        )

    def record_historical_transition(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: AlarmTransition,
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

        if not isinstance(
            transition,
            AlarmTransition,
        ):
            raise TypeError(
                "transition must be an AlarmTransition"
            )

        if transition.source != instance_id:
            raise ValueError(
                "transition source must match instance_id"
            )

        with self._database.connect() as connection:
            alarm_row = connection.execute(
                """
                SELECT node_id, instance_id
                FROM alarms
                WHERE alarm_id = ?
                """,
                (transition.alarm_id,),
            ).fetchone()

            if alarm_row is None:
                raise ValueError(
                    "historical transition alarm does not exist"
                )

            if (
                alarm_row["node_id"] != node_id.id
                or alarm_row["instance_id"]
                != instance_id.value
            ):
                raise ValueError(
                    "alarm_id belongs to another scope"
                )

            transition_row = connection.execute(
                """
                SELECT *
                FROM alarm_transitions
                WHERE transition_id = ?
                """,
                (transition.transition_id,),
            ).fetchone()

            if transition_row is not None:
                existing = self._decode_transition(
                    transition_row
                )

                if existing == transition:
                    return

                raise ValueError(
                    f"transition "
                    f"{transition.transition_id!r} "
                    "already exists with conflicting historical data"
                )

            self.append_transition(
                transition,
                _connection=connection,
            )

    def list_active(
        self,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[AlarmRecord, ...]:
        if node_id is not None and not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId or None"
            )

        if (
            instance_id is not None
            and not isinstance(instance_id, NodeInstanceId)
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId or None"
            )

        clauses = [
            "state IN (?, ?)",
        ]

        parameters: list[str] = [
            AlarmState.ACTIVE.value,
            AlarmState.ACKNOWLEDGED.value,
        ]

        if node_id is not None:
            clauses.append("node_id = ?")
            parameters.append(node_id.id)

        if instance_id is not None:
            clauses.append("instance_id = ?")
            parameters.append(instance_id.value)

        query = f"""
            SELECT *
            FROM alarms
            WHERE {' AND '.join(clauses)}
            ORDER BY opened_at ASC, alarm_id ASC
        """

        with self._database.connect() as connection:
            rows = connection.execute(
                query,
                tuple(parameters),
            ).fetchall()

        return tuple(
            self._decode_alarm(row)
            for row in rows
        )

    def list_transitions(
        self,
        alarm_id: str,
    ) -> tuple[AlarmTransition, ...]:
        normalized = self._normalize_id(
            alarm_id,
            "alarm_id",
        )

        with self._database.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM alarm_transitions
                WHERE alarm_id = ?
                ORDER BY
                    transition_timestamp ASC,
                    transition_id ASC
                """,
                (normalized,),
            ).fetchall()

        return tuple(
            self._decode_transition(row)
            for row in rows
        )

    def list_transitions_between(
        self,
        start: datetime,
        end: datetime,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[AlarmTransition, ...]:
        self._validate_window(start, end)

        if node_id is not None and not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId or None"
            )

        if (
            instance_id is not None
            and not isinstance(instance_id, NodeInstanceId)
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId or None"
            )

        clauses = [
            "t.transition_timestamp >= ?",
            "t.transition_timestamp < ?",
        ]

        parameters: list[str] = [
            self._encode_datetime(start),
            self._encode_datetime(end),
        ]

        if node_id is not None:
            clauses.append("a.node_id = ?")
            parameters.append(node_id.id)

        if instance_id is not None:
            clauses.append("a.instance_id = ?")
            parameters.append(instance_id.value)

        query = f"""
            SELECT t.*
            FROM alarm_transitions AS t
            INNER JOIN alarms AS a
                ON a.alarm_id = t.alarm_id
            WHERE {' AND '.join(clauses)}
            ORDER BY
                t.transition_timestamp ASC,
                t.transition_id ASC
        """

        with self._database.connect() as connection:
            rows = connection.execute(
                query,
                tuple(parameters),
            ).fetchall()

        return tuple(
            self._decode_transition(row)
            for row in rows
        )

    def _connection_context(
        self,
        connection: sqlite3.Connection | None,
    ):
        if connection is None:
            return self._database.connect()

        return nullcontext(connection)

    @staticmethod
    def _decode_alarm(
        row,
    ) -> AlarmRecord:
        return AlarmRecord(
            alarm_id=row["alarm_id"],
            alarm_type=row["alarm_type"],
            severity=AlarmSeverity(
                row["severity"]
            ),
            state=AlarmState(
                row["state"]
            ),
            timestamp=(
                SQLiteAlarmHistoryRepository._decode_datetime(
                    row["opened_at"]
                )
            ),
            source=NodeInstanceId(
                row["source"]
            ),
            title=row["title"],
            description=row["description"],
            acknowledged=bool(
                row["acknowledged"]
            ),
            acknowledged_by=row["acknowledged_by"],
            acknowledged_at=(
                SQLiteAlarmHistoryRepository._decode_optional_datetime(
                    row["acknowledged_at"]
                )
            ),
            resolved_at=(
                SQLiteAlarmHistoryRepository._decode_optional_datetime(
                    row["resolved_at"]
                )
            ),
            closed_at=(
                SQLiteAlarmHistoryRepository._decode_optional_datetime(
                    row["closed_at"]
                )
            ),
            correlation_id=row["correlation_id"],
            attributes=json.loads(
                row["attributes_json"]
            ),
        )

    @staticmethod
    def _decode_transition(
        row,
    ) -> AlarmTransition:
        return AlarmTransition(
            transition_id=row["transition_id"],
            alarm_id=row["alarm_id"],
            transition_type=AlarmTransitionType(
                row["transition_type"]
            ),
            timestamp=(
                SQLiteAlarmHistoryRepository._decode_datetime(
                    row["transition_timestamp"]
                )
            ),
            source=NodeInstanceId(
                row["source"]
            ),
            state=AlarmState(
                row["state"]
            ),
            actor=row["actor"],
            metadata=json.loads(
                row["metadata_json"]
            ),
        )

    @staticmethod
    def _encode_datetime(
        value: datetime,
    ) -> str:
        return value.isoformat(
            timespec="microseconds"
        )

    @staticmethod
    def _encode_optional_datetime(
        value: datetime | None,
    ) -> str | None:
        if value is None:
            return None

        return SQLiteAlarmHistoryRepository._encode_datetime(
            value
        )

    @staticmethod
    def _decode_datetime(
        value: str,
    ) -> datetime:
        return datetime.fromisoformat(value)

    @staticmethod
    def _decode_optional_datetime(
        value: str | None,
    ) -> datetime | None:
        if value is None:
            return None

        return SQLiteAlarmHistoryRepository._decode_datetime(
            value
        )

    @staticmethod
    def _normalize_id(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be a string"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _validate_window(
        start: datetime,
        end: datetime,
    ) -> None:
        if not isinstance(start, datetime):
            raise TypeError(
                "start must be a datetime"
            )

        if not isinstance(end, datetime):
            raise TypeError(
                "end must be a datetime"
            )

        if (
            start.tzinfo is None
            or start.utcoffset() is None
        ):
            raise ValueError(
                "start must be timezone-aware"
            )

        if start.utcoffset().total_seconds() != 0:
            raise ValueError(
                "start must be expressed in UTC"
            )

        if (
            end.tzinfo is None
            or end.utcoffset() is None
        ):
            raise ValueError(
                "end must be timezone-aware"
            )

        if end.utcoffset().total_seconds() != 0:
            raise ValueError(
                "end must be expressed in UTC"
            )

        if start >= end:
            raise ValueError(
                "start must precede end"
            )
