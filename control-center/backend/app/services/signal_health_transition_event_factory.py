"""Map SignalHealth transitions to immutable NOC events.

ENG-013C — Signal Health -> NOC integration

This factory converts one already-detected SignalHealthTransition
into one EventRecord.

It does not:

- evaluate Signal Health;
- evaluate Media Health;
- evaluate Source Transport Health;
- detect transitions;
- capture MediaMTX state;
- persist events;
- create or manage alarms.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.domain.streaming.health import HealthStatus
from app.noc.domain.node_event import (
    EventRecord,
    EventSeverity,
)
from app.noc.domain.node_instance import NodeInstanceId
from app.noc.services.health_transition_detector import (
    HealthTransitionKind,
)
from app.services.signal_health_transition_detector import (
    SignalHealthTransition,
)


class SignalHealthTransitionEventFactory:
    """Create EventRecord objects from SignalHealth transitions."""

    def create(
        self,
        *,
        transition: SignalHealthTransition,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> EventRecord:
        """Create one immutable event for a SignalHealth transition."""

        if not isinstance(
            transition,
            SignalHealthTransition,
        ):
            raise TypeError(
                "transition must be a SignalHealthTransition"
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

        current = transition.current
        previous = transition.previous

        event_type, severity = self._event_classification(
            transition
        )

        attributes: dict[str, object] = {
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

        return EventRecord(
            event_id=str(uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=timestamp,
            source=source,
            title=(
                f"Signal Health {transition.kind.value}: "
                f"{current.profile_id}"
            ),
            description=(
                f"Signal Health profile {current.profile_id} "
                f"changed from {previous.status.value} "
                f"to {current.status.value}."
            ),
            correlation_id=None,
            attributes=attributes,
        )

    @staticmethod
    def _event_classification(
        transition: SignalHealthTransition,
    ) -> tuple[str, EventSeverity]:
        kind = transition.kind
        current_status = transition.current.status

        if kind is HealthTransitionKind.DEGRADED:
            severity = (
                EventSeverity.CRITICAL
                if current_status is HealthStatus.CRITICAL
                else EventSeverity.WARNING
            )

            return (
                "SIGNAL_HEALTH_DEGRADED",
                severity,
            )

        if kind is HealthTransitionKind.IMPROVED:
            return (
                "SIGNAL_HEALTH_IMPROVED",
                EventSeverity.NOTICE,
            )

        if kind is HealthTransitionKind.RECOVERED:
            return (
                "SIGNAL_HEALTH_RECOVERED",
                EventSeverity.INFO,
            )

        if kind is HealthTransitionKind.UNKNOWN:
            return (
                "SIGNAL_HEALTH_UNKNOWN",
                EventSeverity.NOTICE,
            )

        raise ValueError(
            f"unsupported Signal Health transition kind: {kind}"
        )
