"""Alarm creation for critical multimedia paths without readers.

ENG-013B — Node SDK

CriticalPathNoReadersAlarmFactory converts a confirmed critical-path
NO_READERS condition into an immutable active AlarmRecord.

It does not persist, acknowledge, resolve or close alarms.
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
from app.noc.services.critical_path_reader_stabilizer import (
    CriticalPathReaderStabilization,
)


CRITICAL_PATH_NO_READERS = "CRITICAL_PATH_NO_READERS"


class CriticalPathNoReadersAlarmFactory:
    """Create alarms for confirmed readerless critical paths."""

    def create(
        self,
        *,
        stabilization: CriticalPathReaderStabilization,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> AlarmRecord:
        """Create an ACTIVE CRITICAL_PATH_NO_READERS alarm."""

        if not isinstance(
            stabilization,
            CriticalPathReaderStabilization,
        ):
            raise TypeError(
                "stabilization must be a "
                "CriticalPathReaderStabilization"
            )

        if not stabilization.confirmed_no_readers:
            raise ValueError(
                "stabilization must represent confirmed "
                "no-readers state"
            )

        if not isinstance(source, NodeInstanceId):
            raise TypeError(
                "source must be a NodeInstanceId"
            )

        self._validate_timestamp(timestamp)

        evaluation = stabilization.evaluation
        path = evaluation.policy.path

        return AlarmRecord(
            alarm_id=f"alm-{uuid4().hex}",
            alarm_type=CRITICAL_PATH_NO_READERS,
            severity=AlarmSeverity.MAJOR,
            state=AlarmState.ACTIVE,
            timestamp=timestamp,
            source=source,
            title=(
                f"Critical path {path} has no readers"
            ),
            description=(
                f"Critical multimedia path {path!r} "
                f"has an active publisher but no active readers."
            ),
            attributes={
                "path": path,
                "publisher_count": str(
                    len(evaluation.publishers)
                ),
                "reader_count": str(
                    len(evaluation.readers)
                ),
                "no_readers_since": (
                    stabilization.no_readers_since.isoformat()
                    if stabilization.no_readers_since is not None
                    else ""
                ),
            },
        )

    @staticmethod
    def _validate_timestamp(
        timestamp: datetime,
    ) -> None:
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
