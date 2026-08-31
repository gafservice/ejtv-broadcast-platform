"""Alarm factory for stalled traffic on critical multimedia paths.

ENG-013B — Node SDK
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.critical_path_traffic_evaluator import (
    CriticalPathTrafficState,
)
from app.noc.services.critical_path_traffic_stabilizer import (
    CriticalPathTrafficStabilization,
)


CRITICAL_PATH_TRAFFIC_STALLED = "CRITICAL_PATH_TRAFFIC_STALLED"


class CriticalPathTrafficStalledAlarmFactory:
    """Create alarms for confirmed stalled critical-path traffic."""

    def create(
        self,
        *,
        stabilization: CriticalPathTrafficStabilization,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> AlarmRecord:
        """Create an ACTIVE CRITICAL_PATH_TRAFFIC_STALLED alarm."""

        if not isinstance(
            stabilization,
            CriticalPathTrafficStabilization,
        ):
            raise TypeError(
                "stabilization must be a "
                "CriticalPathTrafficStabilization"
            )

        if not isinstance(source, NodeInstanceId):
            raise TypeError(
                "source must be a NodeInstanceId"
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

        if (
            stabilization.evaluation.state
            is not CriticalPathTrafficState.STALLED
            or not stabilization.confirmed_stalled
        ):
            raise ValueError(
                "stabilization must represent confirmed "
                "stalled traffic"
            )

        evaluation = stabilization.evaluation
        policy = evaluation.policy
        media_path = evaluation.media_path
        measurement = evaluation.measurement

        if media_path is None:
            raise ValueError(
                "confirmed stalled traffic requires a media_path"
            )

        if measurement is None:
            raise ValueError(
                "confirmed stalled traffic requires a measurement"
            )

        attributes = {
            "path": policy.path,
            "status": str(media_path.status),
            "source_present": (
                "true" if media_path.has_source else "false"
            ),
            "source_type": (
                media_path.source.source_type
                if media_path.source is not None
                else "none"
            ),
            "ready": str(media_path.ready).lower(),
            "available": str(media_path.available).lower(),
            "online": str(media_path.online).lower(),
            "reader_count": str(measurement.reader_count),
            "inbound_bitrate_bps": str(
                measurement.inbound_bitrate_bps
            ),
            "outbound_bitrate_bps": str(
                measurement.outbound_bitrate_bps
            ),
            "measurement_quality": str(
                measurement.quality
            ),
        }

        return AlarmRecord(
            alarm_id=f"alm-{uuid4()}",
            alarm_type=CRITICAL_PATH_TRAFFIC_STALLED,
            severity=AlarmSeverity.CRITICAL,
            state=AlarmState.ACTIVE,
            title=(
                f"Critical path traffic stalled: {policy.path}"
            ),
            description=(
                f"Critical multimedia path {policy.path} "
                "has stopped receiving inbound traffic."
            ),
            source=source,
            timestamp=timestamp,
            attributes=attributes,
        )
