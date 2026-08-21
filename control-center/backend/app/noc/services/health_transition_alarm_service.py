"""Health transition alarm coordination service for the NOC.

ENG-013B — Node SDK

HealthTransitionAlarmService coordinates NodeHealth transitions with the
operational AlarmService lifecycle.

Responsibilities:
- detect NodeHealth transitions;
- raise one operational alarm for a health degradation;
- avoid duplicate active health alarms;
- resolve the active health alarm when health recovers.

It does not evaluate health, acknowledge alarms, close alarms, or persist
AlarmRecord objects directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.noc.domain.node_alarm import AlarmRecord
from app.noc.domain.node_health import NodeHealth
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.alarm_service import (
    AlarmReceipt,
    AlarmService,
)
from app.noc.services.health_transition_alarm_factory import (
    HealthTransitionAlarmFactory,
)
from app.noc.services.health_transition_detector import (
    HealthTransition,
    HealthTransitionDetector,
    HealthTransitionKind,
)


HEALTH_ALARM_TYPE = "NODE_HEALTH_DEGRADED"


@dataclass(frozen=True, slots=True)
class HealthTransitionAlarmResult:
    """Result of one health-transition alarm processing operation."""

    transition: HealthTransition | None
    alarm: AlarmRecord | None
    receipt: AlarmReceipt | None


class HealthTransitionAlarmService:
    """Coordinate NodeHealth transitions with operational alarms."""

    def __init__(
        self,
        *,
        alarm_service: AlarmService,
        detector: HealthTransitionDetector | None = None,
        factory: HealthTransitionAlarmFactory | None = None,
    ) -> None:
        if not isinstance(alarm_service, AlarmService):
            raise TypeError(
                "alarm_service must be an AlarmService"
            )

        if (
            detector is not None
            and not isinstance(
                detector,
                HealthTransitionDetector,
            )
        ):
            raise TypeError(
                "detector must be a HealthTransitionDetector or None"
            )

        if (
            factory is not None
            and not isinstance(
                factory,
                HealthTransitionAlarmFactory,
            )
        ):
            raise TypeError(
                "factory must be a HealthTransitionAlarmFactory or None"
            )

        self._alarm_service = alarm_service
        self._detector = (
            detector
            or HealthTransitionDetector()
        )
        self._factory = (
            factory
            or HealthTransitionAlarmFactory()
        )

    @property
    def alarm_service(self) -> AlarmService:
        return self._alarm_service

    @property
    def detector(self) -> HealthTransitionDetector:
        return self._detector

    @property
    def factory(self) -> HealthTransitionAlarmFactory:
        return self._factory

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        previous: NodeHealth | None,
        current: NodeHealth,
        timestamp: datetime,
    ) -> HealthTransitionAlarmResult:
        """Process one NodeHealth change against alarm lifecycle."""

        self._validate_inputs(
            node_id=node_id,
            instance_id=instance_id,
            previous=previous,
            current=current,
            timestamp=timestamp,
        )

        transition = self._detector.detect(
            previous,
            current,
        )

        if transition is None:
            return HealthTransitionAlarmResult(
                transition=None,
                alarm=None,
                receipt=None,
            )

        active_alarm = self._active_health_alarm(
            node_id,
            instance_id,
        )

        if transition.kind is HealthTransitionKind.DEGRADED:
            if active_alarm is not None:
                return HealthTransitionAlarmResult(
                    transition=transition,
                    alarm=active_alarm,
                    receipt=None,
                )

            alarm = self._factory.create(
                transition=transition,
                source=instance_id,
                timestamp=timestamp,
            )

            if alarm is None:
                return HealthTransitionAlarmResult(
                    transition=transition,
                    alarm=None,
                    receipt=None,
                )

            receipt = self._alarm_service.raise_alarm(
                node_id,
                instance_id,
                alarm,
            )

            return HealthTransitionAlarmResult(
                transition=transition,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        if (
            transition.kind is HealthTransitionKind.RECOVERED
            and active_alarm is not None
        ):
            receipt = self._alarm_service.resolve(
                node_id,
                instance_id,
                active_alarm.alarm_id,
                timestamp=timestamp,
            )

            return HealthTransitionAlarmResult(
                transition=transition,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        return HealthTransitionAlarmResult(
            transition=transition,
            alarm=active_alarm,
            receipt=None,
        )

    def _active_health_alarm(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
    ) -> AlarmRecord | None:
        """Return the active NodeHealth alarm, when one exists."""

        for alarm in self._alarm_service.active(
            node_id,
            instance_id,
        ):
            if alarm.alarm_type == HEALTH_ALARM_TYPE:
                return alarm

        return None

    @staticmethod
    def _validate_inputs(
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        previous: NodeHealth | None,
        current: NodeHealth,
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
            previous is not None
            and not isinstance(
                previous,
                NodeHealth,
            )
        ):
            raise TypeError(
                "previous must be a NodeHealth or None"
            )

        if not isinstance(current, NodeHealth):
            raise TypeError(
                "current must be a NodeHealth"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )
