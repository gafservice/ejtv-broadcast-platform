"""Map MediaHealth transitions to durable NOC events.

ENG-013C — Media Health -> NOC integration

This factory maps one already-detected MediaHealthTransition to a
NodeEvent. It preserves Media profile identity and aggregate transition
evidence without inventing a singular descriptive cause.

It does not:

- evaluate Media Health;
- stabilize Media Health;
- detect transitions;
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
from app.services.media_health_transition_detector import (
    MediaHealthTransition,
)


class MediaHealthTransitionEventFactory:
    """Create one NOC event from one MediaHealth transition."""

    def create(
        self,
        *,
        transition: MediaHealthTransition,
        source: NodeInstanceId,
        timestamp: datetime,
    ) -> EventRecord:
        if not isinstance(
            transition,
            MediaHealthTransition,
        ):
            raise TypeError(
                "transition must be a MediaHealthTransition"
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

        event_type = self._event_type(
            transition.kind
        )
        severity = self._severity(
            transition
        )

        profile_id = transition.current.profile_id
        previous = transition.previous.status.value
        current = transition.current.status.value

        attributes = {
            "profile_id": profile_id,
            "service_id": (
                transition.current.service_id
            ),
            "previous": previous,
            "current": current,
            "transition": transition.kind.value,
        }

        if transition.current.path_name is not None:
            attributes["path_name"] = (
                transition.current.path_name
            )

        return EventRecord(
            event_id=str(uuid4()),
            event_type=event_type,
            source=source,
            timestamp=timestamp,
            severity=severity,
            title=(
                f"Media Health {profile_id}: "
                f"{current}"
            ),
            description=(
                f"Media Health profile {profile_id} "
                f"changed from {previous} to {current}."
            ),
            attributes=attributes,
        )

    @staticmethod
    def _event_type(
        kind: HealthTransitionKind,
    ) -> str:
        mapping = {
            HealthTransitionKind.DEGRADED:
                "MEDIA_HEALTH_DEGRADED",
            HealthTransitionKind.IMPROVED:
                "MEDIA_HEALTH_IMPROVED",
            HealthTransitionKind.RECOVERED:
                "MEDIA_HEALTH_RECOVERED",
            HealthTransitionKind.UNKNOWN:
                "MEDIA_HEALTH_UNKNOWN",
        }

        try:
            return mapping[kind]
        except KeyError as exc:
            raise ValueError(
                f"unsupported Media Health transition: "
                f"{kind!r}"
            ) from exc

    @staticmethod
    def _severity(
        transition: MediaHealthTransition,
    ) -> EventSeverity:
        if (
            transition.kind
            is HealthTransitionKind.DEGRADED
        ):
            if (
                transition.current.status
                is HealthStatus.CRITICAL
            ):
                return EventSeverity.CRITICAL

            return EventSeverity.WARNING

        if (
            transition.kind
            is HealthTransitionKind.IMPROVED
        ):
            return EventSeverity.NOTICE

        if (
            transition.kind
            is HealthTransitionKind.RECOVERED
        ):
            return EventSeverity.INFO

        if (
            transition.kind
            is HealthTransitionKind.UNKNOWN
        ):
            return EventSeverity.NOTICE

        raise ValueError(
            "unsupported Media Health transition kind"
        )
