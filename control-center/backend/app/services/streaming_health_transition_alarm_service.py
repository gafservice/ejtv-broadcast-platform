"""Stream Health transition alarm coordination.

ENG-013B — Stream Health Contract Block 5

StreamingHealthTransitionAlarmService consumes one already-detected
StreamingHealthTransition, asks the Stream Health alarm policy for a
lifecycle decision, and delegates alarm lifecycle operations to the
existing AlarmService.

It does not:

- evaluate Stream Health;
- stabilize Stream Health;
- detect Stream Health transitions;
- persist alarms directly;
- write alarm history or evidence directly.

AlarmService remains the operational alarm lifecycle authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.noc.domain.node_alarm import AlarmRecord
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.alarm_service import (
    AlarmReceipt,
    AlarmService,
)
from app.services.streaming_health_alarm_policy import (
    StreamingHealthAlarmAction,
    StreamingHealthAlarmDecision,
    StreamingHealthAlarmPolicy,
)
from app.services.streaming_health_transition_alarm_factory import (
    StreamingHealthTransitionAlarmFactory,
)
from app.services.streaming_health_transition_detector import (
    StreamingHealthTransition,
)


STREAM_HEALTH_ALARM_TYPE = "STREAM_HEALTH"


@dataclass(frozen=True, slots=True)
class StreamingHealthTransitionAlarmResult:
    """Result of one Stream Health alarm-policy operation."""

    transition: StreamingHealthTransition | None
    decision: StreamingHealthAlarmDecision
    alarm: AlarmRecord | None
    receipt: AlarmReceipt | None


class StreamingHealthTransitionAlarmService:
    """Coordinate semantic Stream Health transitions with AlarmService."""

    def __init__(
        self,
        *,
        alarm_service: AlarmService,
        policy: StreamingHealthAlarmPolicy | None = None,
        factory: StreamingHealthTransitionAlarmFactory | None = None,
    ) -> None:
        if not isinstance(alarm_service, AlarmService):
            raise TypeError(
                "alarm_service must be an AlarmService"
            )

        if (
            policy is not None
            and not isinstance(
                policy,
                StreamingHealthAlarmPolicy,
            )
        ):
            raise TypeError(
                "policy must be a StreamingHealthAlarmPolicy or None"
            )

        if (
            factory is not None
            and not isinstance(
                factory,
                StreamingHealthTransitionAlarmFactory,
            )
        ):
            raise TypeError(
                "factory must be a "
                "StreamingHealthTransitionAlarmFactory or None"
            )

        self._alarm_service = alarm_service
        self._policy = (
            policy
            or StreamingHealthAlarmPolicy()
        )
        self._factory = (
            factory
            or StreamingHealthTransitionAlarmFactory()
        )

    @property
    def alarm_service(self) -> AlarmService:
        return self._alarm_service

    @property
    def policy(self) -> StreamingHealthAlarmPolicy:
        return self._policy

    @property
    def factory(
        self,
    ) -> StreamingHealthTransitionAlarmFactory:
        return self._factory

    def process_transition(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: StreamingHealthTransition | None,
        timestamp: datetime,
    ) -> StreamingHealthTransitionAlarmResult:
        """Apply alarm policy to one already-detected transition."""

        self._validate_inputs(
            node_id=node_id,
            instance_id=instance_id,
            transition=transition,
            timestamp=timestamp,
        )

        decision = self._policy.evaluate(
            transition=transition,
        )

        if transition is None:
            return StreamingHealthTransitionAlarmResult(
                transition=None,
                decision=decision,
                alarm=None,
                receipt=None,
            )

        active_alarm = self._active_stream_health_alarm(
            node_id,
            instance_id,
        )

        if decision.action is StreamingHealthAlarmAction.RAISE:
            if active_alarm is not None:
                return StreamingHealthTransitionAlarmResult(
                    transition=transition,
                    decision=decision,
                    alarm=active_alarm,
                    receipt=None,
                )

            alarm = self._factory.create(
                decision=decision,
                source=instance_id,
                timestamp=timestamp,
            )

            if alarm is None:
                return StreamingHealthTransitionAlarmResult(
                    transition=transition,
                    decision=decision,
                    alarm=None,
                    receipt=None,
                )

            receipt = self._alarm_service.raise_alarm(
                node_id,
                instance_id,
                alarm,
            )

            return StreamingHealthTransitionAlarmResult(
                transition=transition,
                decision=decision,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        if decision.action is StreamingHealthAlarmAction.RESOLVE:
            if active_alarm is None:
                return StreamingHealthTransitionAlarmResult(
                    transition=transition,
                    decision=decision,
                    alarm=None,
                    receipt=None,
                )

            receipt = self._alarm_service.resolve(
                node_id,
                instance_id,
                active_alarm.alarm_id,
                timestamp=timestamp,
            )

            return StreamingHealthTransitionAlarmResult(
                transition=transition,
                decision=decision,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        return StreamingHealthTransitionAlarmResult(
            transition=transition,
            decision=decision,
            alarm=active_alarm,
            receipt=None,
        )

    def _active_stream_health_alarm(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> AlarmRecord | None:
        """Return the current Stream Health attention alarm, if any."""

        for alarm in self._alarm_service.active(
            node_id,
            instance_id,
        ):
            if alarm.alarm_type == STREAM_HEALTH_ALARM_TYPE:
                return alarm

        return None

    @staticmethod
    def _validate_inputs(
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: StreamingHealthTransition | None,
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

        if (
            transition is not None
            and not isinstance(
                transition,
                StreamingHealthTransition,
            )
        ):
            raise TypeError(
                "transition must be a "
                "StreamingHealthTransition or None"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )
