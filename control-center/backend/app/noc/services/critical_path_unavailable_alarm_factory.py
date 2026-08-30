"""Alarm factory for unavailable critical multimedia paths.

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
from app.noc.services.critical_path_availability_evaluator import (
    CriticalPathAvailabilityState,
)
from app.noc.services.critical_path_availability_stabilizer import (
    CriticalPathAvailabilityStabilization,
)


CRITICAL_PATH_UNAVAILABLE = "CRITICAL_PATH_UNAVAILABLE"


class CriticalPathUnavailableAlarmFactory:
    """Create alarms for confirmed unavailable critical paths."""

    def create(
        self,
        *,
        stabilization: CriticalPathAvailabilityStabilization,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> AlarmRecord:
        """Create an ACTIVE CRITICAL_PATH_UNAVAILABLE alarm."""

        if not isinstance(
            stabilization,
            CriticalPathAvailabilityStabilization,
        ):
            raise TypeError(
                "stabilization must be a "
                "CriticalPathAvailabilityStabilization"
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
            is not CriticalPathAvailabilityState.UNAVAILABLE
            or not stabilization.confirmed_unavailable
        ):
            raise ValueError(
                "stabilization must represent confirmed "
                "unavailable state"
            )

        evaluation = stabilization.evaluation
        policy = evaluation.policy
        media_path = evaluation.media_path

        attributes = {
            "path": policy.path,
            "path_present": (
                "true" if media_path is not None else "false"
            ),
        }

        if media_path is not None:
            attributes.update(
                {
                    "status": str(media_path.status),
                    "source_present": (
                        "true"
                        if media_path.has_source
                        else "false"
                    ),
                    "source_type": (
                        media_path.source.source_type
                        if media_path.source is not None
                        else "none"
                    ),
                    "ready": str(media_path.ready).lower(),
                    "available": str(
                        media_path.available
                    ).lower(),
                    "online": str(media_path.online).lower(),
                }
            )
        else:
            attributes.update(
                {
                    "status": "MISSING",
                    "source_present": "false",
                    "source_type": "none",
                    "ready": "false",
                    "available": "false",
                    "online": "false",
                }
            )

        return AlarmRecord(
            alarm_id=f"alm-{uuid4()}",
            alarm_type=CRITICAL_PATH_UNAVAILABLE,
            severity=AlarmSeverity.CRITICAL,
            state=AlarmState.ACTIVE,
            title=(
                f"Critical path unavailable: {policy.path}"
            ),
            description=(
                f"Critical multimedia path {policy.path} "
                "is unavailable."
            ),
            source=source,
            timestamp=timestamp,
            attributes=attributes,
        )
