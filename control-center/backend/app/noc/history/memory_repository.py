"""In-memory adapters for NOC operational history.

ENG-013B — Operational History

These adapters implement the history repository ports without durable
storage. They are intended for unit tests, integration tests and semantic
validation before introducing SQLite persistence.
"""

from __future__ import annotations

from datetime import datetime
from threading import RLock

from app.noc.domain.node_alarm import AlarmRecord
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.history.alarm_transition import AlarmTransition
from app.noc.history.event_history_record import EventHistoryRecord
from app.noc.history.repository import (
    AlarmHistoryRepository,
    EventHistoryRepository,
)


class InMemoryEventHistoryRepository:
    """Thread-safe in-memory implementation of EventHistoryRepository."""

    def __init__(self) -> None:
        self._records: dict[str, EventHistoryRecord] = {}
        self._lock = RLock()

    def append(
        self,
        record: EventHistoryRecord,
    ) -> None:
        if not isinstance(record, EventHistoryRecord):
            raise TypeError(
                "record must be an EventHistoryRecord"
            )

        with self._lock:
            if record.event_id in self._records:
                raise ValueError(
                    f"event {record.event_id!r} already exists"
                )

            self._records[record.event_id] = record

    def get(
        self,
        event_id: str,
    ) -> EventHistoryRecord | None:
        normalized = self._normalize_id(
            event_id,
            "event_id",
        )

        with self._lock:
            return self._records.get(normalized)

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
            raise TypeError("node_id must be a NodeId or None")

        if (
            instance_id is not None
            and not isinstance(instance_id, NodeInstanceId)
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId or None"
            )

        with self._lock:
            records = tuple(self._records.values())

        filtered = [
            record
            for record in records
            if start <= record.timestamp < end
            and (
                node_id is None
                or record.node_id == node_id
            )
            and (
                instance_id is None
                or record.instance_id == instance_id
            )
        ]

        return tuple(
            sorted(
                filtered,
                key=lambda item: (
                    item.timestamp,
                    item.event_id,
                ),
            )
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
            raise TypeError("start must be a datetime")

        if not isinstance(end, datetime):
            raise TypeError("end must be a datetime")

        if start.tzinfo is None or start.utcoffset() is None:
            raise ValueError("start must be timezone-aware")

        if start.utcoffset().total_seconds() != 0:
            raise ValueError("start must be expressed in UTC")

        if end.tzinfo is None or end.utcoffset() is None:
            raise ValueError("end must be timezone-aware")

        if end.utcoffset().total_seconds() != 0:
            raise ValueError("end must be expressed in UTC")

        if start >= end:
            raise ValueError("start must precede end")


class InMemoryAlarmHistoryRepository:
    """Thread-safe in-memory implementation of AlarmHistoryRepository."""

    def __init__(self) -> None:
        self._current: dict[str, AlarmRecord] = {}
        self._transitions: dict[str, AlarmTransition] = {}
        self._alarm_scope: dict[
            str,
            tuple[NodeId, NodeInstanceId],
        ] = {}
        self._lock = RLock()

    def save_current(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm: AlarmRecord,
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

        with self._lock:
            existing_scope = self._alarm_scope.get(
                alarm.alarm_id
            )

            scope = (node_id, instance_id)

            if (
                existing_scope is not None
                and existing_scope != scope
            ):
                raise ValueError(
                    "alarm_id already belongs to another scope"
                )

            self._current[alarm.alarm_id] = alarm
            self._alarm_scope[alarm.alarm_id] = scope

    def append_transition(
        self,
        transition: AlarmTransition,
    ) -> None:
        if not isinstance(
            transition,
            AlarmTransition,
        ):
            raise TypeError(
                "transition must be an AlarmTransition"
            )

        with self._lock:
            if (
                transition.transition_id
                in self._transitions
            ):
                raise ValueError(
                    f"transition "
                    f"{transition.transition_id!r} "
                    "already exists"
                )

            self._transitions[
                transition.transition_id
            ] = transition

    def record_lifecycle(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm: AlarmRecord,
        transition: AlarmTransition,
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

        with self._lock:
            existing_scope = self._alarm_scope.get(
                alarm.alarm_id
            )

            scope = (node_id, instance_id)

            if (
                existing_scope is not None
                and existing_scope != scope
            ):
                raise ValueError(
                    "alarm_id already belongs to another scope"
                )

            existing_transition = self._transitions.get(
                transition.transition_id
            )

            if existing_transition is not None:
                existing_alarm = self._current.get(
                    alarm.alarm_id
                )

                if (
                    existing_transition == transition
                    and existing_alarm == alarm
                    and existing_scope == scope
                ):
                    return

                raise ValueError(
                    f"transition "
                    f"{transition.transition_id!r} "
                    "already exists with conflicting lifecycle data"
                )

            self._current[alarm.alarm_id] = alarm
            self._alarm_scope[alarm.alarm_id] = scope
            self._transitions[
                transition.transition_id
            ] = transition

    def get_current(
        self,
        alarm_id: str,
    ) -> AlarmRecord | None:
        normalized = self._normalize_id(
            alarm_id,
            "alarm_id",
        )

        with self._lock:
            return self._current.get(normalized)

    def list_active(
        self,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[AlarmRecord, ...]:
        if node_id is not None and not isinstance(node_id, NodeId):
            raise TypeError("node_id must be a NodeId or None")

        if (
            instance_id is not None
            and not isinstance(instance_id, NodeInstanceId)
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId or None"
            )

        with self._lock:
            items = tuple(self._current.items())
            scopes = dict(self._alarm_scope)

        filtered: list[AlarmRecord] = []

        for alarm_id, alarm in items:
            if not alarm.requires_attention:
                continue

            scope = scopes.get(alarm_id)

            if scope is None:
                continue

            alarm_node_id, alarm_instance_id = scope

            if (
                node_id is not None
                and alarm_node_id != node_id
            ):
                continue

            if (
                instance_id is not None
                and alarm_instance_id != instance_id
            ):
                continue

            filtered.append(alarm)

        return tuple(
            sorted(
                filtered,
                key=lambda item: (
                    item.timestamp,
                    item.alarm_id,
                ),
            )
        )

    def list_transitions(
        self,
        alarm_id: str,
    ) -> tuple[AlarmTransition, ...]:
        normalized = self._normalize_id(
            alarm_id,
            "alarm_id",
        )

        with self._lock:
            transitions = tuple(
                transition
                for transition in self._transitions.values()
                if transition.alarm_id == normalized
            )

        return tuple(
            sorted(
                transitions,
                key=lambda item: (
                    item.timestamp,
                    item.transition_id,
                ),
            )
        )

    def list_transitions_between(
        self,
        start: datetime,
        end: datetime,
        *,
        node_id: NodeId | None = None,
        instance_id: NodeInstanceId | None = None,
    ) -> tuple[AlarmTransition, ...]:
        InMemoryEventHistoryRepository._validate_window(
            start,
            end,
        )

        if node_id is not None and not isinstance(node_id, NodeId):
            raise TypeError("node_id must be a NodeId or None")

        if (
            instance_id is not None
            and not isinstance(instance_id, NodeInstanceId)
        ):
            raise TypeError(
                "instance_id must be a NodeInstanceId or None"
            )

        with self._lock:
            transitions = tuple(self._transitions.values())
            scopes = dict(self._alarm_scope)

        filtered: list[AlarmTransition] = []

        for transition in transitions:
            if not (
                start
                <= transition.timestamp
                < end
            ):
                continue

            scope = scopes.get(
                transition.alarm_id
            )

            if scope is None:
                continue

            alarm_node_id, alarm_instance_id = scope

            if (
                node_id is not None
                and alarm_node_id != node_id
            ):
                continue

            if (
                instance_id is not None
                and alarm_instance_id != instance_id
            ):
                continue

            filtered.append(transition)

        return tuple(
            sorted(
                filtered,
                key=lambda item: (
                    item.timestamp,
                    item.transition_id,
                ),
            )
        )

    @staticmethod
    def _normalize_id(
        value: str,
        field_name: str,
    ) -> str:
        return InMemoryEventHistoryRepository._normalize_id(
            value,
            field_name,
        )


_event_repository_contract: type[
    EventHistoryRepository
] = EventHistoryRepository

_alarm_repository_contract: type[
    AlarmHistoryRepository
] = AlarmHistoryRepository
