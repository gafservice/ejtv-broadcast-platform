"""Recovery service for durable NOC alarms after process restart.

ENG-013B — persistent operational history.

AlarmRecoveryService reconciles durable alarms with the live Node
projection after the canonical Node runtime has been bootstrapped.

Recovery is not a new alarm opening. The original alarm identity and
AlarmState are preserved, while RECOVERED_AT_STARTUP records evidence
that the durable alarm was restored into the live runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.noc.domain.node import Node
from app.noc.domain.node_alarm import AlarmRecord
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import (
    NodeInstance,
    NodeInstanceId,
)
from app.noc.history.alarm_transition import (
    AlarmTransition,
    AlarmTransitionType,
    make_alarm_transition_id,
)
from app.noc.history.repository import AlarmHistoryRepository
from app.noc.registry.registry import NodeRegistry


@dataclass(frozen=True, slots=True)
class AlarmRecoveryResult:
    """Summary of one alarm recovery execution."""

    recovered: tuple[AlarmRecord, ...]

    @property
    def recovered_count(self) -> int:
        return len(self.recovered)


class AlarmRecoveryService:
    """Restore durable active alarms into the live Node projection."""

    def __init__(
        self,
        registry: NodeRegistry,
        history_repository: AlarmHistoryRepository,
    ) -> None:
        if not isinstance(registry, NodeRegistry):
            raise TypeError(
                "registry must be a NodeRegistry"
            )

        if not isinstance(
            history_repository,
            AlarmHistoryRepository,
        ):
            raise TypeError(
                "history_repository must implement "
                "AlarmHistoryRepository"
            )

        self._registry = registry
        self._history_repository = history_repository

    def recover(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        timestamp: datetime | None = None,
    ) -> AlarmRecoveryResult:
        """Recover durable alarms requiring operator attention."""

        when = self._utc_timestamp(
            timestamp
            if timestamp is not None
            else datetime.now(timezone.utc)
        )

        instance, node = self._resolve_instance(
            node_id,
            instance_id,
        )

        durable_alarms = self._history_repository.list_active(
            node_id=node_id,
            instance_id=instance_id,
        )

        recovered: list[AlarmRecord] = []
        records = tuple(instance.alarms or ())

        for alarm in durable_alarms:
            existing = self._find(
                records,
                alarm.alarm_id,
            )

            if existing is not None:
                if existing != alarm:
                    raise RuntimeError(
                        "live alarm conflicts with durable alarm "
                        f"{alarm.alarm_id!r}"
                    )

                continue

            transition = AlarmTransition(
                transition_id=make_alarm_transition_id(
                    alarm_id=alarm.alarm_id,
                    transition_type=(
                        AlarmTransitionType.RECOVERED_AT_STARTUP
                    ),
                    timestamp=when,
                    source=instance_id,
                    state=alarm.state,
                ),
                alarm_id=alarm.alarm_id,
                transition_type=(
                    AlarmTransitionType.RECOVERED_AT_STARTUP
                ),
                timestamp=when,
                source=instance_id,
                state=alarm.state,
                actor=None,
                metadata=alarm.attributes,
            )

            self._history_repository.record_lifecycle(
                node_id=node_id,
                instance_id=instance_id,
                alarm=alarm,
                transition=transition,
            )

            records = records + (alarm,)
            recovered.append(alarm)

        if recovered:
            instance.alarms = records
            self._registry.repository.save(node)

        return AlarmRecoveryResult(
            recovered=tuple(recovered)
        )

    def _resolve_instance(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> tuple[NodeInstance, Node]:
        node = self._registry.require(node_id)

        instance = next(
            (
                candidate
                for candidate in node.instances
                if candidate.instance_id == instance_id
            ),
            None,
        )

        if instance is None:
            raise RuntimeError(
                f"NodeInstance {instance_id!s} not found"
            )

        return instance, node

    @staticmethod
    def _find(
        records: tuple[AlarmRecord, ...],
        alarm_id: str,
    ) -> AlarmRecord | None:
        return next(
            (
                alarm
                for alarm in records
                if alarm.alarm_id == alarm_id
            ),
            None,
        )

    @staticmethod
    def _utc_timestamp(value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "timestamp must be timezone-aware"
            )

        normalized = value.astimezone(timezone.utc)

        if normalized.utcoffset() != timezone.utc.utcoffset(
            normalized
        ):
            raise ValueError(
                "timestamp must normalize to UTC"
            )

        return normalized
