"""Alarm coordination service for the NOC.

ENG-013B — Node SDK
NCS reference: 18-NODE-ALARM.md

AlarmService coordinates the lifecycle of AlarmRecord objects belonging
to registered NodeInstances.

AlarmRecord is immutable. Lifecycle transitions therefore replace the
current record with a new canonical AlarmRecord.

Alarm detection policy does not belong here. Other components decide
when an operational condition should raise an alarm.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import (
    NodeInstance,
    NodeInstanceId,
)
from app.noc.registry.registry import NodeRegistry


class AlarmServiceError(Exception):
    """Base error raised by AlarmService."""


class NodeInstanceNotFoundError(AlarmServiceError):
    """Raised when a NodeInstance cannot be found."""


class AlarmNotFoundError(AlarmServiceError):
    """Raised when an alarm cannot be found."""


class DuplicateAlarmError(AlarmServiceError):
    """Raised when an alarm_id already exists."""


class InvalidAlarmTransitionError(AlarmServiceError):
    """Raised when an alarm lifecycle transition is invalid."""


class AlarmSourceMismatchError(AlarmServiceError):
    """Raised when an alarm belongs to another NodeInstance."""


class AlarmDisposition(str, Enum):
    """Result of an AlarmService operation."""

    RAISED = "RAISED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AlarmReceipt:
    """Result returned after an alarm lifecycle operation."""

    disposition: AlarmDisposition
    alarm: AlarmRecord


class AlarmService:
    """Coordinate alarms for registered NodeInstances."""

    def __init__(self, registry: NodeRegistry) -> None:
        if not isinstance(registry, NodeRegistry):
            raise TypeError(
                "registry must be a NodeRegistry"
            )

        self._registry = registry

    def raise_alarm(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm: AlarmRecord,
    ) -> AlarmReceipt:
        """Store a new ACTIVE alarm."""

        instance, node = self._resolve_instance(
            node_id,
            instance_id,
        )

        if not isinstance(alarm, AlarmRecord):
            raise TypeError(
                "alarm must be an AlarmRecord"
            )

        if alarm.source != instance_id:
            raise AlarmSourceMismatchError(
                "AlarmRecord.source does not match NodeInstance"
            )

        if alarm.state is not AlarmState.ACTIVE:
            raise InvalidAlarmTransitionError(
                "new alarms must begin in ACTIVE state"
            )

        records = self._records(instance)

        if self._find(records, alarm.alarm_id) is not None:
            raise DuplicateAlarmError(
                f"alarm {alarm.alarm_id!r} already exists"
            )

        instance.alarms = records + (alarm,)

        self._registry.repository.save(node)

        return AlarmReceipt(
            disposition=AlarmDisposition.RAISED,
            alarm=alarm,
        )

    def acknowledge(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm_id: str,
        *,
        acknowledged_by: str,
        timestamp: datetime | None = None,
    ) -> AlarmReceipt:
        """Transition ACTIVE -> ACKNOWLEDGED."""

        instance, node = self._resolve_instance(
            node_id,
            instance_id,
        )

        records = self._records(instance)
        current = self._require_alarm(
            records,
            alarm_id,
        )

        if current.state is not AlarmState.ACTIVE:
            raise InvalidAlarmTransitionError(
                "only ACTIVE alarms can be acknowledged"
            )

        actor = self._normalize_actor(
            acknowledged_by
        )

        when = self._utc_timestamp(timestamp)

        if when < current.timestamp:
            raise InvalidAlarmTransitionError(
                "acknowledgement timestamp must not precede "
                "alarm timestamp"
            )

        updated = replace(
            current,
            state=AlarmState.ACKNOWLEDGED,
            acknowledged=True,
            acknowledged_by=actor,
            acknowledged_at=when,
        )

        instance.alarms = self._replace(
            records,
            updated,
        )

        self._registry.repository.save(node)

        return AlarmReceipt(
            disposition=AlarmDisposition.ACKNOWLEDGED,
            alarm=updated,
        )

    def resolve(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm_id: str,
        *,
        timestamp: datetime | None = None,
    ) -> AlarmReceipt:
        """Transition ACTIVE/ACKNOWLEDGED -> RESOLVED."""

        instance, node = self._resolve_instance(
            node_id,
            instance_id,
        )

        records = self._records(instance)
        current = self._require_alarm(
            records,
            alarm_id,
        )

        if current.state not in {
            AlarmState.ACTIVE,
            AlarmState.ACKNOWLEDGED,
        }:
            raise InvalidAlarmTransitionError(
                "only ACTIVE or ACKNOWLEDGED alarms "
                "can be resolved"
            )

        when = self._utc_timestamp(timestamp)

        if when < current.timestamp:
            raise InvalidAlarmTransitionError(
                "resolution timestamp must not precede "
                "alarm timestamp"
            )

        if (
            current.acknowledged_at is not None
            and when < current.acknowledged_at
        ):
            raise InvalidAlarmTransitionError(
                "resolution timestamp must not precede "
                "acknowledgement timestamp"
            )

        updated = replace(
            current,
            state=AlarmState.RESOLVED,
            resolved_at=when,
        )

        instance.alarms = self._replace(
            records,
            updated,
        )

        self._registry.repository.save(node)

        return AlarmReceipt(
            disposition=AlarmDisposition.RESOLVED,
            alarm=updated,
        )

    def close(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm_id: str,
        *,
        timestamp: datetime | None = None,
    ) -> AlarmReceipt:
        """Transition RESOLVED -> CLOSED."""

        instance, node = self._resolve_instance(
            node_id,
            instance_id,
        )

        records = self._records(instance)
        current = self._require_alarm(
            records,
            alarm_id,
        )

        if current.state is not AlarmState.RESOLVED:
            raise InvalidAlarmTransitionError(
                "only RESOLVED alarms can be closed"
            )

        when = self._utc_timestamp(timestamp)

        if current.resolved_at is None:
            raise AlarmServiceError(
                "RESOLVED alarm has no resolved_at timestamp"
            )

        if when < current.resolved_at:
            raise InvalidAlarmTransitionError(
                "close timestamp must not precede "
                "resolution timestamp"
            )

        updated = replace(
            current,
            state=AlarmState.CLOSED,
            closed_at=when,
        )

        instance.alarms = self._replace(
            records,
            updated,
        )

        self._registry.repository.save(node)

        return AlarmReceipt(
            disposition=AlarmDisposition.CLOSED,
            alarm=updated,
        )

    def get(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        alarm_id: str,
    ) -> AlarmRecord | None:
        """Return an alarm by id."""

        instance, _ = self._resolve_instance(
            node_id,
            instance_id,
        )

        return self._find(
            self._records(instance),
            alarm_id,
        )

    def list_all(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> tuple[AlarmRecord, ...]:
        """Return all alarms for a NodeInstance."""

        instance, _ = self._resolve_instance(
            node_id,
            instance_id,
        )

        return self._records(instance)

    def active(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> tuple[AlarmRecord, ...]:
        """Return alarms that still require attention."""

        return tuple(
            alarm
            for alarm in self.list_all(
                node_id,
                instance_id,
            )
            if alarm.requires_attention
        )

    def _resolve_instance(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ):
        if not isinstance(node_id, NodeId):
            raise TypeError(
                "node_id must be a NodeId"
            )

        if not isinstance(instance_id, NodeInstanceId):
            raise TypeError(
                "instance_id must be a NodeInstanceId"
            )

        node = self._registry.require(node_id)

        instance = self._find_instance(
            node.instances,
            instance_id,
        )

        if instance is None:
            raise NodeInstanceNotFoundError(
                f"NodeInstance {instance_id!s} is not registered "
                f"under Node {node_id.id!r}"
            )

        return instance, node

    @staticmethod
    def _records(
        instance: NodeInstance,
    ) -> tuple[AlarmRecord, ...]:
        value = getattr(
            instance,
            "alarms",
            (),
        )

        if value is None:
            return ()

        if not isinstance(value, tuple):
            raise AlarmServiceError(
                "NodeInstance.alarms must be a tuple"
            )

        records: list[AlarmRecord] = []

        for item in value:
            if not isinstance(item, AlarmRecord):
                raise AlarmServiceError(
                    "NodeInstance.alarms must contain "
                    "AlarmRecord objects"
                )

            records.append(item)

        return tuple(records)

    @staticmethod
    def _find(
        records: tuple[AlarmRecord, ...],
        alarm_id: str,
    ) -> AlarmRecord | None:
        normalized = AlarmService._normalize_alarm_id(
            alarm_id
        )

        for alarm in records:
            if alarm.alarm_id == normalized:
                return alarm

        return None

    @classmethod
    def _require_alarm(
        cls,
        records: tuple[AlarmRecord, ...],
        alarm_id: str,
    ) -> AlarmRecord:
        alarm = cls._find(
            records,
            alarm_id,
        )

        if alarm is None:
            raise AlarmNotFoundError(
                f"alarm {alarm_id!r} was not found"
            )

        return alarm

    @staticmethod
    def _replace(
        records: tuple[AlarmRecord, ...],
        updated: AlarmRecord,
    ) -> tuple[AlarmRecord, ...]:
        return tuple(
            updated
            if alarm.alarm_id == updated.alarm_id
            else alarm
            for alarm in records
        )

    @staticmethod
    def _find_instance(
        instances: tuple[NodeInstance, ...],
        instance_id: NodeInstanceId,
    ) -> NodeInstance | None:
        for instance in instances:
            if instance.instance_id == instance_id:
                return instance

        return None

    @staticmethod
    def _normalize_alarm_id(
        alarm_id: str,
    ) -> str:
        if not isinstance(alarm_id, str):
            raise TypeError(
                "alarm_id must be a string"
            )

        normalized = alarm_id.strip()

        if not normalized:
            raise ValueError(
                "alarm_id must not be empty"
            )

        return normalized

    @staticmethod
    def _normalize_actor(
        actor: str,
    ) -> str:
        if not isinstance(actor, str):
            raise TypeError(
                "acknowledged_by must be a string"
            )

        normalized = actor.strip()

        if not normalized:
            raise ValueError(
                "acknowledged_by must not be empty"
            )

        return normalized

    @staticmethod
    def _utc_timestamp(
        value: datetime | None,
    ) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)

        if not isinstance(value, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if value.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware and UTC"
            )

        offset = value.utcoffset()

        if offset is None or offset.total_seconds() != 0:
            raise ValueError(
                "timestamp must be expressed in UTC"
            )

        return value
