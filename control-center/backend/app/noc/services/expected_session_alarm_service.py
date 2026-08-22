"""Operational alarm coordination for expected multimedia sessions.

ENG-013B — Node SDK

ExpectedSessionAlarmService coordinates the lifecycle of
EXPECTED_SESSION_MISSING alarms.

Alarm identity is scoped by policy_id. This allows multiple independent
expected-session alarms of the same alarm_type to coexist on one node
instance.

The service does not evaluate session snapshots or maintain temporal
missing-state history.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.noc.domain.node_alarm import AlarmRecord
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.alarm_service import (
    AlarmReceipt,
    AlarmService,
)
from app.noc.services.expected_session_alarm_factory import (
    EXPECTED_SESSION_MISSING,
    ExpectedSessionAlarmFactory,
)
from app.noc.services.expected_session_evaluator import (
    ExpectedSessionState,
)
from app.noc.services.expected_session_stabilizer import (
    ExpectedSessionStabilization,
)


@dataclass(frozen=True, slots=True)
class ExpectedSessionAlarmResult:
    """Result of expected-session alarm coordination."""

    stabilization: ExpectedSessionStabilization
    alarm: AlarmRecord | None
    receipt: AlarmReceipt | None


class ExpectedSessionAlarmService:
    """Coordinate EXPECTED_SESSION_MISSING alarm lifecycle."""

    def __init__(
        self,
        *,
        alarm_service: AlarmService,
        alarm_factory: ExpectedSessionAlarmFactory | None = None,
    ) -> None:
        if not isinstance(alarm_service, AlarmService):
            raise TypeError(
                "alarm_service must be an AlarmService"
            )

        if (
            alarm_factory is not None
            and not isinstance(
                alarm_factory,
                ExpectedSessionAlarmFactory,
            )
        ):
            raise TypeError(
                "alarm_factory must be an "
                "ExpectedSessionAlarmFactory or None"
            )

        self._alarm_service = alarm_service
        self._alarm_factory = (
            alarm_factory
            if alarm_factory is not None
            else ExpectedSessionAlarmFactory()
        )

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        stabilization: ExpectedSessionStabilization,
        timestamp: datetime,
    ) -> ExpectedSessionAlarmResult:
        """Coordinate one stabilized expected-session observation."""

        self._validate_inputs(
            node_id=node_id,
            instance_id=instance_id,
            stabilization=stabilization,
            timestamp=timestamp,
        )

        policy_id = (
            stabilization.evaluation.policy.policy_id
        )

        active_alarm = self._active_policy_alarm(
            node_id,
            instance_id,
            policy_id,
        )

        if (
            stabilization.evaluation.state
            is ExpectedSessionState.PRESENT
        ):
            if active_alarm is None:
                return ExpectedSessionAlarmResult(
                    stabilization=stabilization,
                    alarm=None,
                    receipt=None,
                )

            receipt = self._alarm_service.resolve(
                node_id,
                instance_id,
                active_alarm.alarm_id,
                timestamp=timestamp,
            )

            return ExpectedSessionAlarmResult(
                stabilization=stabilization,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        if not stabilization.confirmed_missing:
            return ExpectedSessionAlarmResult(
                stabilization=stabilization,
                alarm=active_alarm,
                receipt=None,
            )

        if active_alarm is not None:
            return ExpectedSessionAlarmResult(
                stabilization=stabilization,
                alarm=active_alarm,
                receipt=None,
            )

        alarm = self._alarm_factory.create(
            stabilization=stabilization,
            source=instance_id,
            timestamp=timestamp,
        )

        receipt = self._alarm_service.raise_alarm(
            node_id,
            instance_id,
            alarm,
        )

        return ExpectedSessionAlarmResult(
            stabilization=stabilization,
            alarm=receipt.alarm,
            receipt=receipt,
        )

    def _active_policy_alarm(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        policy_id: str,
    ) -> AlarmRecord | None:
        """Return active missing-session alarm for one policy."""

        for alarm in self._alarm_service.active(
            node_id,
            instance_id,
        ):
            if (
                alarm.alarm_type
                == EXPECTED_SESSION_MISSING
                and alarm.attributes.get("policy_id")
                == policy_id
            ):
                return alarm

        return None

    @staticmethod
    def _validate_inputs(
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        stabilization: ExpectedSessionStabilization,
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
            stabilization,
            ExpectedSessionStabilization,
        ):
            raise TypeError(
                "stabilization must be an "
                "ExpectedSessionStabilization"
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
