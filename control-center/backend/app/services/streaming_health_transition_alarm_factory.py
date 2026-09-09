"""Stream Health alarm materialization.

ENG-013B — Stream Health Contract Block 5

StreamingHealthTransitionAlarmFactory converts an alarm-policy decision
into an immutable AlarmRecord only when the policy explicitly authorizes
a RAISE action.

It does not evaluate Stream Health, detect transitions, decide alarm
policy, persist alarms, or manage alarm lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.domain.streaming.health import HealthStatus
from app.noc.domain.node_alarm import (
    AlarmRecord,
    AlarmSeverity,
    AlarmState,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.services.streaming_health_alarm_policy import (
    StreamingHealthAlarmAction,
    StreamingHealthAlarmDecision,
)


class StreamingHealthTransitionAlarmFactory:
    """Create AlarmRecord objects from authorized Stream Health decisions."""

    def create(
        self,
        *,
        decision: StreamingHealthAlarmDecision,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> AlarmRecord | None:
        """Create one active alarm when policy explicitly authorizes RAISE."""

        if not isinstance(
            decision,
            StreamingHealthAlarmDecision,
        ):
            raise TypeError(
                "decision must be a StreamingHealthAlarmDecision"
            )

        if not isinstance(source, NodeInstanceId):
            raise TypeError(
                "source must be a NodeInstanceId"
            )

        self._validate_timestamp(timestamp)

        if decision.action is not StreamingHealthAlarmAction.RAISE:
            return None

        transition = decision.transition

        if transition is None:
            raise ValueError(
                "RAISE decision requires a transition"
            )

        previous = transition.previous.status.value
        current = transition.current.status.value
        kind = transition.kind.value

        return AlarmRecord(
            alarm_id=self._alarm_id(),
            alarm_type="STREAM_HEALTH",
            severity=self._severity(
                transition.current.status
            ),
            state=AlarmState.ACTIVE,
            timestamp=timestamp,
            source=source,
            title=(
                "Stream Health requires operator attention: "
                f"{current}"
            ),
            description=(
                "Stream Health alarm policy authorized an alarm "
                f"for transition from {previous} to {current} "
                f"({kind})."
            ),
            attributes={
                "previous": previous,
                "current": current,
                "transition": kind,
            },
        )

    @staticmethod
    def _alarm_id() -> str:
        """Create a unique operational alarm identifier."""

        return f"alm-{uuid4().hex}"

    @staticmethod
    def _severity(
        status: HealthStatus,
    ) -> AlarmSeverity:
        """Map policy-authorized Stream Health state to alarm severity."""

        if status is HealthStatus.CRITICAL:
            return AlarmSeverity.CRITICAL

        if status is HealthStatus.DEGRADED:
            return AlarmSeverity.MAJOR

        return AlarmSeverity.WARNING

    @staticmethod
    def _validate_timestamp(
        timestamp: datetime,
    ) -> None:
        """Require an aware UTC timestamp."""

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
