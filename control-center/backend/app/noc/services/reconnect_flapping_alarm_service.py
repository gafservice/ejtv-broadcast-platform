"""Operational alarm coordination for reconnect flapping.

ENG-013B — Node SDK

ReconnectFlappingAlarmService coordinates the lifecycle of
RECONNECT_FLAPPING alarms.

Alarm identity is scoped by LogicalSessionIdentity so independent
multimedia relationships may flap simultaneously without interfering
with each other.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.noc.domain.logical_session_identity import (
    LogicalSessionIdentity,
)
from app.noc.domain.node_alarm import AlarmRecord
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.alarm_service import (
    AlarmReceipt,
    AlarmService,
)
from app.noc.services.reconnect_flapping_alarm_factory import (
    RECONNECT_FLAPPING,
    ReconnectFlappingAlarmFactory,
)
from app.noc.services.reconnect_flapping_evaluator import (
    ReconnectFlappingEvaluation,
    ReconnectFlappingState,
)


@dataclass(frozen=True, slots=True)
class ReconnectFlappingAlarmResult:
    """Result of reconnect flapping alarm coordination."""

    evaluation: ReconnectFlappingEvaluation
    alarm: AlarmRecord | None
    receipt: AlarmReceipt | None


class ReconnectFlappingAlarmService:
    """Coordinate RECONNECT_FLAPPING alarm lifecycle."""

    def __init__(
        self,
        *,
        alarm_service: AlarmService,
        alarm_factory: ReconnectFlappingAlarmFactory | None = None,
    ) -> None:
        if not isinstance(alarm_service, AlarmService):
            raise TypeError(
                "alarm_service must be an AlarmService"
            )

        if (
            alarm_factory is not None
            and not isinstance(
                alarm_factory,
                ReconnectFlappingAlarmFactory,
            )
        ):
            raise TypeError(
                "alarm_factory must be a "
                "ReconnectFlappingAlarmFactory or None"
            )

        self._alarm_service = alarm_service
        self._alarm_factory = (
            alarm_factory
            if alarm_factory is not None
            else ReconnectFlappingAlarmFactory()
        )

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        evaluation: ReconnectFlappingEvaluation,
        timestamp: datetime,
    ) -> ReconnectFlappingAlarmResult:
        """Coordinate one reconnect flapping evaluation."""

        self._validate_inputs(
            node_id=node_id,
            instance_id=instance_id,
            evaluation=evaluation,
            timestamp=timestamp,
        )

        active_alarm = self._active_identity_alarm(
            node_id,
            instance_id,
            evaluation.identity,
        )

        if (
            evaluation.state
            is ReconnectFlappingState.STABLE
        ):
            if active_alarm is None:
                return ReconnectFlappingAlarmResult(
                    evaluation=evaluation,
                    alarm=None,
                    receipt=None,
                )

            receipt = self._alarm_service.resolve(
                node_id,
                instance_id,
                active_alarm.alarm_id,
                timestamp=timestamp,
            )

            return ReconnectFlappingAlarmResult(
                evaluation=evaluation,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        if active_alarm is not None:
            return ReconnectFlappingAlarmResult(
                evaluation=evaluation,
                alarm=active_alarm,
                receipt=None,
            )

        alarm = self._alarm_factory.create(
            evaluation=evaluation,
            source=instance_id,
            timestamp=timestamp,
        )

        receipt = self._alarm_service.raise_alarm(
            node_id,
            instance_id,
            alarm,
        )

        return ReconnectFlappingAlarmResult(
            evaluation=evaluation,
            alarm=receipt.alarm,
            receipt=receipt,
        )

    def _active_identity_alarm(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        identity: LogicalSessionIdentity,
    ) -> AlarmRecord | None:
        """Return active flapping alarm for one logical identity."""

        expected_attributes = {
            "protocol": identity.protocol.value,
            "role": identity.role.value,
            "path": (
                identity.path
                if identity.path is not None
                else ""
            ),
            "remote_ip": identity.remote_ip,
        }

        for alarm in self._alarm_service.active(
            node_id,
            instance_id,
        ):
            if alarm.alarm_type != RECONNECT_FLAPPING:
                continue

            if all(
                alarm.attributes.get(key) == value
                for key, value in expected_attributes.items()
            ):
                return alarm

        return None

    @staticmethod
    def _validate_inputs(
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        evaluation: ReconnectFlappingEvaluation,
        timestamp: datetime,
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
            evaluation,
            ReconnectFlappingEvaluation,
        ):
            raise TypeError(
                "evaluation must be a "
                "ReconnectFlappingEvaluation"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if timestamp.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware and UTC"
            )

        offset = timestamp.utcoffset()

        if (
            offset is None
            or offset != timedelta(0)
        ):
            raise ValueError(
                "timestamp must be expressed in UTC"
            )
