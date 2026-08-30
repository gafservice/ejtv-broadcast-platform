"""Critical-path unavailable alarm coordination.

ENG-013B — Node SDK
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmState,
)
from app.noc.domain.node_id import NodeId
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.alarm_service import (
    AlarmReceipt,
    AlarmService,
)
from app.noc.services.critical_path_availability_evaluator import (
    CriticalPathAvailabilityState,
)
from app.noc.services.critical_path_availability_stabilizer import (
    CriticalPathAvailabilityStabilization,
)
from app.noc.services.critical_path_unavailable_alarm_factory import (
    CRITICAL_PATH_UNAVAILABLE,
    CriticalPathUnavailableAlarmFactory,
)


@dataclass(frozen=True, slots=True)
class CriticalPathUnavailableAlarmResult:
    """Result of one unavailable-path alarm coordination cycle."""

    stabilization: CriticalPathAvailabilityStabilization
    alarm: AlarmRecord | None
    receipt: AlarmReceipt | None


class CriticalPathUnavailableAlarmService:
    """Coordinate unavailable critical-path alarm lifecycle."""

    def __init__(
        self,
        *,
        alarm_service: AlarmService,
        alarm_factory: CriticalPathUnavailableAlarmFactory | None = None,
    ) -> None:
        if not isinstance(alarm_service, AlarmService):
            raise TypeError(
                "alarm_service must be an AlarmService"
            )

        if (
            alarm_factory is not None
            and not isinstance(
                alarm_factory,
                CriticalPathUnavailableAlarmFactory,
            )
        ):
            raise TypeError(
                "alarm_factory must be a "
                "CriticalPathUnavailableAlarmFactory or None"
            )

        self._alarm_service = alarm_service
        self._alarm_factory = (
            alarm_factory
            or CriticalPathUnavailableAlarmFactory()
        )

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        stabilization: CriticalPathAvailabilityStabilization,
        timestamp: datetime,
    ) -> CriticalPathUnavailableAlarmResult:
        """Raise, preserve or resolve one path availability alarm."""

        self._validate_inputs(
            node_id=node_id,
            instance_id=instance_id,
            stabilization=stabilization,
            timestamp=timestamp,
        )

        path = stabilization.evaluation.policy.path

        active_alarm = self._active_path_alarm(
            node_id,
            instance_id,
            path,
        )

        if (
            stabilization.evaluation.state
            is CriticalPathAvailabilityState.AVAILABLE
        ):
            if active_alarm is None:
                return CriticalPathUnavailableAlarmResult(
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

            return CriticalPathUnavailableAlarmResult(
                stabilization=stabilization,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        if not stabilization.confirmed_unavailable:
            return CriticalPathUnavailableAlarmResult(
                stabilization=stabilization,
                alarm=active_alarm,
                receipt=None,
            )

        if active_alarm is not None:
            return CriticalPathUnavailableAlarmResult(
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

        return CriticalPathUnavailableAlarmResult(
            stabilization=stabilization,
            alarm=receipt.alarm,
            receipt=receipt,
        )

    def _active_path_alarm(
        self,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        path: str,
    ) -> AlarmRecord | None:
        """Return active unavailable alarm for one critical path."""

        for alarm in self._alarm_service.active(
            node_id,
            instance_id,
        ):
            if (
                alarm.alarm_type
                == CRITICAL_PATH_UNAVAILABLE
                and alarm.attributes.get("path")
                == path
                and alarm.state
                in (
                    AlarmState.ACTIVE,
                    AlarmState.ACKNOWLEDGED,
                )
            ):
                return alarm

        return None

    @staticmethod
    def _validate_inputs(
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        stabilization: CriticalPathAvailabilityStabilization,
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
            CriticalPathAvailabilityStabilization,
        ):
            raise TypeError(
                "stabilization must be a "
                "CriticalPathAvailabilityStabilization"
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

        if offset is None or offset != timedelta(0):
            raise ValueError(
                "timestamp must be expressed in UTC"
            )
