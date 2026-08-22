"""Alarm creation for confirmed missing multimedia sessions.

ENG-013B — Node SDK

ExpectedSessionAlarmFactory converts a confirmed missing-session
condition into an immutable active AlarmRecord.

It does not persist, acknowledge, resolve or close alarms.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.expected_session_stabilizer import (
    ExpectedSessionStabilization,
)


EXPECTED_SESSION_MISSING = "EXPECTED_SESSION_MISSING"


class ExpectedSessionAlarmFactory:
    """Create alarms for confirmed missing expected sessions."""

    def create(
        self,
        *,
        stabilization: ExpectedSessionStabilization,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> AlarmRecord:
        """Create an ACTIVE expected-session-missing alarm."""

        if not isinstance(
            stabilization,
            ExpectedSessionStabilization,
        ):
            raise TypeError(
                "stabilization must be an "
                "ExpectedSessionStabilization"
            )

        if not stabilization.confirmed_missing:
            raise ValueError(
                "stabilization must represent a "
                "confirmed missing session"
            )

        if not isinstance(source, NodeInstanceId):
            raise TypeError(
                "source must be a NodeInstanceId"
            )

        if not isinstance(timestamp, datetime):
            raise TypeError(
                "timestamp must be a datetime"
            )

        if (
            timestamp.tzinfo is None
            or timestamp.utcoffset() is None
        ):
            raise ValueError(
                "timestamp must be timezone-aware"
            )

        policy = stabilization.evaluation.policy

        path = (
            policy.path
            if policy.path is not None
            else "-"
        )

        title = (
            f"Expected {policy.protocol.value} "
            f"{policy.role.value.lower()} session "
            f"missing on {path}"
        )

        description = (
            f"Expected multimedia session policy "
            f"{policy.policy_id!r} is not currently "
            f"satisfied. "
            f"Protocol={policy.protocol.value}, "
            f"role={policy.role.value}, "
            f"path={path}."
        )

        return AlarmRecord(
            alarm_id=f"alm-{uuid4().hex}",
            alarm_type=EXPECTED_SESSION_MISSING,
            severity=AlarmSeverity.MAJOR,
            state=AlarmState.ACTIVE,
            timestamp=timestamp,
            source=source,
            title=title,
            description=description,
            attributes={
                "policy_id": policy.policy_id,
                "protocol": policy.protocol.value,
                "role": policy.role.value,
                "path": (
                    policy.path
                    if policy.path is not None
                    else ""
                ),
                "missing_since": (
                    stabilization.missing_since.isoformat()
                    if stabilization.missing_since is not None
                    else ""
                ),
            },
        )
