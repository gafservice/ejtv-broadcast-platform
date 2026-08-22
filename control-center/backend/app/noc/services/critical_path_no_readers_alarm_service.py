"""Operational alarm coordination for critical paths without readers.

ENG-013B — Node SDK

CriticalPathNoReadersAlarmService coordinates the lifecycle of
CRITICAL_PATH_NO_READERS alarms.

Alarm identity is scoped by critical path name so multiple critical
paths may independently enter and recover from the no-readers condition.
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
from app.noc.services.critical_path_no_readers_alarm_factory import (
    CRITICAL_PATH_NO_READERS,
    CriticalPathNoReadersAlarmFactory,
)
from app.noc.services.critical_path_reader_evaluator import (
    CriticalPathReaderState,
)
from app.noc.services.critical_path_reader_stabilizer import (
    CriticalPathReaderStabilization,
)


@dataclass(frozen=True, slots=True)
class CriticalPathNoReadersAlarmResult:
    """Result of critical-path no-readers alarm coordination."""

    stabilization: CriticalPathReaderStabilization
    alarm: AlarmRecord | None
    receipt: AlarmReceipt | None


class CriticalPathNoReadersAlarmService:
    """Coordinate CRITICAL_PATH_NO_READERS alarm lifecycle."""

    def __init__(
        self,
        *,
        alarm_service: AlarmService,
        alarm_factory: CriticalPathNoReadersAlarmFactory | None = None,
    ) -> None:
        if not isinstance(alarm_service, AlarmService):
            raise TypeError(
                "alarm_service must be an AlarmService"
            )

        if (
            alarm_factory is not None
            and not isinstance(
                alarm_factory,
                CriticalPathNoReadersAlarmFactory,
            )
        ):
            raise TypeError(
                "alarm_factory must be a "
                "CriticalPathNoReadersAlarmFactory or None"
            )

        self._alarm_service = alarm_service
        self._alarm_factory = (
            alarm_factory
            if alarm_factory is not None
            else CriticalPathNoReadersAlarmFactory()
        )

    def process(
        self,
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        stabilization: CriticalPathReaderStabilization,
        timestamp: datetime,
    ) -> CriticalPathNoReadersAlarmResult:
        """Coordinate one stabilized critical-path observation."""

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
            is not CriticalPathReaderState.NO_READERS
        ):
            if active_alarm is None:
                return CriticalPathNoReadersAlarmResult(
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

            return CriticalPathNoReadersAlarmResult(
                stabilization=stabilization,
                alarm=receipt.alarm,
                receipt=receipt,
            )

        if not stabilization.confirmed_no_readers:
            return CriticalPathNoReadersAlarmResult(
                stabilization=stabilization,
                alarm=active_alarm,
                receipt=None,
            )

        if active_alarm is not None:
            return CriticalPathNoReadersAlarmResult(
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

        return CriticalPathNoReadersAlarmResult(
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
        """Return active no-readers alarm for one path."""

        for alarm in self._alarm_service.active(
            node_id,
            instance_id,
        ):
            if (
                alarm.alarm_type
                == CRITICAL_PATH_NO_READERS
                and alarm.attributes.get("path")
                == path
            ):
                return alarm

        return None

    @staticmethod
    def _validate_inputs(
        *,
        node_id: NodeId,
        instance_id: NodeInstanceId,
        stabilization: CriticalPathReaderStabilization,
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
            CriticalPathReaderStabilization,
        ):
            raise TypeError(
                "stabilization must be a "
                "CriticalPathReaderStabilization"
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
