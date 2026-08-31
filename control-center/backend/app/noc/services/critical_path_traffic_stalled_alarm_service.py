"""Critical-path stalled-traffic alarm coordination.

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
from app.noc.services.critical_path_traffic_evaluator import (
    CriticalPathTrafficState,
)
from app.noc.services.critical_path_traffic_stabilizer import (
    CriticalPathTrafficStabilization,
)
from app.noc.services.critical_path_traffic_stalled_alarm_factory import (
    CRITICAL_PATH_TRAFFIC_STALLED,
    CriticalPathTrafficStalledAlarmFactory,
)


@dataclass(frozen=True, slots=True)
class CriticalPathTrafficStalledAlarmResult:
    """Result of one stalled-traffic alarm coordination cycle."""

    stabilization: CriticalPathTrafficStabilization
    alarm: AlarmRecord | None
    receipt: AlarmReceipt | None


class CriticalPathTrafficStalledAlarmService:
    """Coordinate critical-path stalled-traffic alarm lifecycle."""

    def __init__(
        self,
        *,
        alarm_service: AlarmService,
        alarm_factory: CriticalPathTrafficStalledAlarmFactory | None = None,
    ) -> None:
        if not isinstance(alarm_service, AlarmService):
            raise TypeError(
                "alarm_service must be an AlarmService"
            )

        if (
            alarm_factory is not None
            and not isinstance(
                alarm_factory,
                CriticalPathTrafficStalledAlarmFactory,
            )
        ):
            raise TypeError(
                "alarm_factory must be a "
                "CriticalPathTrafficStalledAlarmFactory or None"
            )

        self._alarm_service = alarm_service
        self._alarm_factory = (
            alarm_factory
            or CriticalPathTrafficStalledAlarmFactory()
        )

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        stabilization: CriticalPathTrafficStabilization,
        timestamp: datetime,
    ) -> CriticalPathTrafficStalledAlarmResult:
        """Raise, preserve or resolve one stalled-traffic alarm."""

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

        state = stabilization.evaluation.state

        # Only positive evidence of traffic recovery resolves the alarm.
        if state is CriticalPathTrafficState.HEALTHY:
            if active_alarm is None:
                return CriticalPathTrafficStalledAlarmResult(
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

            return CriticalPathTrafficStalledAlarmResult(
                stabilization=stabilization,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        # UNKNOWN is absence of reliable traffic evidence.
        # INACTIVE belongs to path availability semantics.
        # Neither one proves that traffic recovered.
        if state in (
            CriticalPathTrafficState.UNKNOWN,
            CriticalPathTrafficState.INACTIVE,
        ):
            return CriticalPathTrafficStalledAlarmResult(
                stabilization=stabilization,
                alarm=active_alarm,
                receipt=None,
            )

        if not stabilization.confirmed_stalled:
            return CriticalPathTrafficStalledAlarmResult(
                stabilization=stabilization,
                alarm=active_alarm,
                receipt=None,
            )

        if active_alarm is not None:
            return CriticalPathTrafficStalledAlarmResult(
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

        return CriticalPathTrafficStalledAlarmResult(
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
        """Return active stalled-traffic alarm for one critical path."""

        for alarm in self._alarm_service.active(
            node_id,
            instance_id,
        ):
            if (
                alarm.alarm_type
                == CRITICAL_PATH_TRAFFIC_STALLED
                and alarm.attributes.get("path") == path
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
        stabilization: CriticalPathTrafficStabilization,
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
            CriticalPathTrafficStabilization,
        ):
            raise TypeError(
                "stabilization must be a "
                "CriticalPathTrafficStabilization"
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
