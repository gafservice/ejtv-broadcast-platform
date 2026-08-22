"""Alarm creation for multimedia reconnect flapping.

ENG-013B — Node SDK

ReconnectFlappingAlarmFactory converts a FLAPPING evaluation into an
immutable active AlarmRecord.

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
from app.noc.services.reconnect_flapping_evaluator import (
    ReconnectFlappingEvaluation,
    ReconnectFlappingState,
)


RECONNECT_FLAPPING = "RECONNECT_FLAPPING"


class ReconnectFlappingAlarmFactory:
    """Create alarms for logical sessions experiencing reconnect flapping."""

    def create(
        self,
        *,
        evaluation: ReconnectFlappingEvaluation,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> AlarmRecord:
        """Create an ACTIVE RECONNECT_FLAPPING alarm."""

        if not isinstance(
            evaluation,
            ReconnectFlappingEvaluation,
        ):
            raise TypeError(
                "evaluation must be a "
                "ReconnectFlappingEvaluation"
            )

        if (
            evaluation.state
            is not ReconnectFlappingState.FLAPPING
        ):
            raise ValueError(
                "evaluation must represent FLAPPING"
            )

        if not isinstance(source, NodeInstanceId):
            raise TypeError(
                "source must be a NodeInstanceId"
            )

        self._validate_timestamp(timestamp)

        identity = evaluation.identity

        path = (
            identity.path
            if identity.path is not None
            else "-"
        )

        title = (
            f"{identity.protocol.value} "
            f"{identity.role.value.lower()} reconnect "
            f"flapping on {path}"
        )

        description = (
            f"Logical multimedia session "
            f"{identity.protocol.value}/"
            f"{identity.role.value}/"
            f"{path}/"
            f"{identity.remote_ip} "
            f"has experienced "
            f"{evaluation.reconnect_count} reconnects "
            f"inside the active flapping window."
        )

        return AlarmRecord(
            alarm_id=f"alm-{uuid4().hex}",
            alarm_type=RECONNECT_FLAPPING,
            severity=AlarmSeverity.MAJOR,
            state=AlarmState.ACTIVE,
            timestamp=timestamp,
            source=source,
            title=title,
            description=description,
            attributes={
                "protocol": identity.protocol.value,
                "role": identity.role.value,
                "path": (
                    identity.path
                    if identity.path is not None
                    else ""
                ),
                "remote_ip": identity.remote_ip,
                "reconnect_count": str(
                    evaluation.reconnect_count
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
