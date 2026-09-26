"""Signal Health transition alarm coordination.

ENG-013C — Signal Health -> Alarms / Recovery

SignalHealthTransitionAlarmService consumes one already-detected
SignalHealthTransition, asks SignalHealthAlarmPolicy for a lifecycle
decision, and delegates alarm lifecycle operations to the existing
AlarmService.

Logical alarm identity:

    (profile_id, service_id, path_name)

It does not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect or reclassify transitions;
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
from app.services.signal_health_alarm_policy import (
    SignalHealthAlarmAction,
    SignalHealthAlarmDecision,
    SignalHealthAlarmPolicy,
)
from app.services.signal_health_transition_alarm_factory import (
    SignalHealthTransitionAlarmFactory,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
)


SIGNAL_HEALTH_ALARM_TYPE = "SIGNAL_HEALTH"


@dataclass(frozen=True, slots=True)
class SignalHealthTransitionAlarmResult:
    """Result of one Signal Health alarm-policy operation."""

    transition: SignalHealthTransition | None
    decision: SignalHealthAlarmDecision
    alarm: AlarmRecord | None
    receipt: AlarmReceipt | None


class SignalHealthTransitionAlarmService:
    """Coordinate Signal Health transitions with AlarmService."""

    def __init__(
        self,
        *,
        alarm_service: AlarmService,
        policy: SignalHealthAlarmPolicy | None = None,
        factory: SignalHealthTransitionAlarmFactory | None = None,
    ) -> None:
        if not isinstance(alarm_service, AlarmService):
            raise TypeError(
                "alarm_service must be an AlarmService"
            )

        if (
            policy is not None
            and not isinstance(
                policy,
                SignalHealthAlarmPolicy,
            )
        ):
            raise TypeError(
                "policy must be a "
                "SignalHealthAlarmPolicy or None"
            )

        if (
            factory is not None
            and not isinstance(
                factory,
                SignalHealthTransitionAlarmFactory,
            )
        ):
            raise TypeError(
                "factory must be a "
                "SignalHealthTransitionAlarmFactory or None"
            )

        self._alarm_service = alarm_service
        self._policy = (
            policy
            or SignalHealthAlarmPolicy()
        )
        self._factory = (
            factory
            or SignalHealthTransitionAlarmFactory()
        )

    @property
    def alarm_service(self) -> AlarmService:
        return self._alarm_service

    @property
    def policy(self) -> SignalHealthAlarmPolicy:
        return self._policy

    @property
    def factory(
        self,
    ) -> SignalHealthTransitionAlarmFactory:
        return self._factory

    def process_transition(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: SignalHealthTransition | None,
        timestamp: datetime,
    ) -> SignalHealthTransitionAlarmResult:
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
            return SignalHealthTransitionAlarmResult(
                transition=None,
                decision=decision,
                alarm=None,
                receipt=None,
            )

        active_alarm = self._active_signal_health_alarm(
            node_id=node_id,
            instance_id=instance_id,
            transition=transition,
        )

        if decision.action is SignalHealthAlarmAction.RAISE:
            if active_alarm is not None:
                return SignalHealthTransitionAlarmResult(
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
                return SignalHealthTransitionAlarmResult(
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

            return SignalHealthTransitionAlarmResult(
                transition=transition,
                decision=decision,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        if decision.action is SignalHealthAlarmAction.RESOLVE:
            if active_alarm is None:
                return SignalHealthTransitionAlarmResult(
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

            return SignalHealthTransitionAlarmResult(
                transition=transition,
                decision=decision,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        return SignalHealthTransitionAlarmResult(
            transition=transition,
            decision=decision,
            alarm=active_alarm,
            receipt=None,
        )

    def _active_signal_health_alarm(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: SignalHealthTransition,
    ) -> AlarmRecord | None:
        """Return attention alarm for the same logical Signal identity."""

        current = transition.current

        for alarm in self._alarm_service.active(
            node_id,
            instance_id,
        ):
            if alarm.alarm_type != SIGNAL_HEALTH_ALARM_TYPE:
                continue

            attributes = alarm.attributes or {}

            if (
                attributes.get("profile_id")
                != current.profile_id
            ):
                continue

            if (
                attributes.get("service_id")
                != current.service_id
            ):
                continue

            if (
                attributes.get("path_name")
                != current.path_name
            ):
                continue

            return alarm

        return None

    @staticmethod
    def _validate_inputs(
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        transition: SignalHealthTransition | None,
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
                SignalHealthTransition,
            )
        ):
            raise TypeError(
                "transition must be a "
                "SignalHealthTransition or None"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )
