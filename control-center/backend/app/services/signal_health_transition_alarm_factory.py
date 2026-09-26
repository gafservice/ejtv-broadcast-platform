"""Signal Health alarm materialization.

ENG-013C — Signal Health -> Alarms / Recovery

SignalHealthTransitionAlarmFactory converts an already-authorized
SignalHealthAlarmDecision into an immutable AlarmRecord only when policy
explicitly authorizes a RAISE action.

It does not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect transitions;
- decide alarm policy;
- persist alarms;
- manage alarm lifecycle.
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
from app.services.signal_health_alarm_policy import (
    SignalHealthAlarmAction,
    SignalHealthAlarmDecision,
)


class SignalHealthTransitionAlarmFactory:
    """Create AlarmRecord objects from authorized Signal Health decisions."""

    def create(
        self,
        *,
        decision: SignalHealthAlarmDecision,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> AlarmRecord | None:
        """Create one active alarm only when policy authorizes RAISE."""

        if not isinstance(
            decision,
            SignalHealthAlarmDecision,
        ):
            raise TypeError(
                "decision must be a SignalHealthAlarmDecision"
            )

        if not isinstance(source, NodeInstanceId):
            raise TypeError(
                "source must be a NodeInstanceId"
            )

        self._validate_timestamp(timestamp)

        if decision.action is not SignalHealthAlarmAction.RAISE:
            return None

        transition = decision.transition

        if transition is None:
            raise ValueError(
                "RAISE decision requires a transition"
            )

        previous = transition.previous
        current = transition.current

        attributes: dict[str, str] = {
            "profile_id": current.profile_id,
            "service_id": current.service_id,
            "previous": previous.status.value,
            "current": current.status.value,
            "transition": transition.kind.value,
            "media_previous": previous.media_status.value,
            "media_current": current.media_status.value,
            "transport_previous": (
                previous.transport_status.value
            ),
            "transport_current": (
                current.transport_status.value
            ),
        }

        if current.path_name is not None:
            attributes["path_name"] = current.path_name

        return AlarmRecord(
            alarm_id=self._alarm_id(),
            alarm_type="SIGNAL_HEALTH",
            severity=self._severity(
                current.status
            ),
            state=AlarmState.ACTIVE,
            timestamp=timestamp,
            source=source,
            title=(
                "Signal Health requires operator attention: "
                f"{current.profile_id} / {current.status.value}"
            ),
            description=(
                f"Signal Health profile {current.profile_id} "
                "requires operator attention after transition "
                f"from {previous.status.value} "
                f"to {current.status.value} "
                f"({transition.kind.value})."
            ),
            attributes=attributes,
        )

    @staticmethod
    def _alarm_id() -> str:
        """Create a unique operational alarm identifier."""

        return f"alm-{uuid4().hex}"

    @staticmethod
    def _severity(
        status: HealthStatus,
    ) -> AlarmSeverity:
        """Map authorized Signal Health state to alarm severity."""

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
