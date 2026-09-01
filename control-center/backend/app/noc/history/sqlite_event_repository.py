"""SQLite adapter for durable NOC event history.

ENG-013B — Operational History
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.event_history_record import (
    EventHistoryRecord,
)
from app.noc.history.sqlite_database import (
    SQLiteHistoryDatabase,
)


class SQLiteEventHistoryRepository:
    """SQLite implementation of the EventHistoryRepository port."""

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

    def append(
        self,
        record: EventHistoryRecord,
    ) -> None:
        if not isinstance(record, EventHistoryRecord):
            raise TypeError(
                "record must be an EventHistoryRecord"
            )

        with self._database.connect() as connection:
            try:
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
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        record.event.event_id,
                        record.node_id.id,
                        record.node_id.name,
                        record.node_id.display_name,
                        self._encode_datetime(
                            record.node_id.created_at
                        ),
                        record.instance_id.value,
                        record.event.event_type,
                        record.event.severity.value,
                        self._encode_datetime(
                            record.event.timestamp
                        ),
                        self._encode_datetime(
                            record.recorded_at
                        ),
                        record.event.source.value,
                        record.event.title,
                        record.event.description,
                        record.event.correlation_id,
                        (
                            None
                            if record.event.attributes is None
                            else json.dumps(
                                dict(record.event.attributes),
                                sort_keys=True,
                                separators=(",", ":"),
                            )
                        ),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    f"event {record.event_id!r} "
                    "already exists"
                ) from exc

    def get(
        self,
        event_id: str,
    ) -> EventHistoryRecord | None:
        normalized = self._normalize_id(
            event_id,
            "event_id",
        )

        with self._database.connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM events
                WHERE event_id = ?
                """,
                (normalized,),
            ).fetchone()

        if row is None:
            return None

        return self._decode_row(row)

    def list_between(
        self,
        start: datetime,
        end: datetime,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[EventHistoryRecord, ...]:
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
            "event_timestamp >= ?",
            "event_timestamp < ?",
        ]

        parameters: list[str] = [
            self._encode_datetime(start),
            self._encode_datetime(end),
        ]

        if node_id is not None:
            clauses.append("node_id = ?")
            parameters.append(node_id.id)

        if instance_id is not None:
            clauses.append("instance_id = ?")
            parameters.append(instance_id.value)

        query = f"""
            SELECT *
            FROM events
            WHERE {' AND '.join(clauses)}
            ORDER BY event_timestamp ASC, event_id ASC
        """

        with self._database.connect() as connection:
            rows = connection.execute(
                query,
                tuple(parameters),
            ).fetchall()

        return tuple(
            self._decode_row(row)
            for row in rows
        )

    @staticmethod
    def _decode_row(row) -> EventHistoryRecord:
        instance_id = NodeInstanceId(
            row["instance_id"]
        )

        event = EventRecord(
            event_id=row["event_id"],
            event_type=row["event_type"],
            severity=EventSeverity(
                row["severity"]
            ),
            timestamp=SQLiteEventHistoryRepository._decode_datetime(
                row["event_timestamp"]
            ),
            source=NodeInstanceId(
                row["source"]
            ),
            title=row["title"],
            description=row["description"],
            correlation_id=row["correlation_id"],
            attributes=(
                None
                if row["attributes_json"] is None
                else json.loads(
                    row["attributes_json"]
                )
            ),
        )

        node_id = NodeId(
            id=row["node_id"],
            name=row["node_name"],
            display_name=row["node_display_name"],
            created_at=(
                SQLiteEventHistoryRepository._decode_datetime(
                    row["node_created_at"]
                )
            ),
        )

        return EventHistoryRecord(
            event=event,
            node_id=node_id,
            instance_id=instance_id,
            recorded_at=SQLiteEventHistoryRepository._decode_datetime(
                row["recorded_at"]
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
    def _decode_datetime(
        value: str,
    ) -> datetime:
        return datetime.fromisoformat(value)

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
